from libby import login_manager
import models
from models.__all_models import User


if login_manager:
    @login_manager.user_loader
    def load_user(user_id):
        with models.create_session() as session:
            return session.query(User).get(user_id)