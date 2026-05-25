"""Initialize database tables"""
import sys
import logging
from app.core.database import sync_engine, Base
from app.models.tenant import Tenant
from app.models.document import Document

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_db():
    """Create all tables"""
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=sync_engine)
        logger.info("Database tables created successfully!")
        return True
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        return False


if __name__ == "__main__":
    success = init_db()
    sys.exit(0 if success else 1)
