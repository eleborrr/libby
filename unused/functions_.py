from itsdangerous import URLSafeTimedSerializer
from wtforms import ValidationError

import models
from models.__all_models import Book, Edition, User, Library, Role
from libby import login_manager, app, mail, url
from libby.match import match
from flask import abort, render_template_string
from flask_mail import Message
from libby.qr_generators import _create_qr_list
from libby.consts import *
import uuid

if login_manager:
    @login_manager.user_loader
    def load_user(user_id):
        with models.create_session() as session:
            return session.query(User).get(user_id)


def create_user(login, surname, name, password, library_id, role_id):
    return User(login=login, surname=surname, name=name, password=password, library_id=library_id, role_id=role_id)


def create_library(school_name):
    return Library(school_name=school_name)


def create_edition(name, author, publication_year, library_id):
    return Edition(name=name, author=author, publication_year=publication_year, library_id=library_id)


def create_book(edition_id, owner_id=None):
    return Book(edition_id=edition_id, owner_id=owner_id)


def check_reg_confirm(user_id):
    with models.create_session() as session:
        return session.query(User).get(user_id).confirmed


def check_email_domen(form, content):
    if content.data.split('@')[1] != 'edu.tatar.ru':
        raise ValidationError('Почта должна относиться к edu.tatar.ru')


def create_role(name):
    return Role(name=name)


def create_roles():
    with models.create_session() as session:
        roles = ['Student', 'Librarian']
        for i in session.query(Role).all():
            roles.remove(i.name)
        for i in roles:
            session.add(create_role(i))
        session.commit()


def lend_book(user_id, book_id):
    with models.create_session() as session:
        book = session.query(Book).get(book_id)
        if not book.owner:
            book.owner_id = user_id
        session.commit()
        session.close()


def register_library(school_name, login, name, surname, password):
    """Функция, создающая библиотеку и регистрирующую библиотекаря, что её управляет"""
    with models.create_session() as session:
        library = create_library(school_name)
        library_id = session.query(Library).order_by(-Library.id).first()
        if not library_id:
            library_id = 1
        else:
            library_id = library_id.id
        session.add(library)
        librarian_role = session.query(Role).filter(Role.name == 'Librarian').first()
        user = create_user(login, surname, name, password, library_id, librarian_role.id)
        session.add(user)
        session.commit()
        return library.id, user.id


def register_student(login, name, surname, password, library_id):
    with models.create_session() as session:
        student_role = session.query(Role).filter(Role.name == 'Student').first()
        user = create_user(login, surname, name, password, library_id, student_role.id)
        session.add(user)
        session.commit()
        return user.id


def filter_books(library_id=None,
                 id_=None,
                 owner_id=None,
                 edition_id=None,
                 owner_surname=None,
                 free=None,
                 session=None):
    query = session.query(Book).join(Edition).filter(Edition.library_id == library_id)
    kwargs = {  # Значения, которые будут помещены в форму
        'id_': '',
        'owner_id': '',
        'owner_surname': '',
        'free': ''
    }

    if id_:
        query = query.filter(Book.id == int(id_))
        kwargs['id_'] = id_
    if edition_id:
        query = query.filter(Edition.id == edition_id)
    if owner_id:
        query = query.filter(Book.owner_id == int(owner_id))
        kwargs['owner_id'] = owner_id
    if free and int(free):
        query = query.filter(Book.owner_id == None)
        kwargs['free'] = int(free)
    if owner_surname:
        kwargs['owner_surname'] = owner_surname
    result = query.all()
    new_res = []
    for i in result:  # Фильтруем поля, требующие неточного сравнения
        try:
            if owner_surname:
                assert match(i.owner.surname.lower(), owner_surname.lower())
        except AssertionError:
            continue
        else:
            new_res.append(i)
    return new_res, kwargs


