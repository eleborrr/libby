from libby import url
from flask import render_template, redirect, url_for, request, Blueprint, jsonify
from libby.functions import *
from libby.qr_generators import *
from flask_login import current_user, login_user, logout_user, login_required
from libby.forms import *
import models


def log_dec(func):
    def new_func(*args, **kwargs):
        try:
            res = func(*args, **kwargs)
        except Exception as er:
            app.logger.error(str(er.__class__) + ':' + ', '.join(er.args) + f'in {func.__name__}')
            raise er
        else:
            app.logger.info(f'success in {func.__name__}')
            return res

    return new_func


app.before_first_request(create_roles)


@log_dec
@app.route('/')
def index():
    app.logger.debug('debug message')
    return render_template('index.html', url_for=url_for)


@log_dec
@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')


@log_dec
@app.route('/sign_in', methods=['GET', 'POST'])
def sign_in():
    if current_user.is_authenticated:
        return redirect('/library/editions')
    with models.create_session() as session:
        library_form = CreateLibraryForm()
        login_form = LoginForm()
        register_form = RegisterStudentForm()

        # Обработка формы 1
        if library_form.validate_on_submit():
            ex = session.query(User).filter(User.login == library_form.email.data).first()
            if ex:
                return render_template('tabs-page.html',
                                       library_form=library_form,
                                       register_form=register_form,
                                       login_form=login_form,
                                       tab_num=1,
                                       msg1="Этот адрес электронной почты уже занят",
                                       url_for=url_for)
            register_library(library_form.library_school_name.data,
                             login=library_form.email.data,
                             name=library_form.name.data,
                             surname=library_form.surname.data,
                             password=library_form.password.data)
            return redirect('/sign_up#tab_03')

        # Обработка формы 2
        if register_form.validate_on_submit():
            ex = session.query(User).filter(User.login == register_form.email1.data).first()
            if ex:
                return render_template('tabs-page.html',
                                       library_form=library_form, register_form=register_form,
                                       login_form=login_form,
                                       tab_num=2,
                                       msg2="Этот адрес электронной почты уже занят",
                                       url_for=url_for)
            libraries = session.query(Library).all()
            for i in libraries:
                if i.generate_id() == register_form.library_id.data:
                    if not i.opened:
                        return render_template('tabs-page.html',
                                               library_form=library_form, register_form=register_form,
                                               login_form=login_form,
                                               tab_num=2,
                                               msg2="Библиотека закрыта для регистрации",
                                               url_for=url_for)
                    library_id = i.id
                    break
            else:
                return render_template('tabs-page.html',
                                       library_form=library_form,
                                       register_form=register_form,
                                       login_form=login_form,
                                       tab_num=2,
                                       msg2='Неверный идентификатор библиотеки',
                                       url_for=url_for)
            user_id = register_student(register_form.email1.data, register_form.surname1.data, register_form.name1.data,
                             register_form.password1.data, library_id)
            login_user(session.query(User).get(user_id))
            return redirect('/sign_up#tab_03')

        # Обработка формы 3
        if login_form.validate_on_submit():
            us = session.query(User).filter(User.login == login_form.email2.data).first()
            if not us:
                return render_template('tabs-page.html',
                                       library_form=library_form,
                                       register_form=register_form,
                                       login_form=login_form,
                                       tab_num=3,
                                       msg3="Неверный адрес электронной почты",
                                       url_for=url_for)
            if not us.check_password(login_form.password2.data):
                return render_template('tabs-page.html',
                                       library_form=library_form,
                                       register_form=register_form,
                                       login_form=login_form,
                                       tab_num=3,
                                       msg3="Неверный пароль",
                                       url_for=url_for)
            login_user(us, remember=login_form.remember_me.data)
            return redirect('/library/editions')

        # get
        return render_template('tabs-page.html',
                               library_form=library_form,
                               register_form=register_form,
                               login_form=login_form,
                               tab_num=3,
                               url_for=url_for)


@log_dec
@app.route('/sign_up')
def sign_up():
    return redirect('/sign_in')


lb = Blueprint('library', __name__)



@log_dec
@lb.route('/editions', methods=['GET', 'POST'], strict_slashes=False)
@login_required
def editions():
    if not check_reg_confirm(current_user.id):
        return redirect('/confirm_email')
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
                               url_for=url_for)


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
                               url_for=url_for, current_user=current_user)


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
        return render_template('students.html', students=new_res, form=form, library_code=library_code)


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
@app.route('/test_send_messages')
@login_required
def test_send_messages():
    print(app.debug)
    if app.debug:
        send_email(current_user, CONFIRM_EMAIL)
        send_email(current_user, CHANGE_PASSWORD)
    return redirect('/')


@log_dec
@app.route('/confirm_email')
@login_required
def confirm_email_message():
    if current_user.confirmed:
        return redirect('/library')
    send_email(current_user, CONFIRM_EMAIL)
    return render_template('confirm_email_message.html', current_user=current_user)


@log_dec
@app.route('/confirm_email/<string:token>')
def confirm_email(token):
    with models.create_session() as session:
        user = get_user_by_token(token, session, app.config['SECRET_KEY'])
        if not user:
            return 'Токен не действителен'
        user.confirmed = True
        session.commit()
        return redirect('/library')
    # return 'Адрес электронной почты был подтвержден'


@log_dec
@app.route('/change_password/<string:token>', methods=['GET', 'POST'])
def change_password(token):
    with models.create_session() as session:
        user = get_user_by_token(token, session, app.config['SECRET_KEY'])
        if not user:
            return 'Токен не действителен'  # И это тоже
        form = ChangePasswordForm()
        if form.validate_on_submit():
            user.set_password(form.new_password.data)
            session.commit()
            return 'Пароль был изменён'  # Изменить
        return render_template('change_password.html', form=form)


@log_dec
@app.route('/change_password')
@login_required
def change_password_message():
    send_email(current_user, CHANGE_PASSWORD)
    return render_template('change_password_message.html')


@log_dec
@app.route('/get_page_of/<int:mode>/<int:page>')
@login_required
def page_of(mode, page):
    with models.create_session() as session:

        if mode == TARGET_BOOK:
            f = get_page_of_books
            res = f(page, {**dict(request.args), 'session': session, 'library_id': current_user.library_id})
            dict_res = {
                'els': [
                ]
            }

            for i in res:
                dict_res['els'].append(i.to_dict())

        elif mode == TARGET_EDITION:
            f = get_page_of_editions
            res = f(page, {**dict(request.args), 'session': session, 'library_id': current_user.library_id})
            dict_res = {
                'els': [
                ]
            }
            for i in res:
                dict_res['els'].append(i.to_dict())
        elif mode == TARGET_STUDENT:
            f = get_page_of_students
            res = f(page, {**dict(request.args), 'session': session, 'library_id': current_user.library_id})
            dict_res = {
                'els': [
                ]
            }
            for i in res:
                dict_res['els'].append(i.to_dict())
        else:
            return abort(404, description='mode should be 1, 2 or 3')
        print(dict_res)
        return jsonify(dict_res)


@log_dec
@app.route('/cur_us_id')
@login_required
def cur_us_id():
    return jsonify({
        "id": current_user.id
    })


@log_dec
@app.route('/no_image_path')
def no_image_path():
    return jsonify({
        "path": url_for('static', filename='img/no_edition_image.png')
    })


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

# class LibraryView(FlaskView):
#     pass
#
#
# LibraryView.register(app, '/library')
