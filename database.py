from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine('postgres+psycopg2://postgres:postgres@localhost:5432/ml_prediction')

db_session = scoped_session(sessionmaker(bind=engine))
