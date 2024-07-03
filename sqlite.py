import sqlite3
from course import Course


def create_database():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    # 创建 users 表
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        username TEXT,
        password TEXT
        year TEXT,
        semester TEXT
    )
    ''')
    # 更新 courses 表，加入 user_id
    c.execute('''
    CREATE TABLE IF NOT EXISTS courses (
        year TEXT,
        semester TEXT,
        course_id TEXT,
        name TEXT,
        type TEXT,
        credit TEXT,
        gpa TEXT,
        normal_score TEXT,
        real_score TEXT,
        total_score TEXT,
        user_id TEXT,
        FOREIGN KEY (user_id) REFERENCES users(user_id),
        PRIMARY KEY (course_id, year, semester, user_id)
    )
    ''')
    conn.commit()
    conn.close()


def insert_user(user_id, username, password, year, semester):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('''
    INSERT INTO users (user_id, username, password, year, semester)
    VALUES (?, ?, ?, ?, ?)
    ''', (user_id, username, password, year, semester))
    conn.commit()
    conn.close()


def get_user(user_id):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('''
    SELECT * FROM users WHERE user_id = ?
    ''', (user_id,))
    user = c.fetchone()
    conn.close()
    return user


def insert_course(course: Course, user_id):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    if course.real_score in [None, '', 'NULL']:
        course.real_score = 0
    if course.normal_score in [None, '', 'NULL']:
        course.normal_score = 0
    c.execute('''
    INSERT INTO courses (year, semester, course_id, name, type, credit, gpa, normal_score, real_score, total_score, user_id)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (course.year, course.semester, course.course_id, course.name, course.type, course.credit, course.gpa, course.normal_score, course.real_score, course.total_score, user_id))
    conn.commit()
    conn.close()


def get_courses(user_id):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('''
    SELECT * FROM courses WHERE user_id = ?
    ''', (user_id,))
    courses = c.fetchall()
    conn.close()
    return courses


def get_course(user_id, course_id, year, semester):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('''
    SELECT * FROM courses WHERE user_id = ? AND course_id = ? AND year = ? AND semester = ?
    ''', (user_id, course_id, year, semester))
    course = c.fetchone()
    conn.close()
    if course is None:
        return None
    return Course(*course)


# update_course update course
def update_course(course: Course, user_id):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    if course.real_score in [None, '', 'NULL']:
        course.real_score = 0
    if course.normal_score in [None, '', 'NULL']:
        course.normal_score = 0
    c.execute('''
    UPDATE courses SET real_score = ?, normal_score = ?, total_score = ? WHERE user_id = ? AND course_id = ? AND year = ? AND semester = ?
    ''', (course.real_score, course.normal_score, course.total_score, user_id, course.course_id, course.year, course.semester))
    conn.commit()
    conn.close()


def delete_course(user_id, course_id, year, semester):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('''
    DELETE FROM courses WHERE user_id = ? AND course_id = ? AND year = ? AND semester = ?
    ''', (user_id, course_id, year, semester))
    conn.commit()
    conn.close()
