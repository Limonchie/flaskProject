import os
import shutil
import sqlite3
import datetime
import logging
import json
import requests
from math import ceil
from flask import Flask, render_template, request, redirect, url_for, current_app, session, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
from datetime import timedelta

import db

VERSION = "0"
BASE_URL = os.environ.get("BASE_URL", "")
DOCS_PATH = os.environ.get("DOCS_PATH", "docs")
CONTRACTS_PATH = os.environ.get("CONTRACTS_PATH", "contracts_templates")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "DEBUG")
DOCS_TTL = int(os.environ.get("DOCS_TTL", 3600))

app = Flask("chinaekb_form")
app.logger.setLevel(LOG_LEVEL)
app.secret_key = 'secret_123'

app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  # 20 MB
app.config['UPLOAD_FOLDER'] = 'uploads'
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Настройка Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Класс пользователя
class User(UserMixin):
    def __init__(self, id):
        self.id = id

# Загрузка пользователя
@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if not os.path.exists('chinaekb.db'):
    db.init_db()

if CONTRACTS_PATH != "contracts_templates":
    files = os.listdir("contracts_templates")
    for i in files:
        if not os.path.exists(CONTRACTS_PATH + "/" + i):
            shutil.copy2("contracts_templates/" + i, CONTRACTS_PATH + "/" + i)

def select_exam(examselection):
    exams = {
        "1": (2000, 1, "HSK"),
        "2": (2000, 2, "HSK"),
        "3": (3000, 3, "HSK"),
        "4": (3000, 4, "HSK"),
        "5": (4000, 5, "HSK"),
        "6": (4000, 6, "HSK"),
        "7": (2000, "базовый", "HSKK"),
        "8": (3000, "средний", "HSKK"),
        "9": (4000, "высокий", "HSKK"),
        "10": (2000, "A", "BCT"),
        "11": (3000, "B", "BCT"),
        "12": (1000, 1, "YCT"),
        "13": (1000, 2, "YCT"),
        "14": (1500, 3, "YCT"),
        "15": (1500, 4, "YCT")
    }
    return exams.get(examselection, (0, 0, "_____________"))

def clear_docs() -> None:
    if DOCS_TTL == 0:
        return
    files = os.listdir(DOCS_PATH)
    for i in files:
        file_path = os.path.join(DOCS_PATH, i)
        if datetime.datetime.now().timestamp() - os.path.getmtime(file_path) > DOCS_TTL:
            os.remove(file_path)

def save_student_data(table_name, data, file_paths):
    with sqlite3.connect('chinaekb.db') as conn:
        c = conn.cursor()
        columns = ', '.join(data.keys())
        placeholders = ', '.join('?' * len(data))
        query = f'INSERT INTO {table_name} ({columns}) VALUES ({placeholders})'
        c.execute(query, tuple(data.values()) + (','.join(file_paths),))
        conn.commit()

