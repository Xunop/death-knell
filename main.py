#!/bin/python3

import requests
import ddddocr
import argparse
import re
import base64
import difflib
import os
from time import sleep
from PIL import Image
import io
from contextlib import redirect_stdout
from io import StringIO

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

from course import Course


def parse_args():
    # Parse args from command line

    parser = argparse.ArgumentParser(description='A simple crawler for NJUPT')
    parser.add_argument('-u', '--user', help='User ID', required=True)
    parser.add_argument('-p', '--password',
                        help='User Password', required=True)
    parser.add_argument('-n', '--name', help='User Name', required=True)
    parser.add_argument(
        '-y', '--year', help='Year(eg: 2023-2024)', required=True)
    parser.add_argument('-s', '--semester',
                        help='Semester(eg: 1)', default='')
    # webhook
    parser.add_argument('-w', '--webhook',
                        help='Webhook URL', default='')
    return parser.parse_args()


def find_available_filename(base_filename):
    # Find an available filename by adding a number suffix

    suffix = 2
    while True:
        new_filename = f"{base_filename}-{suffix}.txt"
        if not os.path.isfile(new_filename):
            return new_filename
        suffix += 1


def compare_and_output_diff(old_filename, new_filename):
    print('Comparing files...')
    if not os.path.isfile(new_filename):
        print(f'No new file {new_filename} found')
        return
    # Compare files and print differences
    with open(old_filename, 'r', encoding='utf-8') as main_file, \
            open(new_filename, 'r', encoding='utf-8') as new_file:
        main_content = main_file.readlines()
        new_content = new_file.readlines()

        d = difflib.Differ()
        diff = list(d.compare(main_content, new_content))

        print(
            f'Differences between {old_filename} and {new_filename}:')

        with open('score.diff', 'w', encoding='utf-8') as diff_file:
            for line in diff:
                if line.startswith('- ') or line.startswith('+ '):
                    diff_file.write(line.strip() + '\n')
                    print(line.strip())
        with open(old_filename, 'w', encoding='utf-8') as main_file:
            main_file.writelines(new_content)


def write_to_file(courses, filename, new_filename):
    # Write results to a file
    # Check if course-data.txt file exists
    # Write results to a new file

    if os.path.isfile(filename):
        filename = new_filename
    with open(filename, 'w', encoding='utf-8') as file:
        for course in courses:
            file.write(f"{course['Name']}-学年: {course['Year']}\n")
            file.write(f"{course['Name']}-学期: {course['Semester']}\n")
            file.write(f"{course['Name']}-课程号: {course['ID']}\n")
            file.write(f"课程名称: {course['Name']}\n")
            file.write(f"{course['Name']}-课程性质: {course['Type']}\n")
            file.write(f"{course['Name']}-学分: {course['Credit']}\n")
            file.write(f"{course['Name']}-绩点: {course['GPA']}\n")
            file.write(f"{course['Name']}-平时分: {course['Normal']}\n")
            file.write(f"{course['Name']}-卷面分: {course['Real']}\n")
            file.write(f"{course['Name']}-总分: {course['Total']}\n\n")


def write_to_course_file(courses):
    for course in courses:
        if not os.path.isfile(course['Name'] + '.txt'):
            with open(course['Name'] + '.txt', 'w', encoding='utf-8') as file:
                file.write(f"学年: {course['Year']}\n")
                file.write(f"学期: {course['Semester']}\n")
                file.write(f"课程号: {course['ID']}\n")
                file.write(f"课程名称: {course['Name']}\n")
                file.write(f"课程性质: {course['Type']}\n")
                file.write(f"学分: {course['Credit']}\n")
                file.write(f"绩点: {course['GPA']}\n")
                file.write(f"平时分: {course['Normal']}\n")
                file.write(f"卷面分: {course['Real']}\n")
                file.write(f"总分: {course['Total']}\n\n")
            continue
        if not os.path.isfile('score.diff'):
            continue
        # FIXME: Can't update old course info
        # Update old course info
        with open('score.diff', 'r', encoding='utf-8') as diff_file:
            if course['Name'] in diff_file.read():
                with open(course['Name'] + '.txt', 'w', encoding='utf-8') as file:
                    file.write(f"学年: {course['Year']}\n")
                    file.write(f"学期: {course['Semester']}\n")
                    file.write(f"课程号: {course['ID']}\n")
                    file.write(f"课程名称: {course['Name']}\n")
                    file.write(f"课程性质: {course['Type']}\n")
                    file.write(f"学分: {course['Credit']}\n")
                    file.write(f"绩点: {course['GPA']}\n")
                    file.write(f"平时分: {course['Normal']}\n")
                    file.write(f"卷面分: {course['Real']}\n")
                    file.write(f"总分: {course['Total']}\n\n")


