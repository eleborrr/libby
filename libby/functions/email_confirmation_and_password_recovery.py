from itsdangerous import URLSafeTimedSerializer
from libby import app, mail, url
from libby.consts import *
from flask import render_template_string
from flask_mail import Message
from models.__all_models import User


def generate_token(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=app.config['SECURITY_PASSWORD_SALT'])


def send_email(user, target):
    email = user.login
    token = generate_token(email)
    if target == CONFIRM_EMAIL:  # confirm email
        link = f'{url}/confirm_email/{token}'
        template = render_template_string('Для подтверждения адреса электронной почты перейдите по <a href="{{ link }}">ссылке</a>', link=link)  # Можно вынести в отдельный файл
        subject = 'Подтверждение адреса электронной почте на сайте libby.ru'
    elif target == CHANGE_PASSWORD:  # change password:
        link = f'change_password/{token}'
        template = render_template_string('Для смены пароля перейдите '
                                          'по <a href="{{ link }}">ссылке</a>', link=link)  # Можно вынести в отдельный файл
        subject = 'Изменение пароля к аккаунту на сайте libby.ru'
    else:
        raise ValueError
    message = Message(subject=subject, recipients=[email], html=template)
    mail.send(message)


def confirm_token(token, secret_key, expiration=3600):
    serializer = URLSafeTimedSerializer(secret_key)
    try:
        email = serializer.loads(
            token,
            salt=app.config['SECURITY_PASSWORD_SALT'],
            max_age=expiration
        )
    except Exception:
        return False
    return email


def get_user_by_token(token, session, secrete_key):
    email = confirm_token(token, secrete_key)
    user = session.query(User).filter(User.login == email).first()
    return user