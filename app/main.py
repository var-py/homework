from flask import Flask, redirect, render_template, request, url_for
from sqlalchemy import insert, select
from sqlalchemy.orm import Session

from app.DB.models import UserAction
from app.DB.session import engine

app = Flask(__name__)


def Delete_fromDB(id):
    with Session(engine) as session:
        stmt = select(UserAction).where(UserAction.id == id)
        delete = session.scalar(stmt)

        if delete:
            session.delete(delete)
            session.commit()


@app.route("/")
def home():
    return "привет-привет"


@app.route("/healthz")
def healthz():
    """Health-check endpoint: используется Docker HEALTHCHECK и CI/CD."""
    return {"status": "ok"}


@app.route("/helloorbye", methods=["GET", "POST"])
def helloorbye():
    result_message = ""
    if request.method == "POST":
        choice = request.form.get("user_choice", "").lower()

        if choice == "привет":
            result_message = "Привет!"
        elif choice == "пока":
            result_message = "Пока!️"
    with Session(engine) as session:
        if result_message != "":
            stmt = insert(UserAction).values(choice=result_message)
            session.execute(stmt)
            session.commit()
    return render_template("lo.html", message=result_message)


@app.route("/dashboard")
def dashboard():
    with Session(engine) as session:
        stmt = select(UserAction).order_by(UserAction.id)
        actions = session.scalars(stmt).all()

    return render_template("dashboard.html", actions=actions)


@app.route("/delete/<int:id>", methods=["POST"])
def delete_action(id):
    Delete_fromDB(id)
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)
