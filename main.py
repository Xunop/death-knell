#!/bin/python3

import requests
import ddddocr
import argparse
import re
import base64
import difflib
import os
from urllib.parse import urlencode, urljoin
from contextlib import redirect_stdout
from io import StringIO


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

        current_course = -1
        # cut the first 19 matches
        matches = matches[19:]
        courses = []
        for idx, match in enumerate(matches):
            data = idx % 22
            if match == '&nbsp\\':
                match = 'NULL'
            if match == 'o<f>':
                break
            match = match.strip()
            if data == 0:
                course_year = match
                current_course += 1
                course_data = {'Year': course_year}
            elif data == 1:
                course_data['Semester'] = match
            elif data == 2:
                course_data['ID'] = match
            elif data == 3:
                course_data['Name'] = match
            elif data == 4:
                course_data['Type'] = match  # 课程性质
            elif data == 6:
                course_data['Credit'] = match  # 学分
            elif data == 8:
                course_data['GPA'] = match  # 绩点
            elif data == 9:
                course_data['Normal'] = match  # 平时分
            elif data == 11:
                course_data['Real'] = match  # 卷面分
            elif data == 13:
                course_data['Total'] = match  # 总分
                courses.append(course_data)
        return courses

    except Exception as e:
        print(f"An error occurred: {e}")


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

captcha_url = 'http://jwxt.njupt.edu.cn/CheckCode.aspx'

content_url = 'http://jwxt.njupt.edu.cn/content.aspx'

query_score_url = 'http://jwxt.njupt.edu.cn/xscj_gc.aspx'


# method
method = 1

cookie = requests.get(root_url)

args = parse_args()
user_name = args.name
user_id = args.user
user_pwd = args.password
year = args.year
semester = args.semester
webhook_url = args.webhook

# request with cookie
response = requests.get(captcha_url, cookies=cookie.cookies)

# ignore print info
null_file = StringIO()
with redirect_stdout(null_file):
    ocr = ddddocr.DdddOcr()

captcha = ocr.classification(response.content)

login_data = {
    '__VIEWSTATE': 'dDwtMTM0OTIyMDA2Nzs7PmQzMJt4J8nhapAW2eCOBH0ej4Fq',
    '__VIEWSTATEGENERATOR': '92719903',
    'txtUserName': user_id,
    'TextBox2': user_pwd,
    'txtSecretCode': captcha,
    'RadioButtonList1': '%D1%A7%C9%FA',
    'Button1': '',
    'lbLanguage': '',
    'hidPdrs': '',
    'hidsc': ''
}

login_response = requests.post(
    login_url, data=login_data, cookies=cookie.cookies)

if '<title>ERROR' in login_response.text:
    print('Login failed, try another method')
    method = 2
    login_data = {
        '__VIEWSTATE': 'dDwtMTM0OTIyMDA2Nzs7PhbP2uocdzpYvi/UGitcfOWK03ui',
        'txtUserName': user_id,
        'TextBox2': user_pwd,
        'txtSecretCode': captcha,
        'RadioButtonList1': '%D1%A7%C9%FA',
        'Button1': '',
        'lbLanguage': '',
        'hidPdrs': '',
        'hidsc': ''
    }

    login_response = requests.post(
        login_url, data=login_data, cookies=cookie.cookies)

params = {
    'xh': user_id,
    'xm': user_name,
    'gnmkdm': 'N121605'
}

query_score_url = urljoin(query_score_url, '?' +
                          urlencode(params, encoding='gb2312'))


headers = {
    'Referer': 'http://jwxt.njupt.edu.cn/xs_main.aspx?xh=' + user_id,
}

content_reponse = requests.get(
    query_score_url, headers=headers, cookies=cookie.cookies)

view_state = content_reponse.text.split(
    '<input type="hidden" name="__VIEWSTATE" value="')[1].split('" />')[0]

if method == 1:
    view_state_generator = content_reponse.text.split(
        '<input type="hidden" name="__VIEWSTATEGENERATOR" value="')[1].split('" />')[0]
    score_data = {
        '__VIEWSTATE': view_state,
        '__VIEWSTATEGENERATOR': view_state_generator,
        'ddlXN': year,
        'ddlXQ': semester,
        'Button1': '%B0%B4%D1%A7%C6%DA%B2%E9%D1%AF'
    }
else:
    score_data = {
        '__VIEWSTATE': view_state,
        'ddlXN': year,
        'ddlXQ': semester,
        'Button1': '%B0%B4%D1%A7%C6%DA%B2%E9%D1%AF'
    }

score_response = requests.post(
    query_score_url, data=score_data, cookies=cookie.cookies, headers=headers)

view_state = score_response.text.split(
    '<input type="hidden" name="__VIEWSTATE" value="')[1].split('" />')[0]
courses = parse_score(view_state)

filename = 'course-data.txt'
new_filename = 'course-data.tmp'
write_to_file(courses, filename, new_filename)
compare_and_output_diff(filename, new_filename)
push_to_feishu(filename)
write_to_course_file(courses)
