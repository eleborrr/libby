from models.__all_models import Book, Edition, User, Role
from flask import abort
from libby.match import match
from libby.consts import *
from libby.functions.db_work import get_role_id


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


def get_waits(library_id=None, session=None):
    wait_role_id = get_role_id(WaitingStudent)
    return session.query(User).filter(User.role_id == wait_role_id).filter(User.library_id == library_id).all(), None  # Всегда должно возвращаться 2 значения


def get_page_of(f,
                page,
                filter_context):
    result = f(**filter_context)[0]
    page_limits = slice(PAGE_SIZE * (page - 1), PAGE_SIZE * page)
    return result[page_limits]


def get_page_of_editions(page, filter_context):
    return get_page_of(filter_editions, page, filter_context)


def get_page_of_books(page, filter_context):
    return get_page_of(filter_books, page, filter_context)


def get_page_of_students(page, filter_context):
    return get_page_of(filter_students, page, filter_context)


def get_page_of_waits(page, filter_context):
    return get_page_of(get_waits, page, filter_context)