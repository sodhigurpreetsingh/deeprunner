"""Seed a test tenant"""
import logging
from uuid import UUID
from app.core.database import SyncSessionLocal
from app.models.tenant import Tenant

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_tenant():
    """Create a test tenant"""
    db = SyncSessionLocal()
    try:
        tenant_id = UUID("550e8400-e29b-41d4-a716-446655440000")

        # Check if tenant exists
        existing = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if existing:
            logger.info(f"Tenant {tenant_id} already exists")
            return

        # Create new tenant
        tenant = Tenant(
            id=tenant_id,
            name="test_tenant",
            rate_limit_per_minute=100
        )
        db.add(tenant)
        db.commit()
        logger.info(f"Created test tenant: {tenant_id}")

    except Exception as e:
        logger.error(f"Failed to create tenant: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_tenant()
