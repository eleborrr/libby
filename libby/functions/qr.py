import models
from models.__all_models import Edition
from libby.qr_generators import _create_qr_list


def generate_edition_qr(edition_id, url='localhost:5000'):
    with models.create_session() as session:
        res = _create_qr_list([(x.generate_id(), x.id) for x in session.query(Edition).get(edition_id).books], url)[0]
        return res