def filter_students(library_id=None,
                    id_=None,
                    surname=None,
                    name=None,
                    class_num=None,
                    class_letter=None,
                    session=None):
    student_role = session.query(Role).filter(Role.name == "Student").first().id
    query = session.query(User).filter(User.library_id == library_id)
    query = query.filter(User.role_id == student_role)
    kwargs = {
        'id_': '',
        'surname': '',
        'class_num': '',
        'class_letter': ''
    }

    try:  # Фильтруем все возможные поля через query
        if id_:
            query = query.filter(User.id == int(id_))
            kwargs['id_'] = id_
        if surname:
            query = query.filter(User.surname == surname)
            kwargs['surname'] = surname
        # if class_num:
        #     query = query.filter(User.class_num == class_num)
        #     kwargs['class_num'] = edition_id
        # if class_letter:
        #     query = query.filter(Book.owner_id == int(owner_id))
        #     kwargs['class_letter'] = owner_id
        # if free and int(free):
        #     query = query.filter(Book.owner_id == None)
        #     kwargs['free'] = int(free)
    except ValueError:
        return abort(400)
    result = query.all()
    new_res = []
    for i in result:  # Фильтруем поля, требующие неточного сравнения
        flag = True
        if name:
            kwargs['name'] = name
            if not match(i.edition.name.lower(), name.lower()):
                flag = False
        if surname:
            kwargs['surname'] = surname
            if not match(i.edition.author.lower(), surname.lower()):
                flag = False
        if class_num:
            kwargs['class_num'] = class_num
            if not match(i.edition.author.lower(), class_num.lower()):
                flag = False
        if class_letter:
            kwargs['class_letter'] = class_letter
            try:
                if not match(i.owner.surname.lower(), class_letter.lower()):
                    flag = False
            except AttributeError:
                flag = False
        if flag:
            new_res.append(i)
    return new_res, kwargs


def generate_edition_qr(edition_id, url='localhost:5000'):
    with models.create_session() as session:
        res = _create_qr_list([(x.generate_id(), x.id) for x in session.query(Edition).get(edition_id).books], url)[0]
        return res


def generate_token(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=app.config['SECURITY_PASSWORD_SALT'])


def send_email(user, target):
    email = user.login
    token = generate_token(email)
    if target == CONFIRM_EMAIL:  # confirm email
        link = f'{url}/confirm_email/{token}'
        template = render_template_string('Для подтверждения адреса электронной почты'
                                          'перейдите по <a href="{{ link }}">{{ link }}</a>', link=link)  # Можно вынести в отдельный файл
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


def filter_editions(library_id=None,
                    id_=None,
                    name=None,
                    author=None,
                    publication_year=None,
                    session=None):
    res = session.query(Edition).filter(Edition.library_id == library_id)
    kwargs = {
        'id_': '',
        'name': '',
        'author': '',
        'publication_year': ''
    }

    if publication_year:
        kwargs['publication_year'] = publication_year
        res = res.filter(Edition.publication_year == publication_year)
    if id_:
        kwargs['id_'] = id_
        res = res.filter(Edition.id == id_)
    if name:
        kwargs['name'] = name
    if author:
        kwargs['author'] = author

    res = res.all()
    new_res = []

    for edition in res:
        try:
            if name:
                assert match(edition.name.lower(), name.lower())
            if author:
                assert match(edition.author.lower(), author.lower())
        except AssertionError:
            continue
        else:
            new_res.append(edition)
    return new_res, kwargs


def get_page_of(target,
                page,
                filter_context):
    if target == TARGET_EDITION:
        f = filter_editions
    elif target == TARGET_BOOK:
        f = filter_books
    elif target == TARGET_STUDENT:
        f = filter_students
    else:
        raise ValueError('target должен быть TARGET_EDITION, TARGET_BOOK, TARGET_STUDENT')

    result = f(**filter_context)[0]
    page_limits = slice(PAGE_SIZE * (page - 1), PAGE_SIZE * page + 1)
    return result[page_limits]


def get_page_of_editions(page, filter_context):
    return get_page_of(TARGET_EDITION, page, filter_context)


def get_page_of_books(page, filter_context):
    return get_page_of(TARGET_BOOK, page, filter_context)


def get_page_of_students(page, filter_context):
    return get_page_of(TARGET_STUDENT, page, filter_context)


def make_url(final, form, **kwargs):
    args = []
    for i in kwargs:
        res = getattr(form, i).data
        if res:
            args.append(f'{i}={res}')
    if args:
        final += '?'
        final += '&'.join(args)
    return final


def get_id_of_last_edition():
    with models.create_session() as session:
        eds = session.query(Edition).all()
        eds.sort(key=lambda x: -x.id)
        return 0 if not eds else eds[0].id


def generate_name_for_edition_name(mod):
    return str(uuid.uuid4()) + '.' + mod


def allowed_image_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ['jpg', 'jpeg', 'png', 'webp', 'gif', 'svg']
