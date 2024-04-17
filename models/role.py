from models import SqlAlchemyBase
from sqlalchemy import Column as Cl
import sqlalchemy as sql


class Role(SqlAlchemyBase):
    __tablename__ = 'roles'
    id = Cl(sql.Integer, autoincrement=True, primary_key=True, nullable=False)
    name = Cl(sql.String(32))
