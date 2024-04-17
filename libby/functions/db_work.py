import models
from models.__all_models import Book, Edition, User, Library, Role
from libby.consts import *


def create_user(login, surname, name, password, library_id, role_id, class_number=None, class_literal=None):
    return User(login=login, surname=surname, name=name, password=password, library_id=library_id, role_id=role_id,
                class_number=class_number, class_literal=class_literal)


def create_library(school_name):
    return Library(school_name=school_name)


def create_edition(name, author, publication_year, library_id):
    return Edition(name=name, author=author, publication_year=publication_year, library_id=library_id)


def create_book(edition_id, owner_id=None):
    return Book(edition_id=edition_id, owner_id=owner_id)


def check_reg_confirm(user_id):
    with models.create_session() as session:
        return session.query(User).get(user_id).confirmed


def create_role(name):
    return Role(name=name)


def create_roles():
    with models.create_session() as session:
        roles = [Student, Librarian, WaitingStudent]
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


def register_student(login, name, surname, password, library_id, class_number=None, class_literal=None):
    with models.create_session() as session:
        student_role = session.query(Role).filter(Role.name == 'Student').first()
        user = create_user(login, surname, name, password, library_id, student_role.id, class_number, class_literal)
        session.add(user)
        session.commit()
        return user.id


def get_id_of_last_edition():
    with models.create_session() as session:
        eds = session.query(Edition).all()
        eds.sort(key=lambda x: -x.id)
        return 0 if not eds else eds[0].id


def get_role_id(name):
    with models.create_session() as session:
        role = session.query(Role).filter(Role.name == name).first()
        if role is None:
            return 0
        return role.id
