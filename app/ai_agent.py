"""ИИ-агент — эксперт по аспидовым змеям (DeepSeek API).

Ключ DeepSeek берётся из отдельной переменной DEEPSEEK_API_KEY
(файл .env или переменная окружения).
"""

import json
import os
import urllib.error
import urllib.request

from dotenv import dotenv_values

# Ключ DeepSeek — в отдельной переменной, в коде его дублировать не нужно.
DEEPSEEK_API_KEY = (os.getenv("DEEPSEEK_API_KEY") or dotenv_values(".env").get("DEEPSEEK_API_KEY") or "").strip()

API_URL = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-chat"
TIMEOUT = 60

WIKI_URL = "https://ru.wikipedia.org/wiki/Аспидовые_змеи"

SYSTEM_PROMPT = f"""Ты — эксперт-герпетолог по аспидовым змеям (семейство Elapidae):
кобры, крайты, мамбы, тайпаны, тигровые и чёрные змеи, австралийские,
коралловые и морские змеи.

Опирайся на статью Википедии «Аспидовые змеи»: {WIKI_URL}

Ты знаешь:
- систематику (роды Naja, Ophiophagus, Bungarus, Dendroaspis, Oxyuranus,
  Notechis, Pseudechis, Micrurus, Pseudonaja и др.) и ареалы;
- ядовитый аппарат: неподвижные передние (proteroglyphous) зубы;
- состав яда: постсинаптические нейротоксины, цитотоксины, миотоксины;
- клиническую картину укусов, первую помощь и антидотную терапию;
- питание, размножение, содержание в террариуме и профилактику укусов.

Отвечай по-русски: сначала короткий ответ, затем детали. Латинские названия
давай при первом упоминании. Если вопрос не по теме или данных нет — скажи
прямо. Ты не врач: при разговоре об укусах всегда напоминай о срочной
госпитализации и не заменяй консультацию специалиста."""


class AgentError(RuntimeError):
    """Ошибка обращения к DeepSeek API."""


def ask(question: str) -> str:
    """Задать вопрос агенту и вернуть ответ модели."""
    question = (question or "").strip()
    if not question:
        raise AgentError("Пустой запрос отправлять нечего.")
    if not DEEPSEEK_API_KEY:
        raise AgentError(
            "DEEPSEEK_API_KEY не задан. Добавьте его в .env (см. .env.example) "
            "или экспортируйте переменную окружения DEEPSEEK_API_KEY."
        )

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
        "stream": False,
    }
    request = urllib.request.Request(
        API_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:300]
        raise AgentError(f"DeepSeek API вернул HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise AgentError(f"Не удалось подключиться к DeepSeek: {exc.reason}") from exc
    except TimeoutError as exc:
        raise AgentError(f"DeepSeek не ответил за {TIMEOUT} с.") from exc

    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise AgentError(f"Неожиданный ответ DeepSeek API: {data!r}") from exc
