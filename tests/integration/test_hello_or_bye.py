from sqlalchemy import select
from sqlalchemy.orm import Session

from app.DB.models import UserAction
from app.main import engine


def test_hello_or_bye_responses(client):
    res_hello = client.post("/helloorbye", data={"user_choice": "привет"})
    assert res_hello.status_code == 200
    assert "Привет!" in res_hello.get_data(as_text=True)

    res_bye = client.post("/helloorbye", data={"user_choice": "пока"})
    assert res_bye.status_code == 200
    assert "Пока!" in res_bye.get_data(as_text=True)


def test_create_and_delete(client):
    res = client.post("/helloorbye", data={"user_choice": "привет"})
    assert res.status_code == 200
    assert "Привет!" in res.get_data(as_text=True)

    with Session(engine) as session:
        stmt = select(UserAction).where(UserAction.choice == "Привет!").order_by(UserAction.id.desc())
        created = session.scalar(stmt)
        assert created is not None
        action_id = created.id

    del_res = client.post(f"/delete/{action_id}")
    assert del_res.status_code == 302

    with Session(engine) as session:
        assert session.get(UserAction, action_id) is None