def process_form_data(form_data, file_paths):
    student_data = {
        'last_name': form_data['studentname-lastname'].strip().lower().capitalize(),
        'first_name': form_data['studentname-name'].strip().lower().capitalize(),
        'middle_name': form_data['studentname-surname'].strip().lower().capitalize(),
        'birth_date': str(form_data['studentbirth']),
        'address': form_data['studentaddress'],
        'gender': form_data['studentgender'],
        'snils': form_data['studentsnils'],
        'id_type': form_data['studentid-type'],
        'id_serial': form_data['studentid-serial'],
        'id_number': form_data['studentid-number'],
        'id_issued_by': form_data['studentid-by'],
        'id_issued_date': str(form_data['studentid-issued']),
        'bank_details': form_data['studentbank'],
        'phone': form_data['studentphone'],
        'email': form_data['studentemail'],
        'study_plan': form_data['study_plan'],
        'exam_selection': form_data['examselection'],
        'exam_date': form_data['examdate'],
        'submission_date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    save_student_data('students', student_data, file_paths)

@app.route(BASE_URL + "/status")
def status():
    resp = {"success": True, "version": VERSION, "status": "ok"}
    return json.dumps(resp), 200, {'Content-Type': 'application/json'}

@app.errorhandler(500)
def error(error):
    if request.method == "POST":
        return json.dumps({"success": False, "message": "Unknown server error"}), 500, {'Content-Type': 'application/json'}
    else:
        return render_template("500.html", base_url=BASE_URL), 500

@app.errorhandler(404)
def not_found(error):
    if request.method == "POST":
        return json.dumps({"success": False, "message": "Nothing was found"}), 404, {'Content-Type': 'application/json'}
    else:
        return render_template("404.html", base_url=BASE_URL), 404

@app.errorhandler(405)
def not_allowed(error):
    return json.dumps({"success": False, "message": "Method not allowed"}), 405, {'Content-Type': 'application/json'}

@app.route("/favicon.ico")
def favicon():
    return send_from_directory("static", "favicon.ico")

@app.route(BASE_URL + "/static/<path:path>")
def getstatic(path):
    return send_from_directory("static", path)

@app.route(BASE_URL + "/docs/<path:path>")
def getdocs(path):
    clear_docs()
    return send_from_directory(DOCS_PATH, path)

@app.route(BASE_URL + "/")
def index():
    return redirect(BASE_URL + "/forms")

@app.route(BASE_URL + "/forms")
def forms():
    return render_template("forms.html", base_url=BASE_URL)

@app.route(BASE_URL + "/education_adult", methods=["GET", "POST"])
def education_adult():
    if request.method == 'GET':
        return render_template("education_adult.html", base_url=BASE_URL, formtitle="Образование для взрослых")
    elif request.method == 'POST':
        form_data = request.form.to_dict()
        form_data['study_plan'] = "Практический курс китайского языка для взрослых"
        form_data['studentid-type'] = "passport"
        studentfiles = request.files.getlist('studentfiles')
        file_paths = [secure_filename(file.filename) for file in studentfiles if file and file.filename]
        for file in studentfiles:
            if file and file.filename:
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename)))
        process_form_data(form_data, file_paths)
        return redirect(url_for('success'))

@app.route(BASE_URL + "/exam_adult", methods=["GET", "POST"])
def exam_adult():
    if request.method == 'GET':
        return render_template("exam_adult.html", base_url=BASE_URL)
    elif request.method == 'POST':
        form_data = request.form.to_dict()
        form_data['study_plan'] = "Экзамен для взрослых"
        form_data['studentid-type'] = "passport"
        studentfiles = request.files.getlist('studentfiles')
        file_paths = [secure_filename(file.filename) for file in studentfiles if file and file.filename]
        for file in studentfiles:
            if file and file.filename:
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename)))
        process_form_data(form_data, file_paths)
        return redirect(url_for('success'))

@app.route(BASE_URL + "/education_children_under14", methods=["GET", "POST"])
def education_children_under14():
    if request.method == 'GET':
        return render_template("education_children_under14.html", base_url=BASE_URL, formtitle="Образование для несовершеннолетних (до 14 лет)")
    elif request.method == 'POST':
        form_data = request.form.to_dict()
        form_data['study_plan'] = "Практический базовый курс китайского языка для детей"
        form_data['studentid-type'] = "birth certificate"
        studentfiles = request.files.getlist('studentfiles')
        file_paths = [secure_filename(file.filename) for file in studentfiles if file and file.filename]
        for file in studentfiles:
            if file and file.filename:
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename)))
        process_form_data(form_data, file_paths)
        return redirect(url_for('success'))

@app.route(BASE_URL + "/education_children_over14", methods=["GET", "POST"])
def education_children_over14():
    if request.method == 'GET':
        return render_template("education_children_over14.html", base_url=BASE_URL, formtitle="Образование для несовершеннолетних (от 14 до 18 лет)")
    elif request.method == 'POST':
        form_data = request.form.to_dict()
        form_data['study_plan'] = "Практический базовый курс китайского языка для детей"
        form_data['studentid-type'] = "passport"
        studentfiles = request.files.getlist('studentfiles')
        file_paths = [secure_filename(file.filename) for file in studentfiles if file and file.filename]
        for file in studentfiles:
            if file and file.filename:
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename)))
        process_form_data(form_data, file_paths)
        return redirect(url_for('success'))

@app.route(BASE_URL + "/exam_children_under14", methods=["GET", "POST"])
def exam_children_under14():
    if request.method == 'GET':
        return render_template("exam_children_under14.html", base_url=BASE_URL, formtitle="Экзамен для несовершеннолетних (до 14 лет)")
    elif request.method == 'POST':
        form_data = request.form.to_dict()
        form_data['study_plan'] = "Экзамен для детей (до 14 лет)"
        form_data['studentid-type'] = "birth certificate"
        studentfiles = request.files.getlist('studentfiles')
        file_paths = [secure_filename(file.filename) for file in studentfiles if file and file.filename]
        for file in studentfiles:
            if file and file.filename:
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename)))
        process_form_data(form_data, file_paths)
        return redirect(url_for('success'))

