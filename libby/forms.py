from flask_wtf import FlaskForm
from wtforms import StringField as sf, PasswordField as pf, SubmitField, BooleanField, IntegerField, SelectField, FileField
from wtforms.fields.html5 import EmailField as ef
from wtforms.validators import DataRequired, Length, EqualTo, NumberRange
from libby.functions import check_email_domen


class ValidatorsMixin:
    def __init__(self):
        for i in self.validators:
            if isinstance(i, DataRequired):
                i.message = f'Поле "{self.label.text}" должно быть заполнено'
            elif isinstance(i, EqualTo):
                i.message = f'Пароли не совпадают'
            elif isinstance(i, Length):
                i.message = f'Длина содержимого должна быть от {i.min} до {i.max}'


class StringField(sf, ValidatorsMixin):
    def __init__(self, *args, **kwargs):
        sf.__init__(self, *args, **kwargs)
        ValidatorsMixin.__init__(self)


class EmailField(ef, ValidatorsMixin):
    def __init__(self, *args, **kwargs):
        ef.__init__(self, *args, **kwargs)
        ValidatorsMixin.__init__(self)


class PasswordField(pf, ValidatorsMixin):
    def __init__(self, *args, **kwargs):
        pf.__init__(self, *args, **kwargs)
        ValidatorsMixin.__init__(self)


class OptionalIntegerField(IntegerField):
    def process_data(self, value):
        if not value:
            value = None
        IntegerField.process_data(self, value)

    def process_formdata(self, valuelist):
        if valuelist:
            try:
                self.data = int(valuelist[0])
            except ValueError:
                self.data = None
                if valuelist[0]:
                    raise ValueError(self.gettext('Неверное целочисленное значение'))


class CreateLibraryForm(FlaskForm):  # Создает пользователя-библиотекаря и библиотеку
    name = StringField('Имя', validators=[DataRequired(), Length(max=32)])
    surname = StringField('Фамилия', validators=[DataRequired(), Length(max=32)])
    email = EmailField('Адрес электронной почты', validators=[DataRequired(), Length(max=64)])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(max=128)])
    repeat = PasswordField('Повторите пароль', validators=[DataRequired(), Length(max=128), EqualTo('password')])
    library_school_name = StringField('Наименование школы (полное)', validators=[DataRequired(), Length(max=64)])
    submit = SubmitField('Зарегистрироваться')


class RegisterStudentForm(FlaskForm):
    name1 = StringField('Имя', validators=[DataRequired(), Length(max=32)])
    surname1 = StringField('Фамилия', validators=[DataRequired(), Length(max=32)])
    class_number = IntegerField('Номер класса', validators=[DataRequired(), NumberRange(1, 11)])
    class_literal = StringField('Литера класса', validators=[DataRequired(), Length(min=1, max=1)])
    email1 = EmailField('Адрес электронной почты', validators=[DataRequired(), Length(max=64)])  #check_email_domen
    password1 = PasswordField('Пароль', validators=[DataRequired(), Length(max=128)])
    repeat1 = PasswordField('Повторите пароль', validators=[DataRequired(), Length(max=128), EqualTo('password1')])
    submit1 = SubmitField('Зарегистрироваться')


class LoginForm(FlaskForm):
    email2 = EmailField('Адрес электронной почты', validators=[DataRequired()])
    password2 = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit2 = SubmitField('Войти')


def book_filter_form(**kwargs):
    class BookFilterForm(FlaskForm):
        id = OptionalIntegerField('Номер книги', default=kwargs['id_'])
        owner_id = OptionalIntegerField('Номер владельца', default=kwargs['owner_id'])
        owner_surname = StringField('Фамилия владельца', default=kwargs['owner_surname'])
        free = BooleanField('Только свободные книги', default=kwargs['free'])
        submit = SubmitField('Искать')

    return BookFilterForm()


def student_filter_form(**kwargs):
    class StudentFilterForm(FlaskForm):
        id_ = OptionalIntegerField('Номер ученика', default=kwargs['id_'])
        surname = StringField('Фамилия ученика', default=kwargs['surname'])
        class_num = OptionalIntegerField('Номер класса ученика', default=kwargs['class_num'])
        class_letter = StringField('Литера класса ученика', default=kwargs['class_letter'])
        submit = SubmitField('Искать')

    return StudentFilterForm()


def give_book_form(students):
    class GiveBookForm(FlaskForm):
        select_student = SelectField("Выберите, кому дать эту книгу",
                                     choices=[(str(st.id), st.surname + ' ' + st.name) for st in students])
        submit = SubmitField("Отправить")

    return GiveBookForm()


class CreateEditionForm(FlaskForm):
    name = StringField("Название книги", validators=[DataRequired()])
    author = StringField("Фамилия автора", validators=[DataRequired()])
    publication_year = IntegerField("Год публикации", validators=[DataRequired()])
    book_counts = IntegerField("Количество книг", validators=[DataRequired()])
    submit = SubmitField("Создать")


class BorrowBookForm(FlaskForm):
    submit = SubmitField('Взять книгу')


def edit_library(**kwargs):
    class EditLibrary(FlaskForm):
        name = StringField('Имя', validators=[DataRequired(), Length(max=32)], default=kwargs.get('name'))
        surname = StringField('Фамилия', validators=[DataRequired(), Length(max=32)], default=kwargs.get('surname'))
        students_join_possibility = BooleanField('Разрешить регистрацию',
                                                 default=kwargs.get('students_join_possibility'))
        library_school_name = StringField('Наименование школы (полное)', validators=[DataRequired(), Length(max=64)],
                                          default=kwargs.get('library_school_name'))
        submit = SubmitField('Сохранить')

    return EditLibrary()


def edit_student_profile_form(**kwargs):
    class EditStudentProfileForm(FlaskForm):
        name = StringField('Ваше имя', default=kwargs['name'])
        surname = StringField('Ваша фамилия', default=kwargs['surname'])
        submit = SubmitField('Изменить')

    return EditStudentProfileForm()


class ChangePasswordForm(FlaskForm):
    new_password = PasswordField('Новый пароль', validators=[DataRequired(), Length(max=128)])
    confirm_new_password = PasswordField('Повторите пароль', validators=[EqualTo('new_password')])
    submit = SubmitField('Сменить пароль')


def edition_filter_form(**kwargs):
    class EditionFilterForm(FlaskForm):
        id_ = OptionalIntegerField('Идентификатор книги', default=kwargs['id_'])
        name = StringField('Имя книги', default=kwargs['name'])
        author = StringField('Автор книги', default=kwargs['author'])
        publication_year = OptionalIntegerField('Год издания', default=kwargs['publication_year'])
        submit = SubmitField('Поиск')

    return EditionFilterForm()


class AddEditionImageForm(FlaskForm):
    photo = FileField("Загрузить фотографию", validators=[DataRequired()])
    submit = SubmitField("Подтвердить")
