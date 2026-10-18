from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column


class Base(DeclarativeBase):
    pass


class UserAction(Base):
    __tablename__ = "user_actions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    choice: Mapped[str] = mapped_column(nullable=False)

    def __repr__(self) -> str:
        return f"<UserAction(id={self.id}, choice='{self.choice}')>"
