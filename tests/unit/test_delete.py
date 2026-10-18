from sqlalchemy.orm import Session

from app.DB.models import UserAction
from app.main import Delete_fromDB, engine


def test_delete_from_db():
    with Session(engine) as session:
        action = UserAction(choice="тест")
        session.add(action)
        session.commit()
        action_id = action.id

    Delete_fromDB(action_id)

    with Session(engine) as session:
        assert session.get(UserAction, action_id) is None