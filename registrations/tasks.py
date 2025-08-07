from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone
from datetime import timedelta
from events.models import Event
from .models import Registration

@shared_task
def send_ticket_email(user_email, username, registration_id):
    print(f"Sending email to {user_email}, for {username}, registration ID: {registration_id}")

    subject = 'Konfirmasi Tiket Event DevCoach'

    text_content = f"""Halo {username},

Terima kasih telah memesan tiket untuk Event DevCoach bersama Dicoding!

Berikut adalah detail pemesanan tiket Anda:

ID Pemesanan: {registration_id}

Silakan hadir 10 menit sebelum acara dimulai.

Kami tunggu kedatangan Anda di Event DevCoach!
Pesan ini dikirim secara otomatis. Mohon tidak membalas.

- Tim Penyelenggara DevCoach
"""

    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #2c3e50; background-color: #f9f9f9; padding: 20px;">
        <div style="max-width: 600px; margin: auto; background-color: #ffffff; padding: 30px; border-radius: 10px; border: 1px solid #e0e0e0;">
            <h2 style="color: #1A73E8; text-align: center;">🎟️ Konfirmasi Tiket Anda</h2>

            <p>Halo <strong>{username}</strong>,</p>

            <p>Terima kasih telah mendaftar pada <strong>Event DevCoach</strong> yang diselenggarakan oleh <strong>Dicoding</strong>! 🎉</p>

            <p><strong>Detail Tiket Anda:</strong></p>
            <div style="background-color: #f1f3f4; padding: 15px; border-radius: 8px; font-size: 16px;">
                <strong>ID Pemesanan:</strong> {registration_id}
            </div>

            <p style="margin-top: 20px;">Silakan hadir <strong>10 menit sebelum acara dimulai</strong> agar tidak ketinggalan sesi pembuka.</p>

            <p>Kami menantikan kehadiran Anda di <strong>Event DevCoach</strong>! 🚀</p>

            <hr style="margin: 30px 0;">

            <p style="font-size: 12px; color: #888; text-align: center;">
                Pesan ini dikirim secara otomatis. Mohon tidak membalas pesan ini.
                <br><strong>DevCoach Organizer Team</strong>
            </p>
        </div>
    </body>
    </html>
    """

    email = EmailMultiAlternatives(
        subject, text_content, 'no-reply@devcoach-dicoding.com', [user_email]
    )
    email.attach_alternative(html_content, "text/html")
    email.send()
    return f'Email sent to {user_email}'

@shared_task
def send_reminder_email():
    now = timezone.now()
    two_hours_later = now + timedelta(hours=2)

    events = Event.objects.filter(start_time__gte=now, start_time__lte=two_hours_later)

    for event in events:
        registrations = Registration.objects.filter(ticket_id__event_id=event)
        for registration in registrations:
            user = registration.user_id
            subject = f'Reminder: Event {event.name} is starting soon!'
            
            text_content = f"""Halo {user.username},

Ini adalah pengingat bahwa event "{event.name}" akan dimulai dalam 2 jam.

Detail Event:
- Nama: {event.name}
- Lokasi: {event.location}
- Waktu Mulai: {event.start_time.strftime('%Y-%m-%d %H:%M:%S')}

Jangan sampai ketinggalan!

- Tim Penyelenggara DevCoach
"""

            html_content = f"""
            <html>
            <body>
                <p>Halo {user.username},</p>
                <p>Ini adalah pengingat bahwa event "<strong>{event.name}</strong>" akan dimulai dalam 2 jam.</p>
                <p><strong>Detail Event:</strong></p>
                <ul>
                    <li><strong>Nama:</strong> {event.name}</li>
                    <li><strong>Lokasi:</strong> {event.location}</li>
                    <li><strong>Waktu Mulai:</strong> {event.start_time.strftime('%Y-%m-%d %H:%M:%S')}</li>
                </ul>
                <p>Jangan sampai ketinggalan!</p>
                <p>- Tim Penyelenggara DevCoach</p>
            </body>
            </html>
            """

            email = EmailMultiAlternatives(
                subject, text_content, 'no-reply@devcoach-dicoding.com', [user.email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send()

