import sqlalchemy as db
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column

Base = declarative_base()


class UsersMapped(Base):
    __tablename__ = 'users'

    id = Column('id', db.BIGINT, primary_key=True)
    user_name = Column('user_name', db.String(255))
    user_password = Column('user_password', db.String(255))
    user_status = Column('status', db.INT)

