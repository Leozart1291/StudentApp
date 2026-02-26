from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    ROLE_CHOICES = (
        ("student", "Студент"),
        ("teacher", "Учитель"),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField("Имя", max_length=30, null=True, blank=True)
    last_name = models.CharField("Фамилия", max_length=30, null=True, blank=True)
    phone_number = models.CharField("Номер телефона", max_length=20, null=True, blank=True)
    photo = models.ImageField(upload_to='profile_photos/', default='default.jpg')
    gender = models.CharField(max_length=10, null=True, blank=True)

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="student")  # ✅ добавь

    def __str__(self):
        return self.user.username



from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()



# БД с профессиями
class Profession(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name




# БД с инфой о курсах
from django.db import models

class CourseInfo(models.Model):
    title = models.CharField(max_length=255)
    description1 = models.TextField(blank=True, null=True)
    description2 = models.TextField(blank=True, null=True)
    description3 = models.TextField(blank=True, null=True)
    image1 = models.ImageField(upload_to='courses/', blank=True, null=True)
    image2 = models.ImageField(upload_to='courses/', blank=True, null=True)

    def __str__(self):
        return self.title




# БД с карточками курсов
class CourseCard(models.Model):
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='courses/images/', blank=True, null=True)
    profession = models.ForeignKey(Profession, on_delete=models.CASCADE, related_name='courses')
    info = models.OneToOneField('CourseInfo', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.title







# БД с модули курсов
class Module(models.Model):
    course = models.ForeignKey(CourseCard, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0)  # чтобы сортировать модули

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.course.title} — {self.title}"






# БД с уроки в модулях
# class Lesson(models.Model):
#     module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='lessons')
#     title = models.CharField(max_length=200)
#     content = models.TextField()  # текст урока
#     video_url = models.URLField(blank=True, null=True)  # ссылка на YouTube
#     order = models.PositiveIntegerField(default=0)
#
#     class Meta:
#         ordering = ['order']
#
#     def __str__(self):
#         return f"{self.module.title}: {self.title}"



class Lesson(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    content = models.TextField()
    video = models.FileField(upload_to='videos/', blank=True, null=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.module.title}: {self.title}"





# БД с курсов у пользователя
class UserCourse(models.Model):
    """Курс, который пользователь добавил к себе"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_courses')
    course = models.ForeignKey(CourseCard, on_delete=models.CASCADE, related_name='user_courses')
    progress = models.FloatField(default=0.0)  # процент прохождения, например 0–100
    started_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'course')

    def __str__(self):
        return f"{self.user.username} — {self.course.title}"





from .utils import generate_certificate  # импорт функции (создай в utils.py)

# БД с прогрессом курса
class LessonProgress(models.Model):
    user_course = models.ForeignKey(UserCourse, on_delete=models.CASCADE, related_name='lesson_progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.user_course.user.username} — {self.lesson.title}"



    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # обновляем прогресс курса
        all_lessons = Lesson.objects.filter(module__course=self.user_course.course).count()
        completed = LessonProgress.objects.filter(user_course=self.user_course, is_completed=True).count()
        if all_lessons > 0:
            self.user_course.progress = (completed / all_lessons) * 100
            self.user_course.save()

        if self.user_course.progress == 100:
            from .models import Certificate
            if not Certificate.objects.filter(user=self.user_course.user, course=self.user_course.course).exists():
                generate_certificate(self.user_course.user, self.user_course.course)






class LessonTest(models.Model):
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE, related_name='test')
    title = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.lesson.title} Тест"


class Question(models.Model):
    test = models.ForeignKey(LessonTest, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()

    def __str__(self):
        return f"Вопрос: {self.text[:50]}..."


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"Ответ: {self.text} ({'верный' if self.is_correct else 'ошибка'})"


class TestResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    test = models.ForeignKey(LessonTest, on_delete=models.CASCADE)
    score = models.FloatField(default=0)
    passed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'test')

    def __str__(self):
        return f"{self.user.username} — {self.test.lesson.title} — {self.score:.0f}%"









class LessonTest(models.Model):
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE, related_name='test')
    title = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Тест к уроку: {self.lesson.title}"


class Question(models.Model):
    test = models.ForeignKey(LessonTest, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.order}. {self.text[:60]}"


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.order}. {self.text[:50]} ({'✔' if self.is_correct else '✖'})"


class TestResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    test = models.ForeignKey(LessonTest, on_delete=models.CASCADE)
    score = models.FloatField(default=0)
    passed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(auto_now_add=True)



from django.db import models
from django.contrib.auth.models import User

class Certificate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="certificates")
    course = models.ForeignKey("CourseCard", on_delete=models.CASCADE, related_name="certificates")
    file = models.FileField(upload_to="certificates/")
    issued_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Сертификат: {self.user.get_full_name()} — {self.course.title}"




class Comment(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.text[:50]}"




class AIAnalysis(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ai_analyses")
    lesson = models.ForeignKey("Lesson", on_delete=models.CASCADE, related_name="ai_analyses")
    test_result = models.ForeignKey("TestResult", on_delete=models.SET_NULL, null=True, blank=True)

    summary = models.TextField()
    strengths = models.TextField(blank=True)       # строкой (проще чем JSON)
    weaknesses = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"AIAnalysis {self.user.username} — {self.lesson.title}"