def parse_score(content):
    try:
        # base64 decode
        decoded_str = base64.b64decode(
            content).decode('utf-8', errors='ignore')

        pattern = re.compile(r'l<([^;]+);+>>;')
        matches = pattern.findall(decoded_str)

        # cut the first 19 matches
        matches = matches[19:]
        courses = []
        course_data = {}
        for idx, match in enumerate(matches):
            if match == '&nbsp\\':
                match = 'NULL'
            if match == 'o<f>':
                break
            match = match.strip()

           # Create course fields based on the index within a cycle of 22
            cycle_index = idx % 22
            if cycle_index == 0:
                course_data['year'] = match
            elif cycle_index == 1:
                course_data['semester'] = match
            elif cycle_index == 2:
                course_data['course_id'] = match
            elif cycle_index == 3:
                course_data['name'] = match
            elif cycle_index == 4:
                course_data['type'] = match
            elif cycle_index == 6:
                course_data['credit'] = match
            elif cycle_index == 8:
                course_data['gpa'] = match
            elif cycle_index == 9:
                course_data['normal_score'] = match
            elif cycle_index == 11:
                course_data['real_score'] = match
            elif cycle_index == 13:
                course_data['total_score'] = match
                # Create a Course object and add to the list when all required data is gathered
                courses.append(Course(**course_data))

        return courses

    except Exception as e:
        print(f"An error occurred: {e}")
        return []


def get_course_info(file_name, course_name):
    try:
        with open(file_name, 'r') as file:
            lines = file.readlines()

            for line in lines:
                if f"{course_name}-学分" in line:
                    course_credit = line.split(':')[1].strip()
                if f"{course_name}-绩点" in line:
                    course_gpa = line.split(':')[1].strip()
                if f"{course_name}-平时分" in line:
                    course_normal = line.split(':')[1].strip()
                if f"{course_name}-卷面分" in line:
                    course_real = line.split(':')[1].strip()
                if f"{course_name}-学期" in line:
                    course_semester = line.split(':')[1].strip()

                if f"{course_name}-学年" in line:
                    course_year = line.split(':')[1].strip()
                if f"{course_name}-总分" in line:
                    course_total = line.split(':')[1].strip()
                    dead = False
                    if course_total not in ['优秀', '良好', '中等', '及格', '不及格']:
                        course_total = int(course_total)
                        if course_total < 60:
                            dead = True
                    else:
                        if course_total == '不及格':
                            dead = True
            return {
                "courseCredit": course_credit,
                "courseGPA": course_gpa,
                "courseNormal": course_normal,
                "courseReal": course_real,
                "courseTotal": course_total,
                "isDead": dead,
                "courseSemester": course_semester,
                "courseYear": course_year
            }
    except Exception as e:
        print(f"An error occurred: {e}")


def push_to_feishu(filename):
    if not os.path.isfile(filename):
        return
    try:
        with open(filename, 'r') as file:
            lines = file.readlines()

            for line in lines:
                if "课程名称" in line:
                    course_name = line.split(':')[1].strip()
                    if not os.path.isfile(course_name + '.txt'):
                        course_info = get_course_info(filename, course_name)
                        headers = {
                            'Content-Type': 'application/json'
                        }
                        json = {
                            "isDead": course_info["isDead"],
                            "courseName": course_name,
                            "year": course_info["courseYear"],
                            "semester": course_info["courseSemester"],
                            "courseCredit": course_info["courseCredit"],
                            "courseGPA": course_info["courseGPA"],
                            "courseNormal": course_info["courseNormal"],
                            "courseReal": course_info["courseReal"],
                            "courseTotal": course_info["courseTotal"],
                        }
                        requests.post(
                            webhook_url, headers=headers, json=json)
    except Exception as e:
        print(f"An error occurred: {e}")


