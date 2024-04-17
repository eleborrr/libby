from models import SqlAlchemyBase
from sqlalchemy import Column as Cl
from sqlalchemy import ForeignKey
from sqlalchemy import orm
import sqlalchemy as sql
from flask import url_for


class Edition(SqlAlchemyBase):
    __tablename__ = 'editions'
    id = Cl(sql.Integer, autoincrement=True, primary_key=True, nullable=False)
    name = Cl(sql.String(64), nullable=False)
    author = Cl(sql.String(64), nullable=False)
    publication_year = Cl(sql.Integer, nullable=False)
    library_id = Cl(sql.Integer, ForeignKey('libraries.id', ondelete='CASCADE'), nullable=False)
    library = orm.relation('Library')
    books = orm.relation('Book', back_populates='edition', cascade='all,delete')

    def to_dict(self):
        return {
            'id_': self.id,
            'name': self.name,
            'author': self.author,
            'publication_year': self.publication_year,
        }