@app.route(BASE_URL + "/exam_children_over14", methods=["GET", "POST"])
def exam_children_over14():
    if request.method == 'GET':
        return render_template("exam_children_over14.html", base_url=BASE_URL, formtitle="Экзамен для несовершеннолетних (от 14 до 18 лет)")
    elif request.method == 'POST':
        form_data = request.form.to_dict()
        form_data['study_plan'] = "Экзамен для детей (от 14 до 18 лет)"
        form_data['studentid-type'] = "passport"
        studentfiles = request.files.getlist('studentfiles')
        file_paths = [secure_filename(file.filename) for file in studentfiles if file and file.filename]
        for file in studentfiles:
            if file and file.filename:
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename)))
        process_form_data(form_data, file_paths)
        return redirect(url_for('success'))

app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=7)

@app.route(BASE_URL + "/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember') == 'on'

        if username == 'moder1' and password == 'password1':
            user = User('moderator1')
            login_user(user, remember=remember)
            return redirect(BASE_URL + "/moderation")
        elif username == 'moder2' and password == 'password2':
            user = User('moderator2')
            login_user(user, remember=remember)
            return redirect(BASE_URL + "/moderation")
        else:
            return render_template("login.html", base_url=BASE_URL, error="Неверный логин или пароль")

    return render_template("login.html", base_url=BASE_URL)

@app.route(BASE_URL + "/logout")
@login_required
def logout():
    logout_user()
    return redirect(BASE_URL + "/forms")

@app.route(BASE_URL + "/moderation", methods=["GET", "POST"])
@login_required
def moderation():
    if request.method == 'GET':
        table_name = request.args.get('table_name', default='students')
        status = request.args.get('status', default='all')
        limit = int(request.args.get('limit', default='20'))
        page = int(request.args.get('page', default='1'))

        with sqlite3.connect('chinaekb.db') as conn:
            c = conn.cursor()
            query = f'SELECT * FROM {table_name}'
            if status != 'all':
                query += f' WHERE status = ?'
                c.execute(query, (status,))
            else:
                c.execute(query)

            total_records = len(c.fetchall())
            total_pages = ceil(total_records / limit)

            offset = (page - 1) * limit
            query += f' LIMIT ? OFFSET ?'
            c.execute(query, (limit, offset) if status == 'all' else (status, limit, offset))

            if table_name == 'students':
                students = c.fetchall()
                minor_students_with_representatives = []
                adult_students = []
            elif table_name == 'adult_students':
                adult_students = c.fetchall()
                students = []
                minor_students_with_representatives = []

        success_message = session.pop('success_message', None)

        return render_template("moderation.html", base_url=BASE_URL, students=students, adult_students=adult_students, minor_students_with_representatives=minor_students_with_representatives, table_name=table_name, status=status, limit=limit, page=page, total_pages=total_pages, success_message=success_message)

def delete_files(file_paths):
    for file_path in file_paths:
        full_path = os.path.join(app.config['UPLOAD_FOLDER'], file_path)
        if os.path.exists(full_path):
            os.remove(full_path)
            logger.info(f"Файл {full_path} удален")
        else:
            logger.warning(f"Файл {full_path} не найден")

@app.route(BASE_URL + "/moderation/<table_name>/student/<int:student_id>", methods=["GET", "POST"])
@login_required
def student_details(table_name, student_id):
    if request.method == 'GET':
        with sqlite3.connect('chinaekb.db') as conn:
            c = conn.cursor()
            c.execute(f'SELECT * FROM {table_name} WHERE id = ?', (student_id,))
            student = c.fetchone()
            representative = None
            if student and table_name == 'students':
                c.execute('SELECT * FROM representatives WHERE student_id = ?', (student_id,))
                representative = c.fetchone()

        if student:
            return render_template("student_details.html", base_url=BASE_URL, student=student, representative=representative, table_name=table_name)
        else:
            return "Студент не найден", 404

    elif request.method == 'POST':
        action = request.form.get('action')

        if action == 'approve':
            with sqlite3.connect('chinaekb.db') as conn:
                c = conn.cursor()
                c.execute(f'SELECT * FROM {table_name} WHERE id = ?', (student_id,))
                student = c.fetchone()

                if student is None:
                    logger.error(f"Студент с ID {student_id} не найден в таблице {table_name}")
                    return json.dumps({"success": False, "message": "Студент не найден"}), 404, {'Content-Type': 'application/json'}

                if table_name == 'students':
                    c.execute('SELECT * FROM representatives WHERE student_id = ?', (student_id,))
                    representative = c.fetchone()
                    student_data = {
                        'id': student[0],
                        'last_name': student[1],
                        'first_name': student[2],
                        'middle_name': student[3],
                        'birth_date': student[4],
                        'address': student[5],
                        'gender': student[6],
                        'snils': student[7],
                        'age_group': student[8],
                        'id_type': student[9],
                        'id_serial': student[10],
                        'id_number': student[11],
                        'id_issued_by': student[12],
                        'id_issued_date': student[13],
                        'bank_details': student[14],
                        'phone': student[15],
                        'email': student[16],
                        'study_plan': student[17],
                        'exam_selection': student[18],
                        'exam_date': student[19],
                        'status': student[20],
                        'submission_date': student[21],
                        'representative': {
                            'last_name': representative[2],
                            'first_name': representative[3],
                            'middle_name': representative[4],
                            'birth_date': representative[5],
                            'address': representative[6],
                            'gender': representative[7],
                            'snils': representative[8],
                            'id_serial': representative[9],
                            'id_number': representative[10],
                            'id_issued_by': representative[11],
                            'id_issued_date': representative[12],
                            'bank_details': representative[13],
                            'phone': representative[14],
                            'email': representative[15]
                        } if representative else None
                    }
                elif table_name == 'adult_students':
                    student_data = {
                        'id': student[0],
                        'last_name': student[1],
                        'first_name': student[2],
                        'middle_name': student[3],
                        'birth_date': student[4],
                        'address': student[5],
                        'gender': student[6],
                        'snils': student[7],
                        'id_type': student[8],
                        'id_serial': student[9],
                        'id_number': student[10],
                        'id_issued_by': student[11],
                        'id_issued_date': student[12],
                        'bank_details': student[13],
                        'phone': student[14],
                        'email': student[15],
                        'study_plan': student[16],
                        'exam_selection': student[17],
                        'exam_date': student[18],
                        'status': student[19],
                        'submission_date': student[20]
                    }

                try:
                    response = requests.post('https://1c.rsvpu.ru/univer_prof_test/hs/confucius_center/put_contract',
                                             json=student_data, auth=('AbiturWeb', 's5*Uzjea'))
                    response.raise_for_status()
                    logger.info(f"Заявка {student_id} одобрена и отправлена в 1С")

                    c.execute(f'UPDATE {table_name} SET status = ? WHERE id = ?', ('проверено', student_id))
                    conn.commit()

                    file_paths = student[22].split(',') if len(student) > 22 else []
                    delete_files(file_paths)

                    session['success_message'] = "Заявка успешно отправлена в 1С"
                    return redirect(url_for('moderation'))
                except requests.exceptions.RequestException as e:
                    logger.error(f"Ошибка при отправке данных в 1С: {e}")
                    logger.error(f"Статус код: {response.status_code}")
                    logger.error(f"Текст ошибки: {response.text}")
                    return json.dumps({"success": False, "message": "Ошибка при отправке данных в 1С"}), 500, {'Content-Type': 'application/json'}

        elif action == 'reject':
            with sqlite3.connect('chinaekb.db') as conn:
                c = conn.cursor()
                c.execute(f'UPDATE {table_name} SET status = ? WHERE id = ?', ('отклонено', student_id))
                conn.commit()

            logger.info(f"Заявка {student_id} отклонена")
            return json.dumps({"success": True, "message": "Заявка отклонена"}), 200, {'Content-Type': 'application/json'}

        return json.dumps({"success": False, "message": "Неизвестное действие"}), 400, {'Content-Type': 'application/json'}

@app.route(BASE_URL + "/success")
def success():
    return render_template("success.html", base_url=BASE_URL)

@app.route(BASE_URL + "/<path:file_path>", methods=['GET', 'POST'])
def get_file(file_path):
    return send_from_directory(app.config['UPLOAD_FOLDER'], file_path)

if __name__ == "__main__":
    app.run("0.0.0.0", port=3000)