root_url = 'http://jwxt.njupt.edu.cn/'

login_url = 'http://jwxt.njupt.edu.cn/default2.aspx'

cookie_url = 'http://jwxt.njupt.edu.cn/beLd2jeSRcTo/5TAbvFJ54R4g.e793599.js'

captcha_url = 'http://jwxt.njupt.edu.cn/CheckCode.aspx'

content_url = 'http://jwxt.njupt.edu.cn/content.aspx'

query_score_url = 'http://jwxt.njupt.edu.cn/xscj_gc.aspx'


# cookie = requests.get(root_url)

args = parse_args()
user_name = args.name
user_id = args.user
user_pwd = args.password
year = args.year
semester = args.semester
webhook_url = args.webhook

# request with cookie
# response = requests.get(captcha_url, cookies=cookie.cookies)

# ignore print info
null_file = StringIO()
with redirect_stdout(null_file):
    ocr = ddddocr.DdddOcr()

# captcha = ocr.classification(response.content)

options = Options()
# Use headless mode
options.add_argument("--headless")
driver = webdriver.Firefox(options=options)

try:
    login_url = "http://jwxt.njupt.edu.cn"
    driver.get(login_url)

    sleep(5)

    captcha_element = driver.find_element(By.ID, "icode")
    location = captcha_element.location
    size = captcha_element.size
    screenshot = driver.get_screenshot_as_png()
    image_stream = io.BytesIO(screenshot)
    image = Image.open(image_stream)

    # Get the position of the captcha
    left = location['x']
    top = location['y']
    right = left + size['width']
    bottom = top + size['height']

    # Get the captcha image
    captcha_image = image.crop((left, top, right, bottom))
    captcha = ocr.classification(captcha_image)

    print(captcha)
    driver.find_element(By.NAME, "txtUserName").send_keys(
        user_id)
    driver.find_element(By.NAME, "TextBox2").send_keys(
        user_pwd)
    driver.find_element(By.NAME, "txtSecretCode").send_keys(
        captcha)

    driver.find_element(By.ID, "RadioButtonList1_2").send_keys(
        Keys.SPACE)
    driver.find_element(By.NAME, "Button1").click()

    WebDriverWait(driver, 10).until(EC.alert_is_present())
    alert = Alert(driver)
    # print("alert：", alert.text)
    # Accept the alert
    alert.accept()

    # Find the menu
    information_query_menu = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located(
            (By.XPATH, "//span[contains(text(), '信息查询')]"))
    )

    # Move to the menu
    ActionChains(driver).move_to_element(information_query_menu).perform()

    score_query_link = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located(
            (By.XPATH, "//a[contains(@onclick, '成绩查询')]"))
    )
    # Need to switch to the iframe
    driver.switch_to.frame("iframeautoheight")
    # driver.save_screenshot('before_click.png')
    score_query_link.click()
    ActionChains(driver).move_by_offset(100, 100).perform()
    # driver.save_screenshot('after_click.png')

    print("Querying score...")

    print(driver.current_url)
    # print(driver.page_source)

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.ID, "ddlXN"))
    )

    # Select year
    year_select = driver.find_element(By.NAME, "ddlXN")
    # print(year_select.text)
    year_select.send_keys(year)

    # Select semester
    semester_select = driver.find_element(By.NAME, "ddlXQ")
    semester_select.send_keys(semester)

    query_button = driver.find_element(By.ID, "Button1")
    query_button.click()

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.ID, "Datagrid1"))
    )

    score_table = driver.find_element(By.NAME, "__VIEWSTATE")
    score_value = score_table.get_attribute("value")
    # score_content = score_table.get_attribute("innerHTML")
    # print(score_value)

    courses = parse_score(score_value)
    for course in courses:
        print(course)


finally:
    driver.quit()
