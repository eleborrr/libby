from models import SqlAlchemyBase
from sqlalchemy import Column as Cl
from sqlalchemy import orm
import sqlalchemy as sql
import hashlib


class Library(SqlAlchemyBase):
    __tablename__ = 'libraries'
    id = Cl(sql.Integer, autoincrement=True, primary_key=True, nullable=False)
    school_name = Cl(sql.String(64), nullable=False)
    users = orm.relation('User', back_populates='library')
    editions = orm.relation('Edition', back_populates='library')
    opened = Cl(sql.Boolean, nullable=False, default=True)

    def generate_id(self):
        return hashlib.shake_128(str(self.id).encode()).hexdigest(5)

    def check_id(self, other):
        return other == self.generate_id()
