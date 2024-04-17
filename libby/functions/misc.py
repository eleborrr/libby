from wtforms import ValidationError


def check_email_domen(form, content):
    if content.data.split('@')[1] != 'edu.tatar.ru':
        raise ValidationError('Почта должна относиться к edu.tatar.ru')


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