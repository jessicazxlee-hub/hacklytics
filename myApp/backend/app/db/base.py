from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Import all models here so Alembic autogenerate can discover metadata.
from app.models import restaurant, user  # noqa: F401,E402
