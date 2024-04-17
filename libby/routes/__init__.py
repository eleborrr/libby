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


from libby.routes.library_bp import *
from libby.routes.no_bp import *
from libby import app