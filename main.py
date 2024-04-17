import os
import libby
import click
try:
    import pretty_errors
except ImportError:
    pass


class ProductionConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SECURITY_PASSWORD_SALT = os.urandom(32)
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_USE_TLS = True  # Changeable
    MAIL_PORT = os.environ.get('MAIL_PORT')
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER')
    DEBUG = False
    db_file = None  # Change for prod
    port = os.environ.get('port')
    host = '0.0.0.0'


class DevelopmentConfig:
    SECRET_KEY = 'TestSecretKey'
    SECURITY_PASSWORD_SALT = os.urandom(32)
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_USE_TLS = True
    MAIL_PORT = 587
    MAIL_USERNAME = 'testing.some.web.apps@gmail.com'
    MAIL_PASSWORD = 'QWSDCFDRFGgftgbhTTGBGTG2132&'
    MAIL_DEFAULT_SENDER = 'Mr Test'
    UPLOAD_FOLDER = 'static/img'
    DEBUG = True
    db_file = 'sqlite:///db/libby.sqlite?check_same_thread=False'
    port = 5000
    host = '127.0.0.1'


# mod = None
# if len(sys.argv) == 1:
#     mod = DevelopmentConfig
# elif len(sys.argv) > 2:
#     raise ValueError('only one argument should be given')
# elif sys.argv[1] == 'dev':
#     mod = DevelopmentConfig
# elif sys.argv[1] == 'prod':
#     mod = ProductionConfig
# else:
#     raise ValueError('argument should be dev or prod')
#
# libby.init_app(mod)
# libby.run(port=mod.port, host=mod.host)


@click.command()
@click.option('--mod', '-m',
              help='Режим запуска. dev для разработки, prod для промышленного запуска. По умолчанию dev')
@click.option('--url', '-u',
              help='Домен, на котором будет запускаться сайт (нужен для qr-кодов). По умолчанию localhost:5000')
def main(mod, url):
    """Команда запуска сервера"""
    if mod == 'prod':
        config = ProductionConfig
    elif mod in ['dev', None]:
        config = DevelopmentConfig
    else:
        raise ValueError('mod should be dev or prod')
    libby.init_app(config, url)
    libby.run(host=config.host, port=config.port)


if __name__ == '__main__':
    main()
