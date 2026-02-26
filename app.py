from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response, send_file, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import json
import os
import qrcode
import io
import secrets
import string
import re
import urllib.request
import urllib.error
import urllib.parse

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'

# API-ключ Gemini (лучше задать через переменную окружения GEMINI_API_KEY)
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'AIzaSyDt9x0gVQYNronwUjMOlQjLrESqWxj9kXw')
GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent'

# Файлы для хранения данных
USERS_FILE = 'users.json'
LESSONS_FILE = 'lessons.json'
ACTIVE_LESSONS_FILE = 'active_lessons.json'
CHAT_MESSAGES_FILE = 'chat_messages.json'

# Функции для работы с JSON
def load_users():
    """Загрузить пользователей из JSON файла"""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []

def save_users(users):
    """Сохранить пользователей в JSON файл"""
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def find_user_by_username(username):
    """Найти пользователя по имени"""
    users = load_users()
    for user in users:
        if user['username'] == username:
            return user
    return None

def find_user_by_email(email):
    """Найти пользователя по email"""
    users = load_users()
    for user in users:
        if user['email'] == email:
            return user
    return None

def find_user_by_id(user_id):
    """Найти пользователя по ID"""
    users = load_users()
    for user in users:
        if user['id'] == user_id:
            return user
    return None

def get_next_id():
    """Получить следующий ID для нового пользователя"""
    users = load_users()
    if not users:
        return 1
    return max(user['id'] for user in users) + 1

def update_user(user_id, **kwargs):
    """Обновить данные пользователя"""
    users = load_users()
    for i, user in enumerate(users):
        if user['id'] == user_id:
            for key, value in kwargs.items():
                if key != 'id':  # ID нельзя изменять
                    users[i][key] = value
            save_users(users)
            return True
    return False

