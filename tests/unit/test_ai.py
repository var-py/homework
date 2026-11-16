import pytest

import app.ai_agent as ai_agent
import app.main as main_module
from app.ai_agent import AgentError


def test_ai_page_has_form(client):
    response = client.get("/ai")

    assert response.status_code == 200
    assert 'name="question"' in response.get_data(as_text=True)


def test_ai_page_shows_answer(client, monkeypatch):
    monkeypatch.setattr(main_module, "ask", lambda question: f"Ответ на: {question}")

    response = client.post("/ai", data={"question": "Чем опасен яд кобры?"})
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Ответ на: Чем опасен яд кобры?" in html
    assert 'name="question"' in html


def test_ai_page_shows_error_without_key(client, monkeypatch):
    def boom(question):
        raise AgentError("DEEPSEEK_API_KEY не задан.")

    monkeypatch.setattr(main_module, "ask", boom)

    response = client.post("/ai", data={"question": "Кто ты?"})
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Ошибка" in html
    assert "DEEPSEEK_API_KEY" in html


def test_ai_page_skips_empty_question(client, monkeypatch):
    def fail(question):
        raise AssertionError("ask() не должен вызываться для пустого запроса")

    monkeypatch.setattr(main_module, "ask", fail)

    response = client.post("/ai", data={"question": "   "})

    assert response.status_code == 200


def test_ask_requires_api_key(monkeypatch):
    monkeypatch.setattr(ai_agent, "DEEPSEEK_API_KEY", "")

    with pytest.raises(AgentError, match="DEEPSEEK_API_KEY"):
        ai_agent.ask("Кто ты?")


def test_ask_rejects_empty_question(monkeypatch):
    monkeypatch.setattr(ai_agent, "DEEPSEEK_API_KEY", "test-key")

    with pytest.raises(AgentError):
        ai_agent.ask("   ")
