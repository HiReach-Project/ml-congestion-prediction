from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String

Base = declarative_base()


class Company(Base):
    __tablename__ = 'company'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    access_key = Column(String)

    def __repr__(self):
        return "<Company(name='{}', access_key='{}')>" \
            .format(self.name, self.access_key)
