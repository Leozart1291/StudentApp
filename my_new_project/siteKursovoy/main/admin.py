from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Profile, Profession, CourseCard, CourseInfo,
    Module, Lesson, UserCourse, LessonProgress,
    LessonTest, Question, Answer, TestResult,
    Certificate,
    AIAnalysis,   # ✅ добавили анализ
)


# -------------------------
# 📸 Профиль пользователя
# -------------------------
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "gender", "role", "photo")   # ✅ роль видна в админке
    list_filter = ("role", "gender")
    search_fields = ("user__username", "first_name", "last_name")


# -------------------------
# 💼 Профессии
# -------------------------
@admin.register(Profession)
class ProfessionAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


# -------------------------
# 📘 Информация о курсе
# -------------------------
@admin.register(CourseInfo)
class CourseInfoAdmin(admin.ModelAdmin):
    list_display = ("title",)
    search_fields = ("title",)


# -------------------------
# 🎓 Карточки курсов (+ inline Modules)
# -------------------------
class ModuleInline(admin.TabularInline):
    model = Module
    extra = 1
    fields = ("order", "title", "description")
    ordering = ("order",)


@admin.register(CourseCard)
class CourseCardAdmin(admin.ModelAdmin):
    list_display = ("title", "profession")
    list_filter = ("profession",)
    search_fields = ("title",)
    inlines = [ModuleInline]


# -------------------------
# 📚 Модули (+ inline Lessons)
# -------------------------
class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1
    fields = ("order", "title")
    ordering = ("order",)


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "order")
    list_filter = ("course",)
    search_fields = ("title",)
    inlines = [LessonInline]
    ordering = ("course", "order")


# -------------------------
# 🧠 Уроки
# -------------------------
@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "module", "order")
    list_filter = ("module",)
    search_fields = ("title",)
    ordering = ("module", "order")


# -------------------------
# 👨‍🎓 Курсы пользователей
# -------------------------
@admin.register(UserCourse)
class UserCourseAdmin(admin.ModelAdmin):
    list_display = ("user", "course", "progress", "started_at")
    list_filter = ("course",)
    search_fields = ("user__username", "course__title")


# -------------------------
# 📈 Прогресс уроков
# -------------------------
@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ("user_course", "lesson", "is_completed", "completed_at")
    list_filter = ("is_completed", "lesson")
    search_fields = ("user_course__user__username", "lesson__title")


# -------------------------
# 🧪 Тесты / Вопросы / Ответы
# -------------------------
class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 1
    fields = ("order", "text", "is_correct")
    ordering = ("order",)


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1
    fields = ("order", "text")
    ordering = ("order",)
    show_change_link = True


@admin.register(LessonTest)
class LessonTestAdmin(admin.ModelAdmin):
    list_display = ("lesson", "title")
    search_fields = ("lesson__title", "title")
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("__str__", "test")
    list_filter = ("test",)
    search_fields = ("text",)
    inlines = [AnswerInline]
    ordering = ("test", "order")


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ("__str__", "question", "is_correct")
    list_filter = ("is_correct", "question__test")
    search_fields = ("text",)
    ordering = ("question", "order")


@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ("user", "test", "score", "passed", "completed_at")
    list_filter = ("passed", "completed_at", "test__lesson__module__course")
    search_fields = ("user__username", "test__lesson__title")


# -------------------------
# 🤖 Анализ (визуальный “ИИ”)
# -------------------------
@admin.register(AIAnalysis)
class AIAnalysisAdmin(admin.ModelAdmin):
    list_display = ("user", "lesson", "created_at")
    list_filter = ("lesson__module__course", "created_at")
    search_fields = ("user__username", "lesson__title", "summary")
    readonly_fields = ("created_at",)


# -------------------------
# 🧾 Сертификаты
# -------------------------
@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ("user", "course", "issued_at", "file_link")
    list_filter = ("issued_at", "course")
    search_fields = ("user__username", "course__title")
    readonly_fields = ("issued_at",)

    def file_link(self, obj):
        if obj.file:
            return format_html('<a href="{}" target="_blank">Скачать</a>', obj.file.url)
        return "-"

    file_link.short_description = "Файл"