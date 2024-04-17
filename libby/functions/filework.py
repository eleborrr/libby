import uuid


def generate_name_for_edition_name(mod):
    return str(uuid.uuid4()) + '.' + mod


def allowed_image_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ['jpg', 'jpeg', 'png', 'webp', 'gif', 'svg']