# Функции для работы с уроками
def load_lessons():
    """Загрузить уроки из JSON файла"""
    if os.path.exists(LESSONS_FILE):
        try:
            with open(LESSONS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []

def save_lessons(lessons):
    """Сохранить уроки в JSON файл"""
    with open(LESSONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(lessons, f, ensure_ascii=False, indent=2)

def get_next_lesson_id():
    """Получить следующий ID для нового урока"""
    lessons = load_lessons()
    if not lessons:
        return 1
    return max(lesson['id'] for lesson in lessons) + 1

def add_lesson(title, description, teacher_id, tasks=None):
    """Добавить новый урок"""
    lessons = load_lessons()
    
    # Обработка заданий: может быть JSON строка или список
    tasks_list = []
    if tasks:
        if isinstance(tasks, str):
            # Попробовать распарсить как JSON
            try:
                tasks_list = json.loads(tasks)
                if not isinstance(tasks_list, list):
                    tasks_list = []
            except (json.JSONDecodeError, ValueError):
                # Если не JSON, обработать как старый формат (строки через перенос)
                tasks_list = [{'type': 'text', 'content': task.strip(), 'id': i} 
                             for i, task in enumerate(tasks.split('\n')) if task.strip()]
        elif isinstance(tasks, list):
            tasks_list = tasks
    
    new_lesson = {
        'id': get_next_lesson_id(),
        'title': title,
        'description': description,
        'teacher_id': teacher_id,
        'tasks': tasks_list,
        'created_at': None  # Можно добавить дату создания
    }
    lessons.append(new_lesson)
    save_lessons(lessons)
    return new_lesson

def get_lessons_by_teacher(teacher_id):
    """Получить все уроки учителя"""
    lessons = load_lessons()
    return [lesson for lesson in lessons if lesson['teacher_id'] == teacher_id]

def find_lesson_by_id(lesson_id):
    """Найти урок по ID"""
    lessons = load_lessons()
    for lesson in lessons:
        if lesson['id'] == lesson_id:
            return lesson
    return None

def update_lesson(lesson_id, title, description, teacher_id, tasks=None):
    """Обновить существующий урок"""
    lessons = load_lessons()
    
    # Найти урок
    for i, lesson in enumerate(lessons):
        if lesson['id'] == lesson_id:
            # Проверить, что урок принадлежит учителю
            if lesson['teacher_id'] != teacher_id:
                return False
            
            # Обработка заданий: может быть JSON строка или список
            tasks_list = []
            if tasks:
                if isinstance(tasks, str):
                    # Попробовать распарсить как JSON
                    try:
                        tasks_list = json.loads(tasks)
                        if not isinstance(tasks_list, list):
                            tasks_list = []
                    except (json.JSONDecodeError, ValueError):
                        # Если не JSON, обработать как старый формат (строки через перенос)
                        tasks_list = [{'type': 'text', 'content': task.strip(), 'id': i} 
                                     for i, task in enumerate(tasks.split('\n')) if task.strip()]
                elif isinstance(tasks, list):
                    tasks_list = tasks
            
            # Обновить данные урока
            lessons[i]['title'] = title
            lessons[i]['description'] = description
            lessons[i]['tasks'] = tasks_list
            
            save_lessons(lessons)
            return True
    
    return False

import json
import os
import tempfile

FILE_PATH = "active_lessons.json"

def load_active_lessons():
    if not os.path.exists(FILE_PATH):
        return []

    try:
        with open(FILE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []

def save_active_lessons(active_lessons):
    dir_name = os.path.dirname(FILE_PATH)

    with tempfile.NamedTemporaryFile(
        'w',
        encoding='utf-8',
        dir=dir_name,
        delete=False
    ) as tmp:
        json.dump(active_lessons, tmp, ensure_ascii=False, indent=2)
        temp_name = tmp.name

    # атомарно заменяет файл
    os.replace(temp_name, FILE_PATH)

def generate_access_code():
    """Сгенерировать код доступа (6 символов)"""
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))

def create_active_lesson(lesson_id, teacher_id):
    """Создать активный урок"""
    active_lessons = load_active_lessons()
    access_code = generate_access_code()
    
    active_lesson = {
        'lesson_id': lesson_id,
        'teacher_id': teacher_id,
        'access_code': access_code,
        'is_active': True,
        'students': []  # Список присоединившихся учеников
    }
    
    # Удалить старые активные уроки этого учителя
    active_lessons = [al for al in active_lessons if al['teacher_id'] != teacher_id]
    active_lessons.append(active_lesson)
    save_active_lessons(active_lessons)
    
    return access_code

def get_active_lesson_by_code(access_code):
    """Получить активный урок по коду"""
    active_lessons = load_active_lessons()
    for active_lesson in active_lessons:
        if active_lesson['access_code'] == access_code and active_lesson.get('is_active', True):
            return active_lesson
    return None

def get_active_lesson_by_teacher(teacher_id):
    """Получить активный урок учителя"""
    active_lessons = load_active_lessons()
    for active_lesson in active_lessons:
        if active_lesson['teacher_id'] == teacher_id and active_lesson.get('is_active', True):
            return active_lesson
    return None

def stop_active_lesson(teacher_id):
    """Остановить активный урок учителя"""
    active_lessons = load_active_lessons()
    for active_lesson in active_lessons:
        if active_lesson['teacher_id'] == teacher_id:
            active_lesson['is_active'] = False
            # Очистить текущее видео при остановке урока
            if 'current_video' in active_lesson:
                del active_lesson['current_video']
    save_active_lessons(active_lessons)

def set_current_gesture_video(access_code, video_url, video_text):
    """Установить текущее воспроизводимое видео жеста для урока"""
    import datetime
    active_lessons = load_active_lessons()
    for active_lesson in active_lessons:
        if active_lesson['access_code'] == access_code and active_lesson.get('is_active', True):
            active_lesson['current_video'] = {
                'url': video_url,
                'text': video_text,
                'timestamp': datetime.datetime.now().isoformat()
            }
            save_active_lessons(active_lessons)
            return True
    return False

def get_current_gesture_video(access_code, last_timestamp=None):
    """Получить текущее воспроизводимое видео жеста для урока"""
    active_lesson = get_active_lesson_by_code(access_code)
    if not active_lesson or 'current_video' not in active_lesson:
        return None
    
    video = active_lesson['current_video']
    
    # Если указан last_timestamp, вернуть видео только если оно новее
    if last_timestamp:
        if video['timestamp'] <= last_timestamp:
            return None
    
    return video

# Камера учителя: кадр (base64) и субтитры для учеников
def set_teacher_frame(access_code, frame_base64):
    """Сохранить текущий кадр камеры учителя (для отображения у учеников)"""
    import datetime
    active_lessons = load_active_lessons()
    for active_lesson in active_lessons:
        if active_lesson['access_code'] == access_code and active_lesson.get('is_active', True):
            active_lesson['teacher_frame'] = {
                'data': frame_base64,
                'timestamp': datetime.datetime.now().isoformat()
            }
            save_active_lessons(active_lessons)
            return True
    return False

def get_teacher_frame(access_code):
    """Получить последний кадр камеры учителя"""
    active_lesson = get_active_lesson_by_code(access_code)
    if not active_lesson or 'teacher_frame' not in active_lesson:
        return None
    return active_lesson['teacher_frame']

def set_teacher_subtitle(access_code, text):
    """Сохранить текущий текст субтитров (распознанная речь учителя)"""
    import datetime
    active_lessons = load_active_lessons()
    for active_lesson in active_lessons:
        if active_lesson['access_code'] == access_code and active_lesson.get('is_active', True):
            active_lesson['teacher_subtitle'] = {
                'text': text,
                'timestamp': datetime.datetime.now().isoformat()
            }
            save_active_lessons(active_lessons)
            return True
    return False

def get_teacher_subtitle(access_code, last_timestamp=None):
    """Получить последний текст субтитров учителя"""
    active_lesson = get_active_lesson_by_code(access_code)
    if not active_lesson or 'teacher_subtitle' not in active_lesson:
        return None
    sub = active_lesson['teacher_subtitle']
    if last_timestamp and sub.get('timestamp', '') <= last_timestamp:
        return None
    return sub

# Функции для работы с учениками в активных уроках
def add_student_to_lesson(access_code, user_id):
    """Добавить ученика к активному уроку"""
    active_lessons = load_active_lessons()
    for active_lesson in active_lessons:
        if active_lesson['access_code'] == access_code and active_lesson.get('is_active', True):
            # Проверить, что ученик еще не добавлен
            if 'students' not in active_lesson:
                active_lesson['students'] = []
            
            # Проверить, не добавлен ли уже этот ученик
            if user_id not in active_lesson['students']:
                active_lesson['students'].append(user_id)
                save_active_lessons(active_lessons)
                return True
            return True  # Уже добавлен
    return False

def get_lesson_students(access_code):
    """Получить список учеников активного урока"""
    active_lesson = get_active_lesson_by_code(access_code)
    if not active_lesson:
        return []
    
    students = active_lesson.get('students', [])
    # Получить данные о каждом ученике
    students_data = []
    for student_id in students:
        user = find_user_by_id(student_id)
        if user and user['role'] == 'student':
            students_data.append({
                'id': user['id'],
                'username': user['username'],
                'email': user['email']
            })
    return students_data

# Функции для работы с сообщениями чата
def load_chat_messages():
    """Загрузить сообщения чата"""
    if os.path.exists(CHAT_MESSAGES_FILE):
        try:
            with open(CHAT_MESSAGES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}

def save_chat_messages(chat_messages):
    """Сохранить сообщения чата"""
    with open(CHAT_MESSAGES_FILE, 'w', encoding='utf-8') as f:
        json.dump(chat_messages, f, ensure_ascii=False, indent=2)

def add_chat_message(access_code, user_id, username, message_text, role):
    """Добавить сообщение в чат урока"""
    import datetime
    chat_messages = load_chat_messages()
    
    if access_code not in chat_messages:
        chat_messages[access_code] = []
    
    message = {
        'id': len(chat_messages[access_code]) + 1,
        'user_id': user_id,
        'username': username,
        'role': role,
        'message': message_text,
        'timestamp': datetime.datetime.now().isoformat()
    }
    
    chat_messages[access_code].append(message)
    save_chat_messages(chat_messages)
    return message

def get_chat_messages(access_code, last_message_id=0):
    """Получить сообщения чата урока"""
    chat_messages = load_chat_messages()
    
    if access_code not in chat_messages:
        return []
    
    # Вернуть только новые сообщения (после last_message_id)
    all_messages = chat_messages[access_code]
    new_messages = [msg for msg in all_messages if msg['id'] > last_message_id]
    return new_messages

# Декоратор для проверки авторизации
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Пожалуйста, войдите в систему для доступа к этой странице.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Декоратор для проверки роли учителя
def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Пожалуйста, войдите в систему.', 'warning')
            return redirect(url_for('login'))
        user = find_user_by_id(session['user_id'])
        if not user or user['role'] != 'teacher':
            flash('Доступ разрешен только учителям.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """Маршрут главной страницы"""
    if 'user_id' in session:
        user = find_user_by_id(session['user_id'])
        if user and user['role'] == 'teacher':
            teacher_lessons = get_lessons_by_teacher(user['id'])
            active_lesson_data = get_active_lesson_by_teacher(user['id'])
            active_lesson_info = None
            if active_lesson_data:
                lesson_info = find_lesson_by_id(active_lesson_data['lesson_id'])
                if lesson_info:
                    active_lesson_info = {
                        **active_lesson_data,
                        'title': lesson_info['title']
                    }
            return render_template('index.html', user=user, teacher_lessons=teacher_lessons, active_lesson=active_lesson_info)
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Маршрут регистрации"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')  # 'teacher' или 'student'
        
        # Проверка обязательных полей
        if not username or not email or not password or not role:
            flash('Пожалуйста, заполните все поля.', 'danger')
            return render_template('register.html')
        
        # Проверка существования пользователя
        if find_user_by_username(username):
            flash('Пользователь с таким именем уже существует.', 'danger')
            return render_template('register.html')
        
        if find_user_by_email(email):
            flash('Пользователь с таким email уже существует.', 'danger')
            return render_template('register.html')
        
        # Создание нового пользователя
        users = load_users()
        new_user = {
            'id': get_next_id(),
            'username': username,
            'email': email,
            'password_hash': generate_password_hash(password),
            'role': role
        }
        users.append(new_user)
        save_users(users)
        
        flash('Регистрация прошла успешно! Теперь вы можете войти.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Маршрут входа"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Пожалуйста, заполните все поля.', 'danger')
            return render_template('login.html')
        
        user = find_user_by_username(username)
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            flash(f'Добро пожаловать, {user["username"]}!', 'success')
            
            # Если есть ожидающий код урока, перенаправить на урок
            if 'pending_lesson_code' in session:
                code = session.pop('pending_lesson_code')
                return redirect(url_for('lesson', access_code=code))
            
            return redirect(url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Маршрут выхода"""
    session.clear()
    flash('Вы успешно вышли из системы.', 'success')
    return redirect(url_for('index'))

@app.route('/lesson')
@app.route('/lesson/<access_code>')
def lesson(access_code=None):
    """Маршрут страницы урока"""
    if not access_code:
        # Учитель заходит на свой урок - требует авторизацию
        if 'user_id' not in session:
            flash('Пожалуйста, войдите в систему.', 'warning')
            return redirect(url_for('login'))
        
        user = find_user_by_id(session['user_id'])
        if user and user['role'] == 'teacher':
            active_lesson = get_active_lesson_by_teacher(user['id'])
            if active_lesson:
                lesson_data = find_lesson_by_id(active_lesson['lesson_id'])
                if lesson_data:
                    return render_template('lesson.html', lesson=lesson_data, access_code=active_lesson['access_code'], current_user=user)
            flash('У вас нет активного урока. Запустите урок на главной странице.', 'info')
            return redirect(url_for('index'))
    else:
        # Ученик входит по коду - может быть без авторизации
        active_lesson = get_active_lesson_by_code(access_code)
        if not active_lesson:
            flash('Неверный код доступа или урок не активен.', 'danger')
            return redirect(url_for('enter_code'))
        
        lesson_data = find_lesson_by_id(active_lesson['lesson_id'])
        if not lesson_data:
            flash('Урок не найден.', 'danger')
            return redirect(url_for('enter_code'))
        
        # Если пользователь не авторизован, сохранить код в сессии для возможной авторизации
        if 'user_id' not in session:
            session['current_lesson_code'] = access_code
        else:
            session['current_lesson_code'] = access_code
            # Если пользователь авторизован как ученик, добавить его к уроку
            user = find_user_by_id(session['user_id'])
            if user and user['role'] == 'student':
                add_student_to_lesson(access_code, user['id'])
        
        # Передать информацию о текущем пользователе, если он авторизован
        current_user = None
        if 'user_id' in session:
            current_user = find_user_by_id(session['user_id'])
        return render_template('lesson.html', lesson=lesson_data, access_code=access_code, current_user=current_user)

@app.route('/start_lesson/<int:lesson_id>')
@teacher_required
def start_lesson(lesson_id):
    """Запустить урок (для учителя)"""
    user = find_user_by_id(session['user_id'])
    lesson_data = find_lesson_by_id(lesson_id)
    
    if not lesson_data or lesson_data['teacher_id'] != user['id']:
        flash('Урок не найден или вы не являетесь его автором.', 'danger')
        return redirect(url_for('index'))
    
    access_code = create_active_lesson(lesson_id, user['id'])
    flash('Урок успешно запущен!', 'success')
    return redirect(url_for('show_lesson_code', access_code=access_code))

@app.route('/lesson_code/<access_code>')
@teacher_required
def show_lesson_code(access_code):
    """Показать код и QR для урока"""
    user = find_user_by_id(session['user_id'])
    active_lesson = get_active_lesson_by_code(access_code)
    
    if not active_lesson or active_lesson['teacher_id'] != user['id']:
        flash('Доступ запрещен.', 'danger')
        return redirect(url_for('index'))
    
    lesson_data = find_lesson_by_id(active_lesson['lesson_id'])
    lesson_url = request.url_root + f'lesson/{access_code}'
    
    return render_template('lesson_code.html', access_code=access_code, lesson=lesson_data, lesson_url=lesson_url)

@app.route('/qr_code/<access_code>')
def qr_code(access_code):
    """Генерация QR-кода"""
    try:
        # Генерация URL для урока
        base_url = request.url_root.rstrip('/')
        lesson_url = f"{base_url}/lesson/{access_code}"
        
        # Создание QR-кода
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=5,
        )
        qr.add_data(lesson_url)
        qr.make(fit=True)
        
        # Создание изображения
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Сохранение в байтовый поток
        img_io = io.BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)
        
        # Возврат изображения
        response = make_response(img_io.getvalue())
        response.headers['Content-Type'] = 'image/png'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    except Exception as e:
        # В случае ошибки создать простое изображение с текстом ошибки
        app.logger.error(f"QR generation error: {str(e)}")
        try:
            from PIL import Image, ImageDraw
            img = Image.new('RGB', (200, 200), color=(255, 255, 255))
            draw = ImageDraw.Draw(img)
            error_text = f"Error: {str(e)[:15]}"
            draw.text((20, 90), error_text, fill=(0, 0, 0))
            img_io = io.BytesIO()
            img.save(img_io, 'PNG')
            img_io.seek(0)
            response = make_response(img_io.getvalue())
            response.headers['Content-Type'] = 'image/png'
            return response
        except Exception as e2:
            app.logger.error(f"Fallback QR error: {str(e2)}")
            return "", 500

@app.route('/enter_code', methods=['GET', 'POST'])
def enter_code():
    """Ввод кода урока (для учеников)"""
    # Проверка, что пользователь авторизован как ученик (или может войти без авторизации)
    if request.method == 'POST':
        code = request.form.get('code', '').strip().upper()
        if not code:
            flash('Введите код доступа.', 'danger')
            return render_template('enter_code.html')
        
        active_lesson = get_active_lesson_by_code(code)
        if not active_lesson:
            flash('Неверный код доступа или урок не активен.', 'danger')
            return render_template('enter_code.html')
        
        # Если пользователь не авторизован, сохранить код в сессии и перенаправить на логин
        if 'user_id' not in session:
            session['pending_lesson_code'] = code
            flash('Пожалуйста, войдите в систему для доступа к уроку.', 'warning')
            return redirect(url_for('login'))
        
        return redirect(url_for('lesson', access_code=code))
    
    return render_template('enter_code.html')

@app.route('/stop_lesson')
@teacher_required
def stop_lesson():
    """Остановить активный урок"""
    user = find_user_by_id(session['user_id'])
    stop_active_lesson(user['id'])
    flash('Урок остановлен.', 'success')
    return redirect(url_for('index'))

import json
from flask import request, session, flash, redirect, url_for, render_template
from werkzeug.security import check_password_hash, generate_password_hash

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Маршрут страницы профиля"""
    user = find_user_by_id(session['user_id'])

    if not user:
        flash('Пользователь не найден.', 'danger')
        return redirect(url_for('index'))

    # ========= CREATE LESSON =========
    if request.method == 'POST' and request.form.get('action') == 'add_lesson':
        if user['role'] != 'teacher':
            flash('Только учителя могут создавать уроки.', 'danger')
            return redirect(url_for('profile'))

        title = (request.form.get('lesson_title') or '').strip()
        description = (request.form.get('lesson_description') or '').strip()

        raw = request.form.get('lesson_tasks', '')
        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        tasks_list = [{"type": "text", "content": line} for line in lines]
        tasks_json = json.dumps(tasks_list, ensure_ascii=False)

        if not title or not description:
            flash('Пожалуйста, заполните все обязательные поля урока.', 'danger')
            teacher_lessons = get_lessons_by_teacher(user['id'])
            # распарсим tasks для шаблона
            for lesson in teacher_lessons:
                t = lesson.get('tasks', '[]')
                try:
                    lesson['tasks'] = json.loads(t) if isinstance(t, str) and t.strip() else (t if isinstance(t, list) else [])
                except Exception:
                    lesson['tasks'] = []
            return render_template('profile.html', user=user, teacher_lessons=teacher_lessons)

        add_lesson(title, description, user['id'], tasks_json)
        flash('Урок успешно создан!', 'success')
        return redirect(url_for('profile'))

    # ========= EDIT LESSON =========
    elif request.method == 'POST' and request.form.get('action') == 'edit_lesson':
        if user['role'] != 'teacher':
            flash('Только учителя могут редактировать уроки.', 'danger')
            return redirect(url_for('profile'))

        lesson_id_raw = request.form.get('lesson_id')
        if not lesson_id_raw:
            flash('ID урока не указан.', 'danger')
            return redirect(url_for('profile'))

        try:
            lesson_id = int(lesson_id_raw)
        except ValueError:
            flash('Неверный ID урока.', 'danger')
            return redirect(url_for('profile'))

        lesson = find_lesson_by_id(lesson_id)
        if not lesson or lesson.get('teacher_id') != user['id']:
            flash('Урок не найден или вы не являетесь его автором.', 'danger')
            return redirect(url_for('profile'))

        title = (request.form.get('lesson_title') or '').strip()
        description = (request.form.get('lesson_description') or '').strip()

        raw = request.form.get('lesson_tasks', '')
        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        tasks_list = [{"type": "text", "content": line} for line in lines]
        tasks_json = json.dumps(tasks_list, ensure_ascii=False)

        if not title or not description:
            flash('Пожалуйста, заполните все обязательные поля урока.', 'danger')
            teacher_lessons = get_lessons_by_teacher(user['id'])
            for lesson in teacher_lessons:
                t = lesson.get('tasks', '[]')
                try:
                    lesson['tasks'] = json.loads(t) if isinstance(t, str) and t.strip() else (t if isinstance(t, list) else [])
                except Exception:
                    lesson['tasks'] = []
            return render_template('profile.html', user=user, teacher_lessons=teacher_lessons)

        if update_lesson(lesson_id, title, description, user['id'], tasks_json):
            flash('Урок успешно обновлен!', 'success')
        else:
            flash('Ошибка при обновлении урока.', 'danger')

        return redirect(url_for('profile'))

    # ========= UPDATE PROFILE =========
    elif request.method == 'POST':
        new_username = (request.form.get('username') or '').strip()
        new_email = (request.form.get('email') or '').strip()
        new_password = request.form.get('password') or ''
        current_password = request.form.get('current_password') or ''

        if not check_password_hash(user['password_hash'], current_password):
            flash('Неверный текущий пароль.', 'danger')
            teacher_lessons = get_lessons_by_teacher(user['id']) if user['role'] == 'teacher' else []
            for lesson in teacher_lessons:
                t = lesson.get('tasks', '[]')
                try:
                    lesson['tasks'] = json.loads(t) if isinstance(t, str) and t.strip() else (t if isinstance(t, list) else [])
                except Exception:
                    lesson['tasks'] = []
            return render_template('profile.html', user=user, teacher_lessons=teacher_lessons)

        if new_username != user['username']:
            if find_user_by_username(new_username):
                flash('Пользователь с таким именем уже существует.', 'danger')
                teacher_lessons = get_lessons_by_teacher(user['id']) if user['role'] == 'teacher' else []
                for lesson in teacher_lessons:
                    t = lesson.get('tasks', '[]')
                    try:
                        lesson['tasks'] = json.loads(t) if isinstance(t, str) and t.strip() else (t if isinstance(t, list) else [])
                    except Exception:
                        lesson['tasks'] = []
                return render_template('profile.html', user=user, teacher_lessons=teacher_lessons)

        if new_email != user['email']:
            existing_user = find_user_by_email(new_email)
            if existing_user and existing_user['id'] != user['id']:
                flash('Пользователь с таким email уже существует.', 'danger')
                teacher_lessons = get_lessons_by_teacher(user['id']) if user['role'] == 'teacher' else []
                for lesson in teacher_lessons:
                    t = lesson.get('tasks', '[]')
                    try:
                        lesson['tasks'] = json.loads(t) if isinstance(t, str) and t.strip() else (t if isinstance(t, list) else [])
                    except Exception:
                        lesson['tasks'] = []
                return render_template('profile.html', user=user, teacher_lessons=teacher_lessons)

        update_data = {
            'username': new_username,
            'email': new_email
        }

        if new_password:
            update_data['password_hash'] = generate_password_hash(new_password)

        if update_user(user['id'], **update_data):
            session['username'] = new_username
            flash('Профиль успешно обновлен!', 'success')
            return redirect(url_for('profile'))
        else:
            flash('Ошибка при обновлении профиля.', 'danger')

    # ========= GET PAGE =========
    teacher_lessons = get_lessons_by_teacher(user['id']) if user['role'] == 'teacher' else []

    # ✅ JSON string -> list for template
    for lesson in teacher_lessons:
        t = lesson.get('tasks', '[]')
        if isinstance(t, str):
            try:
                lesson['tasks'] = json.loads(t) if t.strip() else []
            except Exception:
                lesson['tasks'] = []
        elif isinstance(t, list):
            lesson['tasks'] = t
        else:
            lesson['tasks'] = []

    return render_template('profile.html', user=user, teacher_lessons=teacher_lessons)
@app.route('/api/lesson/<access_code>/join', methods=['POST'])
@login_required
def join_lesson_api(access_code):
    """API: Присоединить ученика к уроку"""
    user = find_user_by_id(session['user_id'])
    if not user or user['role'] != 'student':
        return jsonify({'error': 'Только ученики могут присоединяться к урокам'}), 403
    
    active_lesson = get_active_lesson_by_code(access_code)
    if not active_lesson:
        return jsonify({'error': 'Урок не найден или не активен'}), 404
    
    if add_student_to_lesson(access_code, user['id']):
        return jsonify({'success': True, 'message': 'Вы успешно присоединились к уроку'}), 200
    else:
        return jsonify({'error': 'Не удалось присоединиться к уроку'}), 500

@app.route('/api/lesson/<access_code>/students', methods=['GET'])
def get_lesson_students_api(access_code):
    """API: Получить список учеников урока"""
    # Проверка, что урок существует
    active_lesson = get_active_lesson_by_code(access_code)
    if not active_lesson:
        return jsonify({'error': 'Урок не найден или не активен'}), 404
    
    # Проверка прав доступа (только учитель или ученики этого урока)
    if 'user_id' in session:
        user = find_user_by_id(session['user_id'])
        if user['role'] == 'teacher' and active_lesson['teacher_id'] == user['id']:
            # Учитель может видеть всех учеников
            students = get_lesson_students(access_code)
            return jsonify({'success': True, 'students': students}), 200
        elif user['role'] == 'student' and user['id'] in active_lesson.get('students', []):
            # Ученик может видеть список других учеников
            students = get_lesson_students(access_code)
            return jsonify({'success': True, 'students': students}), 200
    
    return jsonify({'error': 'Доступ запрещен'}), 403

@app.route('/api/lesson/<access_code>/chat/send', methods=['POST'])
def send_chat_message(access_code):
    """API: Отправить сообщение в чат урока"""
    # Проверка, что урок существует
    active_lesson = get_active_lesson_by_code(access_code)
    if not active_lesson:
        return jsonify({'error': 'Урок не найден или не активен'}), 404
    
    # Проверка авторизации
    if 'user_id' not in session:
        return jsonify({'error': 'Требуется авторизация'}), 401
    
    user = find_user_by_id(session['user_id'])
    if not user:
        return jsonify({'error': 'Пользователь не найден'}), 404
    
    # Проверка прав доступа
    is_teacher = user['role'] == 'teacher' and active_lesson['teacher_id'] == user['id']
    is_student = user['role'] == 'student' and user['id'] in active_lesson.get('students', [])
    
    if not (is_teacher or is_student):
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    # Получить текст сообщения
    data = request.get_json()
    message_text = data.get('message', '').strip()
    
    if not message_text:
        return jsonify({'error': 'Сообщение не может быть пустым'}), 400
    
    # Добавить сообщение
    message = add_chat_message(access_code, user['id'], user['username'], message_text, user['role'])
    
    return jsonify({'success': True, 'message': message}), 200

@app.route('/api/lesson/<access_code>/chat/messages', methods=['GET'])
def get_chat_messages_api(access_code):
    """API: Получить сообщения чата урока"""
    # Проверка, что урок существует
    active_lesson = get_active_lesson_by_code(access_code)
    if not active_lesson:
        return jsonify({'error': 'Урок не найден или не активен'}), 404
    
    # Проверка авторизации
    if 'user_id' not in session:
        return jsonify({'error': 'Требуется авторизация'}), 401
    
    user = find_user_by_id(session['user_id'])
    if not user:
        return jsonify({'error': 'Пользователь не найден'}), 404
    
    # Проверка прав доступа
    is_teacher = user['role'] == 'teacher' and active_lesson['teacher_id'] == user['id']
    is_student = user['role'] == 'student' and user['id'] in active_lesson.get('students', [])
    
    if not (is_teacher or is_student):
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    # Получить ID последнего сообщения (для получения только новых)
    last_message_id = request.args.get('last_id', 0, type=int)
    
    # Получить сообщения
    messages = get_chat_messages(access_code, last_message_id)
    
    return jsonify({'success': True, 'messages': messages}), 200

def call_gemini_explain_for_sign_language(text):
    """
    Вызвать Gemini API: разобрать и объяснить текст простыми фразами для глухих и языка жестов.
    Возвращает строку с объяснением или None при ошибке.
    """
    if not text or not text.strip():
        return None
    if not GEMINI_API_KEY:
        app.logger.warning('GEMINI_API_KEY не задан')
        return None
    prompt = (
        'Ты помогаешь переводить речь в текст, понятный для глухих и людей, изучающих язык жестов. '
        'Разбей и объясни следующий текст простыми короткими фразами, по шагам. '
        'Используй простые слова, без сложных терминов. Каждая мысль — с новой строки. '
        'Язык ответа — тот же, что и в тексте (русский или казахский). '
        'Ответь только текстом объяснения, без вступлений.\n\nТекст: '
    ) + text.strip()
    payload = {
        'contents': [
            {
                'parts': [{'text': prompt}]
            }
        ]
    }
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            GEMINI_API_URL,
            data=data,
            headers={
                'Content-Type': 'application/json',
                'x-goog-api-key': GEMINI_API_KEY,
            },
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode('utf-8'))
        candidates = result.get('candidates') or []
        if not candidates:
            return None
        parts = candidates[0].get('content', {}).get('parts') or []
        if not parts:
            return None
        return (parts[0].get('text') or '').strip()
    except Exception as e:
        app.logger.exception('Ошибка вызова Gemini: %s', e)
        return None


@app.route('/api/explain-for-sign-language', methods=['POST'])
def explain_for_sign_language():
    """
    API: Получить от Gemini объяснение текста для глухих (простыми фразами для языка жестов).
    Тело: JSON { "text": "распознанная фраза" }.
    """
    data = request.get_json() or {}
    text = (data.get('text') or '').strip()
    if not text:
        return jsonify({'success': False, 'error': 'Текст не передан'}), 400
    if len(text) > 2000:
        return jsonify({'success': False, 'error': 'Текст слишком длинный'}), 400
    explanation = call_gemini_explain_for_sign_language(text)
    if explanation is None:
        return jsonify({'success': False, 'error': 'Не удалось получить объяснение'}), 502
    return jsonify({'success': True, 'explanation': explanation, 'original': text}), 200


@app.route('/api/gesture-videos/list', methods=['GET'])
def get_gesture_videos_list():
    """API: Получить список доступных видео жестов"""
    video_dir = os.path.join(os.path.dirname(__file__), 'video')
    videos = []
    
    if os.path.exists(video_dir):
        for filename in os.listdir(video_dir):
            if filename.lower().endswith(('.mp4', '.webm', '.mov', '.avi')):
                # Извлечь текст из названия файла (убрать расширение)
                video_text = os.path.splitext(filename)[0]
                videos.append({
                    'filename': filename,
                    'text': video_text,
                    'url': url_for('get_gesture_video', filename=filename)
                })
    
    return jsonify({'success': True, 'videos': videos}), 200

@app.route('/video/<filename>')
def get_gesture_video(filename):
    """Отдать видео файл"""
    video_dir = os.path.join(os.path.dirname(__file__), 'video')
    return send_from_directory(video_dir, filename)

UPLOADS_DIR = os.path.join(os.path.dirname(__file__), 'uploads')

@app.route('/uploads/<path:filename>')
def get_upload_file(filename):
    """Отдать прикреплённый файл задания (для скачивания)"""
    if not os.path.exists(UPLOADS_DIR):
        return '', 404
    return send_from_directory(UPLOADS_DIR, filename, as_attachment=True)

@app.route('/api/lesson/<access_code>/gesture-video/set', methods=['POST'])
def set_gesture_video_api(access_code):
    """API: Установить текущее видео жеста (для учителя)"""
    # Проверка, что урок существует
    active_lesson = get_active_lesson_by_code(access_code)
    if not active_lesson:
        return jsonify({'error': 'Урок не найден или не активен'}), 404
    
    # Проверка авторизации и прав учителя
    if 'user_id' not in session:
        return jsonify({'error': 'Требуется авторизация'}), 401
    
    user = find_user_by_id(session['user_id'])
    if not user or user['role'] != 'teacher' or active_lesson['teacher_id'] != user['id']:
        return jsonify({'error': 'Доступ разрешен только учителю урока'}), 403
    
    # Получить данные видео
    data = request.get_json()
    video_url = data.get('url', '')
    video_text = data.get('text', '')
    
    if not video_url:
        return jsonify({'error': 'URL видео не указан'}), 400
    
    if set_current_gesture_video(access_code, video_url, video_text):
        return jsonify({'success': True}), 200
    else:
        return jsonify({'error': 'Не удалось установить видео'}), 500

@app.route('/api/lesson/<access_code>/gesture-video/get', methods=['GET'])
def get_gesture_video_api(access_code):
    """API: Получить текущее видео жеста (для учеников)"""
    # Проверка, что урок существует
    active_lesson = get_active_lesson_by_code(access_code)
    if not active_lesson:
        return jsonify({'error': 'Урок не найден или не активен'}), 404
    
    # Проверка авторизации
    if 'user_id' not in session:
        return jsonify({'error': 'Требуется авторизация'}), 401
    
    user = find_user_by_id(session['user_id'])
    if not user:
        return jsonify({'error': 'Пользователь не найден'}), 404
    
    # Проверка прав доступа (учитель или ученик урока)
    is_teacher = user['role'] == 'teacher' and active_lesson['teacher_id'] == user['id']
    is_student = user['role'] == 'student' and user['id'] in active_lesson.get('students', [])
    
    if not (is_teacher or is_student):
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    # Получить timestamp последнего полученного видео
    last_timestamp = request.args.get('last_timestamp', None)
    
    video = get_current_gesture_video(access_code, last_timestamp)
    
    if video:
        return jsonify({'success': True, 'video': video}), 200
    else:
        return jsonify({'success': True, 'video': None}), 200

@app.route('/api/lesson/<access_code>/teacher-frame', methods=['GET', 'POST'])
def teacher_frame_api(access_code):
    """API: GET — получить кадр камеры учителя; POST — установить кадр (учитель)"""
    active_lesson = get_active_lesson_by_code(access_code)
    if not active_lesson:
        return jsonify({'error': 'Урок не найден или не активен'}), 404
    if 'user_id' not in session:
        return jsonify({'error': 'Требуется авторизация'}), 401
    user = find_user_by_id(session['user_id'])
    if request.method == 'POST':
        if not user or user['role'] != 'teacher' or active_lesson['teacher_id'] != user['id']:
            return jsonify({'error': 'Только учитель урока может отправлять кадр'}), 403
        data = request.get_json()
        frame_base64 = data.get('frame', '')
        if not frame_base64:
            return jsonify({'error': 'Нет данных кадра'}), 400
        if set_teacher_frame(access_code, frame_base64):
            return jsonify({'success': True}), 200
        return jsonify({'error': 'Ошибка сохранения'}), 500
    frame = get_teacher_frame(access_code)
    if frame:
        return jsonify({'success': True, 'frame': frame.get('data'), 'timestamp': frame.get('timestamp')}), 200
    return jsonify({'success': True, 'frame': None}), 200

@app.route('/api/lesson/<access_code>/teacher-subtitle', methods=['GET', 'POST'])
def teacher_subtitle_api(access_code):
    """API: GET — получить субтитры учителя; POST — установить субтитры (учитель)"""
    active_lesson = get_active_lesson_by_code(access_code)
    if not active_lesson:
        return jsonify({'error': 'Урок не найден или не активен'}), 404
    if 'user_id' not in session:
        return jsonify({'error': 'Требуется авторизация'}), 401
    user = find_user_by_id(session['user_id'])
    if request.method == 'POST':
        if not user or user['role'] != 'teacher' or active_lesson['teacher_id'] != user['id']:
            return jsonify({'error': 'Только учитель может отправлять субтитры'}), 403
        data = request.get_json() or {}
        text = (data.get('text') or '').strip()
        set_teacher_subtitle(access_code, text)
        return jsonify({'success': True}), 200
    last_ts = request.args.get('last_timestamp', None)
    sub = get_teacher_subtitle(access_code, last_ts)
    if sub:
        return jsonify({'success': True, 'text': sub.get('text', ''), 'timestamp': sub.get('timestamp')}), 200
    return jsonify({'success': True, 'text': None}), 200

if __name__ == '__main__':
    import socket
    # Получить локальный IP адрес
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    print("\n" + "="*50)
    print("Сервер запущен!")
    print("="*50)
    print(f"Локальный доступ: http://127.0.0.1:9000")
    print(f"Сеть (WiFi): http://{local_ip}:9000")
    print("="*50)
    print("\nДля доступа с телефона:")
    print(f"1. Убедитесь, что телефон подключен к той же WiFi сети")
    print(f"2. Откройте в браузере телефона: http://{local_ip}:9000")
    print("="*50 + "\n")
    
    app.run(host='0.0.0.0', port=9000, debug=True)
