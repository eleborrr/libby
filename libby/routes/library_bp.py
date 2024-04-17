from libby.functions import *
from libby.routes import log_dec
from libby import app
from libby.forms import *
from flask import render_template, redirect, url_for, request, Blueprint, jsonify
from flask_login import current_user, login_user, logout_user, login_required
import models
from libby.qr_generators import *

lb = Blueprint('library', __name__)


@lb.route('/')
def index():
    return redirect('/library/editions')


@log_dec
@lb.route('/editions', methods=['GET', 'POST'], strict_slashes=False)
@login_required
def editions():
    wait_role_id = get_role_id('WaitingStudent')
    if not check_reg_confirm(current_user.id):
        return redirect('/confirm_email')
    if current_user.library_id is None or current_user.role_id == wait_role_id:
        return redirect('/library/wait_room')
    id_ = request.args.get('id_')
    name = request.args.get('name')
    author = request.args.get('author')
    publication_year = request.args.get('publication_year')
    try:
        if publication_year is not None:
            publication_year = int(publication_year)
    except ValueError:
        return abort(400, description='publication year should be integer')
    with models.create_session() as session:
        new_res, kwargs = filter_editions(library_id=current_user.library_id,
                                          id_=id_,
                                          name=name,
                                          author=author,
                                          publication_year=publication_year,
                                          session=session)

        form = edition_filter_form(**kwargs)
        if form.validate_on_submit():
            url = make_url('/library/editions', form, **kwargs)
            return redirect(url)
        cur_user = session.query(User).get(current_user.id)
        return render_template('editions.html',
                               editions=new_res,
                               form=form,
                               library_code=cur_user.library.generate_id(),
                               current_user=cur_user,
                               url_for=url_for, generator=EditionsCodeGenerator())


@log_dec
@lb.route('/wait_room')
@login_required
def wait_room():
    with models.create_session() as session:
        lib_role_id = get_role_id(Librarian)
        if current_user.role_id == lib_role_id:
            return redirect('/library/editions')
        if current_user.library_id is None:
            lib = None
        else:
            lib = session.query(Library).get(current_user.library_id)
        return "Wait room"  # Нужен html, наследуемый от base-table, передать lib как аргумент в render_template


@log_dec
@lb.route('/accept_room')
@login_required
def accept_room():
    with models.create_session() as session:
        lib_role_id = get_role_id('Librarian')
        if current_user.role_id != lib_role_id:
            return redirect('/library/editions')
        waits = session.query(User).join(Role).filter(Role.name == 'WaitingStudent').all()  # LazyLoad
        return 'Accept'  # Нужен html, наследуемый от base-table, передать waits (если нет lazyload) как аргумент в render_template


@log_dec
@lb.route('/send_join_request/<int:library_id>')
@login_required
def send_join_request(library_id):
    st_role_id = get_role_id(Student)
    wait_role_id = get_role_id(WaitingStudent)
    if current_user.role_id != st_role_id or current_user.library_id is not None:
        return redirect('/library')
    with models.create_session() as session:
        lib = session.query(Library).get(library_id)
        if lib is None:
            return redirect('/library/wait_room')
        cur_us = session.query(User).get(current_user.id)
        cur_us.role_id = wait_role_id
        cur_us.library_id = library_id
        session.commit()
        return redirect('/accept_room')


@log_dec
@lb.route('/accept_student/<int:student_id>')
@login_required
def accept_student(student_id):
    lib_role_id = get_role_id(Librarian)
    wait_role_id = get_role_id(WaitingStudent)
    st_role_id = get_role_id(Student)

    if current_user.role_id != lib_role_id:
        return redirect('/library/editions')
    with models.create_session() as session:
        st = session.query(User).get(student_id)
        if st.role_id != wait_role_id or st.library_id != current_user.library_id:
            return redirect('/library/editions')
        st.role_id = st_role_id
        session.commit()
        return redirect('/library/accept_room')


@log_dec
@lb.route('/refuse_student/<int:student_id>')
@login_required
def refuse_student(student_id):
    lib_role_id = get_role_id(Librarian)
    wait_role_id = get_role_id(WaitingStudent)

    if current_user.role_id != lib_role_id:
        return redirect('/library/editions')
    with models.create_session() as session:
        st = session.query(User).get(student_id)
        if st.role_id != wait_role_id or st.library_id != current_user.library_id:
            return redirect('/library/editions')
        st.library_id = None
        session.commit()
        return redirect('/library/accept_room')


