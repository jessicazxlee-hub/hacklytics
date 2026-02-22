from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Import all models here so Alembic autogenerate can discover metadata.
from app.models import group_chat, group_match, hobby, restaurant, social, user  # noqa: F401,E402
