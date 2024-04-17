from libby.functions import *
from libby.routes import log_dec
from libby import app
from libby.forms import *
from flask import render_template, redirect, url_for, request, jsonify
from flask_login import current_user, login_user, logout_user, login_required
import models

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
            user_id = register_student(register_form.email1.data, register_form.surname1.data, register_form.name1.data,
                                       register_form.password1.data, None)
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


@log_dec
@app.route('/test_send_messages')
@login_required
def test_send_messages():
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
        return render_template('email_confirmed.html')
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
        if page == 9:
            print()
        if not current_user.library_id:
            return jsonify({})
        if mode == TARGET_BOOK:
            f = get_page_of_books
            res = f(page, {**dict(request.args), 'session': session, 'library_id': current_user.library_id})
        elif mode == TARGET_EDITION:
            f = get_page_of_editions
            res = f(page, {**dict(request.args), 'session': session, 'library_id': current_user.library_id})
        elif mode == TARGET_STUDENT:
            lib_role_id = get_role_id(Librarian)
            if current_user.role_id != lib_role_id:
                return jsonify({})
            f = get_page_of_students
            res = f(page, {**dict(request.args), 'session': session, 'library_id': current_user.library_id})

        elif mode == TARGET_WAITING_STUDENTS:
            lib_role_id = get_role_id(Librarian)
            if current_user.role_id != lib_role_id:
                return jsonify({})
            f = get_page_of_waits
            res = f(page, {**dict(request.args), 'session': session, 'library_id': current_user.library_id})
        else:
            return abort(404, description='mode should be 1, 2 or 3')
        dict_res = {
            'els': [
            ]
        }

        for i in (res):
            dict_res['els'].append(i.to_dict())
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