@log_dec
@lb.route('/editions/<int:edition_id>')
@login_required
def edition_route(edition_id):
    if not check_reg_confirm(current_user.id):
        return redirect('/confirm_email')
    with models.create_session() as session:
        edition_ = session.query(Edition).get(edition_id)
        if not edition_:
            return abort(404, description='Неверный идентификатор издания')
        if edition_.library_id != current_user.library_id:
            return abort(403, 'В вашей библиотеке нет такого издания')
        books = session.query(Book).filter(Book.edition_id == edition_id).all()
        return render_template('editionone.html', books=books, count_books=len(books), edition=edition_,
                               url_for=url_for, current_user=current_user, generator=EditionCodeGenerator())


@log_dec
@lb.route('/edition_qr/<int:edition_id>')
@login_required
def edition_qr(edition_id):
    if not check_reg_confirm(current_user.id):
        return redirect('/confirm_email')
    with models.create_session() as session:
        edition_ = session.query(Edition).get(edition_id)
        if not edition_:
            return abort(404, description='Неверный идентификатор издания')
        if edition_.library_id != current_user.library_id:
            return abort(403, 'В вашей библиотеке нет такого издания')
        lists = generate_edition_qr(edition_id, url)
        return render_template("qrs.html", url_for=url_for, edition=edition_, lists=lists, current_user=current_user)


@log_dec
@lb.route('/book/<int:book_id>')
@login_required
def book(book_id):
    if not check_reg_confirm(current_user.id):
        return redirect('/confirm_email')
    with models.create_session() as session:
        book = session.query(Book).get(book_id)
        if not book:
            return abort(404, description='Книга не найдена')
        if book.edition.library_id != current_user.library_id:
            return abort(403, 'Эта книга приписана к другой библиотеке')
        img = create_qrcode(book.generate_id(), book.id, url)
        return render_template('bookone.html', book=book, user=current_user, img=img)


@log_dec
@lb.route('/students', methods=['GET', 'POST'], strict_slashes=False)
@login_required
def students():
    if not check_reg_confirm(current_user.id):
        return redirect('/confirm_email')
    with models.create_session() as session:
        librarian_role = session.query(Role).filter(Role.name == 'Librarian').first()
        if current_user.role_id != librarian_role.id:
            return abort(403, description='Сюда можно только библиотекарю')
        id_, surname, name, class_num, class_letter = request.args.get('id_'), request.args.get(
            'surname'), request.args.get('surname'), request.args.get(
            'class_num'), request.args.get('class_letter')
        res = filter_students(current_user.library_id, id_, surname, name, class_num, class_letter, session)
        if type(res) != tuple:
            return res
        new_res, kwargs = res
        form = student_filter_form(**kwargs)
        if form.validate_on_submit():
            final = '/library/students'
            url = make_url(final, form, **kwargs)
            return redirect(url)
        library_code = session.query(Library).get(current_user.library_id).generate_id()
        return render_template('students.html', students=new_res, form=form, library_code=library_code, generator=StudentsCodeGenerator())


@log_dec
@login_required
@lb.route('/delete_edition/<int:id>')
def delete_edition(id):
    if not check_reg_confirm(current_user.id):
        return redirect('/confirm_email')
    with models.create_session() as session:
        if current_user.role_id != 2:
            return abort(403, description="Эта функция доступна только библиотекарю")
        ed = session.query(Edition).get(id)
        if not ed:
            return abort(404, description="Неизвестная книга")
        if ed.library_id != current_user.library_id:
            abort(403, description="Это издание относится к другой библиотеке")
        session.delete(ed)
        session.commit()
        return redirect('/library/editions')


