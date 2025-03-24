from flask import current_app
from sqlalchemy.orm import scoped_session, sessionmaker
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

@contextmanager
def get_scoped_session():
    """
    Context manager para fornecer uma sessão isolada do SQLAlchemy por thread.
    
    Uso:
        with get_scoped_session() as session:
            result = session.query(Model).all()
            session.commit()  # Commit automático se não houver exceção
    """
    from app import db
    Session = scoped_session(sessionmaker(bind=db.engine))
    session = Session()
    try:
        yield session
        session.commit()
        logger.debug("Sessão do banco de dados comitada com sucesso")
    except Exception as e:
        session.rollback()
        logger.error(f"Erro na sessão do banco de dados: {str(e)}")
        raise
    finally:
        Session.remove()
        logger.debug("Sessão do banco de dados removida")
