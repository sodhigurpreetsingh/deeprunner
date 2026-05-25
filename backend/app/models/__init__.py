"""Database models"""

from app.core.database import Base
from app.models.tenant import Tenant
from app.models.document import Document

__all__ = ['Base', 'Tenant', 'Document']