@log_dec
@login_required
@lb.route('/borrow_book/<string:code>', methods=["GET", "POST"])
def borrow_book(code):
    if not check_reg_confirm(current_user.id):
        return redirect('/confirm_email')
    with models.create_session() as session:
        for i in session.query(Book).all():
            if i.check_id(code):
                cur_book = i
                break
        else:
            return abort(404, description='Неверный идентификатор книги')  # Шаблон с сообщением в центре экрана
        form = BorrowBookForm()
        if form.validate_on_submit():
            lend_book(current_user.id, cur_book.id)
            return redirect('/library/')

        if not current_user.is_authenticated or current_user.libray_id != cur_book.edition.library_id:
            background = 'red'
            msg = f'Эта книга из: {cur_book.edition.library.school_name}'
            show_form = False
        elif cur_book.owner:
            background = 'red'
            msg = f'Эта книга принадлежит: {cur_book.owner.surname} {cur_book.owner.name}'
            show_form = False
        else:
            background = 'green'
            msg = f'Эта книга свободна'
            show_form = True
        return render_template('borrow_book.html',
                               msg=msg,
                               background=background,
                               cur_book=cur_book,
                               current_user=current_user,
                               show_form=show_form)


@log_dec
@login_required
@lb.route('/delete_book/<int:id>')
def delete_book(id):
    if not check_reg_confirm(current_user.id):
        return redirect('/confirm_email')
    with models.create_session() as session:
        if current_user.role_id != 2:
            return abort(403, description="Эта функция доступна только библиотекарю")
        book = session.query(Book).get(id)
        if not book:
            return abort(404, description="Неизвестная книга")
        if book.edition.library_id != current_user.library_id:
            abort(403, description="Это издание относится к другой библиотеке")
        delete_book(id)
        return redirect('/library/books')


@log_dec
@login_required
@lb.route('/add_book/<int:edition_id>')
def add_book_(edition_id):
    if not check_reg_confirm(current_user.id):
        return redirect('/confirm_email')
    with models.create_session() as session:
        if current_user.role_id == 2:
            ed = session.query(Edition).get(edition_id)
            if ed:
                if ed.library_id == current_user.library_id:
                    session.add(Book(edition_id=ed.id))
                    session.commit()
                else:
                    abort(403, description="Эта книга относится к другой библиотеке")
            else:
                abort(404, description="Издание не найдено")
        return redirect(f'/library/editions/{edition_id}')


@log_dec
@login_required
@lb.route('/give_book/<int:book_id>', methods=['GET', 'POST'])
def give_book(book_id):
    if not check_reg_confirm(current_user.id):
        return redirect('/confirm_email')
    with models.create_session() as session:
        book = session.query(Book).get(book_id)
        if not book:
            return abort(404, description="Неизвестная книга")
        if current_user.role_id != 2:
            return abort(403, description="Данная функция доступна только библиотекарю")
        if book.edition.library_id != current_user.library_id:
            return abort(403, description="Эта книга не из вашей библиотеки")
        students = session.query(User).filter(User.role_id == 1, User.library_id == current_user.library_id).all()
        form = give_book_form(students)
        if form.validate_on_submit():
            st_id = form.select_student.data
            book.owner_id = st_id
            session.commit()
            session.close()
            return redirect('/library')
        return render_template('give_book.html', form=form, book=book)


@log_dec
@login_required
@lb.route('/return_book/<int:book_id>')
def return_book(book_id):
    if not check_reg_confirm(current_user.id):
        return redirect('/confirm_email')
    with models.create_session() as session:
        if current_user.role_id != 2:
            return abort(403, description="Данная функция доступна лишь библиотекарю")
        book = session.query(Book).get(book_id)
        if not book:
            return abort(404, description="Такой книги нет в библиотеке")
        if current_user.library_id != book.edition.library_id:
            return abort(403, description="Эта книга находится не в вашей библиотеке")
        book.owner_id = None
        session.commit()
        session.close()
        return redirect('/library')


@log_dec
@login_required
@lb.route('/delete_student/<int:student_id>')
def delete_student(student_id):
    if not check_reg_confirm(current_user.id):
        return redirect('/confirm_email')
    with models.create_session() as session:
        if current_user.role_id != 2:
            return abort(403, description='Эта функция достурна лишь библиотекарю')
        student = session.query(User).get(student_id)
        if not student:
            return abort(404, description='Пользователь не найден')
        if student.role_id != 1 or student.library_id != current_user.library_id:
            return abort(403, description='Такого ученика нет в вашей библиотеке')
        student.role_id = 3
        student.library_id = None
        session.commit()
        return redirect('/library/students')


