from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from .. import settings


engine = create_engine(settings.DB_URI)

session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)


def create_all(engine=engine):
    # create the tables if they don't yet exist
    Base.metadata.create_all(engine)
    # then load the Alembic configuration and generate the
    # version table, "stamping" it with the most recent rev
    alembic_cfg = Config(settings.ALEMBIC_INI_PATH)
    alembic_cfg.set_main_option('script_location',
                                settings.ALEMBIC_SCRIPT_LOCATION)
    command.stamp(alembic_cfg, "head")


def get_session():
    return(Session())

