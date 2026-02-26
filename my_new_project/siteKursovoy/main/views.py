from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.models import User
from .models import CourseCard, Profession
from .models import CourseInfo
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import CourseCard, UserCourse, LessonProgress, Lesson
from .models import CourseCard, Profession
from django.http import HttpResponseForbidden
from django.contrib.auth.models import User
from .models import TestResult, AIAnalysis


def index(request):
    profession_id = request.GET.get('profession')  # берем id из фильтра
    professions = Profession.objects.all()

    if profession_id:
        courses = CourseCard.objects.filter(profession_id=profession_id)
    else:
        courses = CourseCard.objects.all()

    return render(request, 'main/index.html', {
        'courses': courses,
        'professions': professions,
        'selected_profession': profession_id
    })

def Kursy(request):
    return render(request, 'main/Kursy.html')

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Certificate

@login_required
def sertificates(request):
    certificates = Certificate.objects.filter(user=request.user).order_by('-issued_at')
    return render(request, 'main/sertificates.html', {'certificates': certificates})


from django.http import FileResponse

def certificate_view(request, cert_id):
    from .models import Certificate
    cert = Certificate.objects.get(id=cert_id)
    response = FileResponse(open(cert.file.path, 'rb'), content_type='application/pdf')
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


def Login(request):
    return render(request, 'main/Login.html')

@login_required
def Profile(request):
    user_courses = UserCourse.objects.filter(user=request.user)
    return render(request, 'main/Profile.html', {'user_courses': user_courses})

def Profile_edit(request):
    return render(request, 'main/Profile_edit.html')

def jj(request):
    return render(request, 'main/online_lesson.html')

def Register(request):
    return render(request, 'main/Register.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('index')  # заменишь на нужную страницу
        else:
            messages.error(request, 'Неверный логин или пароль')

    return render(request, 'main/Login.html')


from .models import Lesson, Comment
from django.template.loader import render_to_string
from django.http import HttpResponse

def filter_courses(request):
    prof_id = request.GET.get('profession')
    if prof_id:
        courses = CourseCard.objects.filter(profession_id=prof_id)
    else:
        courses = CourseCard.objects.all()[:10]

    html = render_to_string('partials/courses_grid.html', {'courses': courses})
    return HttpResponse(html)


@login_required
def home_view(request):
    profile = request.user.profile  # получаем профиль текущего пользователя
    user_courses = request.user.user_courses.all()  # курсы пользователя
    context = {
        'profile': profile,
        'user_courses': user_courses,
    }
    return render(request, 'main/Profile.html', context)



def register_view(request):
    if request.method == 'POST':
        # Данные для User
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm-password')

        # Данные для Profile
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        role = request.POST.get('role')  # если нужно хранить роль
        phone_number = request.POST.get('phone_number')  # если есть
        gender = request.POST.get('gender')  # если есть

        # Проверка пароля
        if password != confirm_password:
            messages.error(request, "Пароли не совпадают!")
            return render(request, 'main/Register.html')

        # Проверка уникальности логина
        if User.objects.filter(username=username).exists():
            messages.error(request, "Пользователь с таким именем уже существует!")
            return render(request, 'main/Register.html')

        # Создаём пользователя
        user = User.objects.create_user(username=username, email=email, password=password)

        # Создаём профиль (или обновляем автоматически через сигнал)
        profile = user.profile  # создаётся автоматически через сигнал post_save
        profile.first_name = first_name
        profile.last_name = last_name
        profile.gender = gender
        profile.phone_number = phone_number
        profile.role = role or "student"
        profile.save()

        messages.success(request, "Регистрация прошла успешно! Теперь войдите в аккаунт.")
        return redirect('Login')

    return render(request, 'main/Register.html')



from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.shortcuts import render, redirect

@login_required
def profile_settings(request):
    user = request.user
    profile = user.profile

    if request.method == 'POST':
        # Данные из формы
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone_number = request.POST.get('phone_number')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        photo = request.FILES.get('photo')

        # Меняем пароль
        if password:
            if password != password_confirm:
                messages.error(request, "Пароли не совпадают!")
                return redirect('profile_settings')
            else:
                user.set_password(password)
                update_session_auth_hash(request, user)  # сохраняем сессию после смены пароля

        # Обновляем профиль
        profile.first_name = first_name
        profile.last_name = last_name
        profile.phone_number = phone_number
        if photo:
            profile.photo = photo

        # Сохраняем изменения
        user.save()
        profile.save()

        messages.success(request, "Профиль успешно обновлён!")
        return redirect('Profile')

    return render(request, 'main/profile_settings.html', {
        'user': user,
        'profile': profile
    })





from django.db.models import Q

def courses_page(request):
    profession_id = request.GET.get('profession')  # фильтр по профессии
    query = request.GET.get('q', '')               # строка поиска

    professions = Profession.objects.all()
    courses = CourseCard.objects.all()

    # фильтр по профессии
    if profession_id:
        courses = courses.filter(profession_id=profession_id)

    # фильтр по поиску
    if query:
        courses = courses.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        )

    return render(request, 'main/courses.html', {
        'no_scroll': True,
        'courses': courses,
        'professions': professions,
        'selected_profession': profession_id,
        'query': query
    })



