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
from sqlite import insert_course, get_course, update_course, create_database


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

                course_data['user_id'] = user_id

                # Create a Course object and add to the list when all required data is gathered
                courses.append(Course(**course_data))

        return courses

    except Exception as e:
        print(f"An error occurred: {e}")
        return []


def push_to_feishu(courses: list[Course]):
    headers = {
        'Content-Type': 'application/json'
    }
    for course in courses:
        # If the course has not been updated, skip
        if not check_course_update(course, user_id):
            print('Course has not been updated, skipping...')
            continue
        requests.post(
            webhook_url, headers=headers, json=course.to_json())


def store_course(course: Course, user_id: str):
    if check_course_update(course, user_id):
        print('Course has been updated, updating...')
        update_course(course, user_id)
    if not check_course_exist(course, user_id):
        print('Course does not exist, inserting...')
        insert_course(course, user_id)


# Check if the course has been updated, If the total score has changed, update the course
def check_course_update(course: Course, user_id: str):
    # Get course info from database
    stored_course = get_course(user_id, course.course_id,
                               course.year, course.semester)
    if stored_course is None:
        return True

    # If the total score has changed, update the course
    if stored_course.total_score != course.total_score:
        return True
    else:
        # If the total score hasn't changed, no update is required
        return False


def check_course_exist(course: Course, user_id: str):
    stored_course = get_course(user_id, course.course_id,
                               course.year, course.semester)
    if stored_course is None:
        return False
    return True


def get_courses(user_id, user_pwd, year, semester, webhook_url):
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

        # print(captcha)
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

        # print(driver.current_url)
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
        # for course in courses:
        #     print(course)
        return courses

    finally:
        driver.quit()


### Main ###
args = parse_args()
user_name = args.name
user_id = args.user
user_pwd = args.password
year = args.year
semester = args.semester
webhook_url = args.webhook

# ignore print info
null_file = StringIO()
with redirect_stdout(null_file):
    ocr = ddddocr.DdddOcr()

options = Options()
# Use headless mode
options.add_argument("--headless")
driver = webdriver.Firefox(options=options)

create_database()

courses = get_courses(user_id, user_pwd, year, semester, webhook_url)
push_to_feishu(courses)
for course in courses:
    if course is not None:
        store_course(course, user_id)