@log_dec
@lb.route('/editions/create', methods=['GET', 'POST'])
@login_required
def create_edition_route():
    if not check_reg_confirm(current_user.id):
        return redirect('/confirm_email')
    with models.create_session() as session:
        librarian_role = session.query(Role).filter(Role.name == 'Librarian').first().id
        if current_user.role_id != librarian_role:
            return redirect('/library')
        form = CreateEditionForm()
        if form.validate_on_submit():
            edition = create_edition(form.name.data, form.author.data,
                                     form.publication_year.data, current_user.library_id)
            session.add(edition)
            edition_id = get_id_of_last_edition() + 1

            for i in range(form.book_counts.data):
                session.add(create_book(edition_id))
            session.commit()
            return redirect(f'/library/editions/{edition.id}')
        return render_template('create_edition_form.html', form=form, url_for=url_for)


@log_dec
@lb.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if not check_reg_confirm(current_user.id):
        return redirect('/confirm_email')
    with models.create_session() as session:
        librarian_role = session.query(Role).filter(Role.name == 'Librarian').first().id
        user = session.query(User).get(current_user.id)
        library = session.query(Library).get(current_user.library_id)
        if current_user.role_id == librarian_role:
            library_form = edit_library(
                **{'name': user.name,
                   'surname': user.surname,
                   'students_join_possibility': library.opened,
                   'library_school_name': library.school_name}
            )
            if library_form.validate_on_submit():
                if library_form.library_school_name.data:
                    library.school_name = library_form.library_school_name.data
                library.opened = bool(library_form.students_join_possibility.data)
                if library_form.name.data:
                    user.name = library_form.name.data
                if library_form.surname.data:
                    user.surname = library_form.surname.data
                session.commit()
            library_code = session.query(Library).get(current_user.library_id).generate_id()
            return render_template('library_edit.html', form=library_form, current_user=current_user,
                                   library_code=library_code)
        else:
            student_form = edit_student_profile_form(name=current_user.name, surname=current_user.surname)
            if student_form.validate_on_submit():
                if student_form.name.data:
                    user.name = student_form.name.data
                if student_form.surname.data:
                    user.surname = student_form.surname.data
                session.commit()
            return render_template('library_edit.html', form=student_form, current_user=current_user,
                                   library_code='')


@log_dec
@lb.route('/profile/<int:student_id>')
@login_required
def student_profile(student_id):
    if not check_reg_confirm(current_user.id):
        return redirect('/confirm_email')
    with models.create_session() as session:
        student_role = session.query(Role).filter(Role.name == 'Student').first()
        librarian_role = session.query(Role).filter(Role.name == 'Librarian').first()
        student = session.query(User).get(student_id)
        if not student:
            return abort(404, description='Такого ученика нет')
        if student.role_id != librarian_role.id:
            return redirect('/library')
        if current_user.role_id == student_role.id:
            return abort(403, description='Сюда можно только библиотекарю')
        if current_user.library_id != session.query(User).get(student_id).library_id:
            return abort(403, description='Пользователь не в вашей библиотеке')
        books = session.query(Book).filter(Book.owner_id == student_id).all()
        return render_template('profile-st.html', books=books, user=current_user)


@log_dec
@lb.route('/add_edition_photo/<int:edition_id>', methods=['GET', 'POST'])
@login_required
def add_edition_photo(edition_id):
    with models.create_session() as session:
        lib_role_id = session.query(Role).filter(Role.name == 'Librarian').first().id
        if current_user.role_id != lib_role_id:
            return redirect('/library/editions')
        ed = session.query(Edition).get(edition_id)
        if not ed:
            return redirect('/library/editions')
        if ed.library_id != current_user.library_id:
            return redirect('/library/editions')
        form = AddEditionImageForm()
        if form.validate_on_submit():
            file = request.files['photo']
            if not allowed_image_file(file.filename):
                return render_template('add_edition_image.html', form=form, msg='Неподдерживаемый формат')
            filename = generate_name_for_edition_name(file.filename.split('.')[1])
            with open(f'libby/static/img/{filename}', 'wb') as w_file:
                file.save(w_file)
            ed.photo_path = filename
            session.commit()
            return redirect(f'/library/editions/{edition_id}')
        return render_template('add_edition_image.html', form=form)


@log_dec
@lb.route('/my_books')
@login_required
def my_books():
    with models.create_session() as session:
        st_role = session.query(Role).filter(Role.name == 'Student').first().id
        if current_user.role_id != st_role:
            return redirect('/library/editions')
        return render_template('my_books.html', url_for=url_for)


app.register_blueprint(lb, url_prefix='/library')