from django.http import JsonResponse
from django.db.models import Q

def ajax_search_courses(request):
    query = request.GET.get("q", "")
    profession_id = request.GET.get("profession")

    courses = CourseCard.objects.all()

    # фильтр по профессии
    if profession_id:
        courses = courses.filter(profession_id=profession_id)

    # фильтр поиска
    if query:
        courses = courses.filter(
            Q(title__icontains=query)
        )

    data = []
    for course in courses:
        data.append({
            "id": course.id,
            "title": course.title,
            "image": course.image.url if course.image else None,
        })

    return JsonResponse({"courses": data})





# def courses_page(request):
#     profession_id = request.GET.get('profession')  # берем id из фильтра
#     professions = Profession.objects.all()
#
#     if profession_id:
#         courses = CourseCard.objects.filter(profession_id=profession_id)
#     else:
#         courses = CourseCard.objects.all()
#
#     return render(request, 'main/courses.html', {
#         'no_scroll': True,
#         'courses': courses,
#         'professions': professions,
#         'selected_profession': profession_id
#     })







def coursesInf(request):
    coursesinf = CourseInfo.objects.all()

    return render(request, 'main/coursesInfo.html', {'coursesinf': coursesinf})





def course_detail(request, course_id):
    course = get_object_or_404(CourseCard, id=course_id)

    is_added = False
    if request.user.is_authenticated:
        is_added = UserCourse.objects.filter(user=request.user, course=course).exists()

    return render(request, "main/course_detail.html", {
        "course": course,
        "is_added": is_added
    })



# def course_detail(request, course_id):
#     course = get_object_or_404(CourseCard, id=course_id)
#     return render(request, 'main/course_detail.html', {'course': course})

'''def course_detail(request, id):
    course = get_object_or_404(CourseCard, id=id)
    return render(request, 'main/course_detail.html', {'course': course})'''




@login_required
def lesson_detail(request, course_id, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id, module__course_id=course_id)
    course = lesson.module.course

    # Прогресс урока
    user_course, _ = UserCourse.objects.get_or_create(user=request.user, course=course)
    lesson_progress, _ = LessonProgress.objects.get_or_create(user_course=user_course, lesson=lesson)

    # Комментарии
    if request.method == "POST":
        text = request.POST.get("text")
        if text:
            Comment.objects.create(lesson=lesson, user=request.user, text=text)
            return redirect("lesson_detail", course_id=course_id, lesson_id=lesson_id)

    comments = lesson.comments.all().order_by("-created_at")

    return render(request, 'main/lesson_detail.html', {
        'lesson': lesson,
        'course': course,
        'lesson_progress': lesson_progress,
        'comments': comments,
        'course_id': course_id,
        'video_path': lesson.video.url if lesson.video else None
    })



# @login_required
# def lesson_detail(request, course_id, lesson_id):
#     lesson = get_object_or_404(Lesson, id=lesson_id, module__course_id=course_id)
#     course = lesson.module.course
#
#     # Проверяем, добавил ли пользователь этот курс себе
#     user_course, _ = UserCourse.objects.get_or_create(user=request.user, course=course)
#
#     # Проверяем прогресс по уроку
#     lesson_progress, _ = LessonProgress.objects.get_or_create(user_course=user_course, lesson=lesson)
#     #
#     # # Формируем embed ссылку для видео
#     # embed_url = get_embed_url(lesson.video_url)
#
#     # Возвращаем контекст для шаблона
#     return render(request, 'main/lesson_detail.html', {
#         'lesson': lesson,
#         'course': course,
#         'lesson_progress': lesson_progress,
#         'course_id': course_id,
#         # 'embed_url': embed_url,
#         'video_path': lesson.video.url if lesson.video else None  # ← добавили путь к файлу
#     })



