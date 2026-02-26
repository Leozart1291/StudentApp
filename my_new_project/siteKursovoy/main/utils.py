from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from datetime import date
import os
from django.conf import settings
from PIL import Image


def generate_certificate(user, course):
    from .models import Certificate

    # Папка для сертификатов
    cert_dir = os.path.join(settings.MEDIA_ROOT, "certificates")
    os.makedirs(cert_dir, exist_ok=True)

    filename = f"certificate_{user.username}_{course.id}.pdf"
    filepath = os.path.join(cert_dir, filename)

    # 🔥 УДАЛЯЕМ файл, если он уже существует — чтобы не было старой версии
    if os.path.exists(filepath):
        os.remove(filepath)

    # Шрифт
    font_path = os.path.join(settings.BASE_DIR, "main", "static", "fonts", "Roboto-Regular.ttf")
    pdfmetrics.registerFont(TTFont('Roboto', font_path))

    # Фон
    bg_path = os.path.join(settings.BASE_DIR, "main", "static", "images", "cert.png")
    bg_image = ImageReader(Image.open(bg_path))

    # Создание PDF
    c = canvas.Canvas(filepath, pagesize=A4)
    width, height = A4

    c.drawImage(bg_image, 0, 0, width=width, height=height)

    # Имя пользователя
    first_name = user.profile.first_name or user.first_name
    last_name = user.profile.last_name or user.last_name

    # Текст
    c.setFont("Roboto", 22)
    c.drawCentredString(width / 2, height - 300, "КУРС АЯҚТАЛҒАНЫ ТУРАЛЫ СЕРТИФИКАТ")

    c.setFont("Roboto", 20)
    c.drawCentredString(width / 2, height / 1.9, f"Беріледі: {first_name} {last_name}")

    c.setFont("Roboto", 18)
    c.drawCentredString(width / 2, height - 600, f"Курс: {course.title}")

    c.setFont("Roboto", 16)
    c.drawCentredString(width / 2, height - 700, f"Дата: {date.today().strftime('%d.%m.%Y')}")

    c.save()

    # Перезапись сертификата в БД:
    # Удаляем старый, если он существует
    Certificate.objects.filter(user=user, course=course).delete()

    cert = Certificate.objects.create(
        user=user,
        course=course,
        file=f"certificates/{filename}",
    )
    return cert
