from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
                  path('', views.index, name='index'),
                  path('filter_courses/', views.filter_courses, name='filter_courses'),
                  path('Kursy/', views.Kursy, name='Kursy'),
                  path('Login/', views.Login, name='Login'),
                  path('Profile/', views.Profile, name='Profile'),
                  path('Profile_edit/', views.Profile_edit, name='Profile_edit'),
                  path('Register/', views.Register, name='Register'),
                  path('login/', views.login_view, name='login'),
                  path('register/', views.register_view, name='register'),
                  path('logout/', auth_views.LogoutView.as_view(), name='logout'),
                  path('sertificates/', views.sertificates, name='sertificates'),

                  path('courses/', views.courses_page, name='courses'),
                  path('courses/search/', views.ajax_search_courses, name='ajax_search_courses'),
                  path('courses/<int:course_id>/', views.course_detail, name='course_detail'),
                  path('profile/settings/', views.profile_settings, name='profile_settings'),
                  path('jj/', views.jj, name='jj'),

                  # уроки
                  path('course/<int:course_id>/lesson/<int:lesson_id>/', views.lesson_detail, name='lesson_detail'),
                  path('course/<course_id>/lesson/<lesson_id>/complete/', views.complete_lesson,
                       name='complete_lesson'),

                  # мои курсы
                  path('courses/<int:course_id>/add/', views.add_to_my_courses, name='add_to_my_courses'),
                  path('my-courses/<int:course_id>/', views.course_learn, name='course_learn'),


                path('course_create/', views.course_create, name='course_create'),
                path('course_edit_list/', views.course_edit, name='course_edit_list'),

                path("teacher/students/", views.teacher_students_list, name="teacher_students_list"),
                path("teacher/students/<int:student_id>/", views.teacher_student_detail, name="teacher_student_detail"),

                path("course/<int:course_id>/lesson/<int:lesson_id>/ai/", views.ai_analysis_page, name="ai_analysis_page"),

                # Модули курса (с проверкой доступа)
                path('module/<int:module_id>/', views.module_detail, name='module_detail'),

                # (опционально) Тест к уроку
                path('lesson/<int:lesson_id>/test/', views.take_test, name='lesson_test'),



] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