@login_required
def complete_lesson(request, course_id, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = get_object_or_404(CourseCard, id=course_id)
    user_course = UserCourse.objects.get(user=request.user, course=course)

    progress, created = LessonProgress.objects.get_or_create(
        user_course=user_course,
        lesson=lesson
    )
    progress.is_completed = True
    progress.completed_at = timezone.now()
    progress.save()

    # обновляем прогресс
    total_lessons = Lesson.objects.filter(module__course=course).count()
    completed_lessons = LessonProgress.objects.filter(user_course=user_course, is_completed=True).count()
    user_course.progress = (completed_lessons / total_lessons) * 100
    user_course.save()

    # переход к следующему уроку
    next_lesson = Lesson.objects.filter(
        module=lesson.module,
        order__gt=lesson.order
    ).order_by('order').first()

    if next_lesson:
        return redirect('lesson_detail', course_id=course.id, lesson_id=next_lesson.id)
    return redirect('course_learn', course_id=course.id)




@login_required
def add_to_my_courses(request, course_id):
    course = get_object_or_404(CourseCard, id=course_id)
    UserCourse.objects.get_or_create(user=request.user, course=course)
    return redirect('Profile')


'''@login_required
def my_courses(request):
    user_courses = UserCourse.objects.filter(user=request.user)
    return render(request, 'main/Profile.html', {'user_courses': user_courses})'''


@login_required
def course_learn(request, course_id):
    course = get_object_or_404(CourseCard, id=course_id)
    return render(request, 'main/course_learn.html', {'course': course})





# def get_embed_url(video_url):
#     """Преобразует любую ссылку YouTube в nocookie embed URL"""
#     video_url = video_url.strip()
#     video_id = ''
#
#     if 'watch?v=' in video_url:
#         video_id = video_url.split('watch?v=')[1].split('&')[0]
#     elif 'youtu.be/' in video_url:
#         video_id = video_url.split('youtu.be/')[1].split('?')[0]
#
#     if video_id:
#         return f'https://www.youtube-nocookie.com/embed/{video_id}'
#     return ''



from django.shortcuts import render, get_object_or_404
from .models import Module, LessonTest, TestResult

@login_required
def module_detail(request, module_id):
    module = get_object_or_404(Module, id=module_id)
    course = module.course

    # Находим предыдущий модуль
    previous_module = course.modules.filter(order__lt=module.order).last()

    if previous_module:
        previous_lessons = previous_module.lessons.all()
        user_course = request.user.user_courses.get(course=course)

        all_completed = all(
            lesson.lessonprogress_set.filter(user_course=user_course, is_completed=True).exists()
            for lesson in previous_lessons
        )

        if not all_completed:
            return render(request, 'main/locked_module.html', {
                'previous_module': previous_module
            })





from django.shortcuts import render, get_object_or_404, redirect
from .models import Lesson, LessonTest, Question, Answer, TestResult, LessonProgress

def take_test(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    test = getattr(lesson, 'test', None)

    if not test:
        return render(request, 'no_test.html', {'lesson': lesson})

    questions = test.questions.prefetch_related('answers')

    if request.method == 'POST':
        correct_count = 0
        total = questions.count()

        for q in questions:
            selected_id = request.POST.get(f'question_{q.id}')
            if selected_id:
                answer = Answer.objects.get(id=selected_id)
                if answer.is_correct:
                    correct_count += 1

        score = (correct_count / total) * 100 if total > 0 else 0
        passed = score >= 70  # например, минимум 70% для прохождения

        TestResult.objects.update_or_create(
            user=request.user,
            test=test,
            defaults={'score': score, 'passed': passed}
        )

        # Если тест пройден — отмечаем урок как завершённый
        user_course = request.user.user_courses.get(course=lesson.module.course)
        LessonProgress.objects.update_or_create(
            user_course=user_course,
            lesson=lesson,
            defaults={'is_completed': passed}
        )

        return render(request, 'main/test_result.html', {
            'lesson': lesson,
            'score': score,
            'passed': passed
        })

    return render(request, 'main/take_test.html', {
        'lesson': lesson,
        'test': test,
        'questions': questions
    })



@login_required
def course_learn(request, course_id):
    course = get_object_or_404(CourseCard, id=course_id)
    modules = course.modules.all().order_by('order')

    # Пройденные тесты пользователя
    user_tests = TestResult.objects.filter(user=request.user, passed=True)
    passed_tests = {result.test.id for result in user_tests}

    # Разблокированные модули
    passed_modules = set()
    for i, module in enumerate(modules):
        if i == 0:
            # Первый модуль всегда доступен
            passed_modules.add(module.id)
        else:
            prev_module = modules[i-1]
            prev_tests = [lesson.test.id for lesson in prev_module.lessons.all() if lesson.test]
            # Модуль доступен, если все тесты предыдущего модуля пройдены
            if all(tid in passed_tests for tid in prev_tests):
                passed_modules.add(module.id)

    context = {
        'course': course,
        'modules': modules,
        'passed_tests': passed_tests,
        'passed_modules': passed_modules,
    }
    return render(request, 'main/course_learn.html', context)




# from django.shortcuts import render, redirect, get_object_or_404
# from .models import Lesson, Comment
#
# def lesson_detail(request, course_id, lesson_id):
#     lesson = get_object_or_404(Lesson, id=lesson_id)
#
#     if request.method == "POST":
#         text = request.POST.get("text")
#         if text:
#             Comment.objects.create(
#                 lesson=lesson,
#                 user=request.user,
#                 text=text
#             )
#             return redirect("lesson_detail", course_id=course_id, lesson_id=lesson_id)
#
#     comments = lesson.comments.all().order_by("-created_at")
#
#     return render(request, "main/lesson_detail.html", {
#         "lesson": lesson,
#         "comments": comments,
#         "course_id": course_id
#     })








from .models import AIAnalysis, LessonTest, TestResult

def fake_ai_analysis(score: float):
    s = float(score)

    if s >= 90:
        return {
            "summary": "🔥 Отлично! Тема усвоена на высоком уровне.",
            "strengths": "✅ Ты хорошо понял ключевые понятия\n✅ Почти без ошибок",
            "weaknesses": "—",
            "recommendations": "➡️ Можешь переходить к следующему уроку",
        }
    elif s >= 75:
        return {
            "summary": "✅ Хороший результат, но есть мелкие пробелы.",
            "strengths": "✅ Нормальное понимание темы",
            "weaknesses": "⚠️ В некоторых вопросах были ошибки",
            "recommendations": "➡️ Повтори сложные моменты и закрепи материал",
        }
    elif s >= 60:
        return {
            "summary": "⚠️ Минимум пройден, но стоит повторить материал.",
            "strengths": "✅ База есть",
            "weaknesses": "⚠️ Ошибки в важных вопросах",
            "recommendations": "➡️ Пересмотри урок и пройди тест ещё раз",
        }
    else:
        return {
            "summary": "❌ Результат слабый — нужно повторить тему.",
            "strengths": "—",
            "weaknesses": "⚠️ Много ошибок",
            "recommendations": "➡️ Повтори урок, сделай конспект и попробуй снова",
        }


@login_required
def ai_analysis_page(request, course_id, lesson_id):
    """
    Демонстрация: показываем 'как будто ИИ анализирует'.
    Если записи в БД нет — создаём её из правил.
    """
    # находим тест урока и результат
    test = get_object_or_404(LessonTest, lesson_id=lesson_id, lesson__module__course_id=course_id)
    result = TestResult.objects.filter(user=request.user, test=test).first()

    if not result:
        # если человек не проходил тест — просто показываем пустую страницу/сообщение
        return render(request, "main/ai_analysis.html", {"lesson": test.lesson, "result": None, "analysis": None})

    # берём последнюю запись анализа
    # analysis = AIAnalysis.objects.filter(user=request.user, lesson_id=lesson_id).first()
    analysis = 0;

    # если анализа нет — "как будто ИИ" создал его
    if not analysis:
        data = fake_ai_analysis(result.score)
        analysis = AIAnalysis.objects.create(
            user=request.user,
            lesson=test.lesson,
            test_result=result,
            summary=data["summary"],
            strengths=data["strengths"],
            weaknesses=data["weaknesses"],
            recommendations=data["recommendations"],
        )

    return render(request, "main/ai_analysis.html", {
        "lesson": test.lesson,
        "result": result,
        "analysis": analysis
    })








def is_teacher(user) -> bool:
    return hasattr(user, "profile") and getattr(user.profile, "role", "student") == "teacher"


def teacher_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("Login")
        if not is_teacher(request.user):
            return HttpResponseForbidden("Только для учителя.")
        return view_func(request, *args, **kwargs)
    return wrapper


@teacher_required
def teacher_students_list(request):
    # Берём всех пользователей, у кого роль student
    students = User.objects.filter(profile__role="student").order_by("username")
    return render(request, "main/students_list.html", {"students": students})


@teacher_required
def teacher_student_detail(request, student_id):
    student = get_object_or_404(User, id=student_id, profile__role="student")

    results = (
        TestResult.objects
        .filter(user=student)
        .select_related("test__lesson__module__course")
        .order_by("-completed_at")
    )

    analyses = (
        AIAnalysis.objects
        .filter(user=student)
        .select_related("lesson__module__course")
        .order_by("-created_at")[:100]
    )

    return render(request, "main/student_detail.html", {
        "student": student,
        "results": results,
        "analyses": analyses,
    })



@login_required
def course_create(request):
    return render(request, 'main/course_create.html')

@login_required
def course_edit(request):
    return render(request, 'main/course_edit_list.html')
