# homework — Flask + PostgreSQL + CI/CD

[![CI](https://github.com/var-py/homework/actions/workflows/ci.yml/badge.svg)](https://github.com/var-py/homework/actions/workflows/ci.yml)
[![CD](https://github.com/var-py/homework/actions/workflows/cd.yml/badge.svg)](https://github.com/var-py/homework/actions/workflows/cd.yml)

Учебный проект: Flask-приложение с PostgreSQL, упакованное в Docker и собранное
с полным пайплайном CI/CD на GitHub Actions.

## Возможности

| Маршрут | Метод | Назначение |
| --- | --- | --- |
| `/` | GET | приветствие |
| `/helloorbye` | GET/POST | «привет» / «пока», запись действия в БД |
| `/dashboard` | GET | список сохранённых действий |
| `/delete/<id>` | POST | удаление записи |
| `/ai` | GET/POST | ИИ-агент (DeepSeek): вопрос об аспидовых змеях → ответ |
| `/healthz` | GET | health-check (`{"status": "ok"}`) для Docker и CD |

## Структура

```
.
├── app/
│   ├── main.py              # Flask-приложение
│   ├── ai_agent.py          # ИИ-агент DeepSeek: эксперт по аспидовым змеям
│   ├── DB/
│   │   ├── models.py        # SQLAlchemy-модели
│   │   └── session.py       # engine (PostgreSQL в Docker, SQLite в тестах)
│   └── templates/           # lo.html, dashboard.html, ai.html
├── tests/
│   ├── unit/                # изолированные тесты
│   ├── integration/         # тесты через Flask test_client
│   ├── conftest.py
│   └── Dockerfile           # образ для запуска тестов
├── .github/workflows/
│   ├── ci.yml               # линтер + тесты + Docker smoke-тест
│   └── cd.yml               # сборка образа в GHCR + деплой по SSH
├── Dockerfile               # production-образ (gunicorn, non-root)
├── gunicorn.conf.py         # конфигурация gunicorn (preload + post_fork)
├── docker-compose.yml       # локальный стек: web + db
├── docker-compose-test.yml  # запуск pytest в контейнере
├── docker-compose.prod.yml  # production-стек (образ из GHCR)
├── Makefile
├── pyproject.toml           # конфигурация pytest / coverage / ruff
├── requirements.txt
└── requirements-dev.txt
```

## Быстрый старт

```bash
cp .env.example .env          # Windows: copy .env.example .env
make up                       # http://localhost
make down
```

Локально без Docker:

```bash
python -m venv .venv
make install-dev              # pip install -r requirements-dev.txt
make test-local
```

## ИИ-агент (`/ai`)

Страница `/ai` — простой интерфейс к ИИ-агенту, который отвечает как эксперт по
аспидовым змеям (семейство Elapidae). Код агента — `app/ai_agent.py`, страница —
`app/templates/ai.html`.

1. Получите ключ на [platform.deepseek.com/api_keys](https://platform.deepseek.com/api_keys).
2. Впишите его в `.env`:

   ```env
   DEEPSEEK_API_KEY=sk-...
   ```

3. Откройте `/ai`, задайте вопрос и нажмите «Спросить».

Модель — `deepseek-chat`, запросы идут через стандартный `urllib` (новых
зависимостей нет). Знания агента опираются на статью
[«Аспидовые змеи» в Википедии](https://ru.wikipedia.org/wiki/Аспидовые_змеи).
Тесты подменяют вызов API, поэтому ключ и сеть для `pytest` не нужны.

## Тесты

| Команда | Что делает |
| --- | --- |
| `make test-local` | pytest в локальном `.venv` |
| `make test` | pytest в контейнере (`docker-compose-test.yml`) |
| `make test-unit` / `make test-integration` | только unit / только integration |
| `make test-cov` | pytest + coverage в контейнере |
| `make lint` / `make fmt` | `ruff check` / автоисправление + форматирование |
| `make ci` | lint + полный прогон с coverage — то же, что делает CI |

Тесты не требуют PostgreSQL: при запуске под pytest `session.py` автоматически
поднимает in-memory SQLite.

## CI — `.github/workflows/ci.yml`

Запускается на `push` в `master`/`main`, на все `pull_request` и вручную
(`workflow_dispatch`). Параллельные запуски одной ветки отменяются.

| Job | Что проверяет |
| --- | --- |
| **Lint (ruff)** | `ruff check` по правилам из `pyproject.toml` |
| **Tests (unit)** | `pytest tests/unit` |
| **Tests (integration)** | `pytest tests/integration` |
| **Coverage** | полный прогон, `coverage.xml` + `junit.xml` в артефактах |
| **Docker build & smoke test** | `docker compose config` для всех трёх compose-файлов, сборка образов, прогон pytest внутри тестового образа, подъём стека `web + db`, проверка `/`, `/healthz`, `/dashboard`, POST `/helloorbye`; логи печатаются при падении, стек гасится всегда |

## CD — `.github/workflows/cd.yml`

Запускается на `push` в `master`/`main`, на теги `v*.*.*` и вручную.

1. **Build & push image** — сборка `Dockerfile` и публикация в GitHub Container
   Registry: `ghcr.io/var-py/homework`. Теги: ветка, `sha-<short>`, `latest`
   (только для дефолтной ветки), для git-тегов — `1.2.3` и `1.2`.
2. **Deploy to production** — по SSH на сервер: `git pull`, `docker login ghcr.io`,
   `docker compose -f docker-compose.prod.yml pull && up -d`, ожидание статуса
   `healthy` у контейнера, очистка старых образов. Job пропускается, пока не
   включён `DEPLOY_ENABLED`.

### Как включить деплой

1. На сервере (Ubuntu, установлены Docker + compose plugin) один раз:

   ```bash
   git clone https://github.com/var-py/homework.git /opt/homework
   cd /opt/homework && cp .env.example .env   # заполнить пароли
   ```

2. В GitHub → **Settings → Secrets and variables → Actions** добавить:

   | Тип | Имя | Значение |
   | --- | --- | --- |
   | Secret | `DEPLOY_HOST` | IP/домен сервера |
   | Secret | `DEPLOY_USER` | SSH-пользователь |
   | Secret | `DEPLOY_SSH_KEY` | приватный SSH-ключ (без пароля) |
   | Secret | `DEPLOY_PORT` | SSH-порт, необязательно (по умолчанию 22) |
   | Secret | `DEPLOY_PATH` | путь к репозиторию на сервере, напр. `/opt/homework` |
   | Secret | `GHCR_TOKEN` | PAT с правом `read:packages` для `docker login` на сервере |
   | Secret | `GHCR_USER` | GitHub-логин для GHCR, необязательно (по умолчанию автор коммита) |
   | Variable | `DEPLOY_ENABLED` | `true` — включает job деплоя |
   | Variable | `DEPLOY_URL` | ссылка на приложение (для GitHub Environments) |

3. Запушить в `master` или создать тег:

   ```bash
   git tag v1.0.0 && git push origin v1.0.0
   ```

Деплой также можно выполнить вручную на сервере: `make prod-up`.

## Make-цели (кратко)

```bash
make help            # список всех целей
make up / down       # локальный стек
make test / lint     # проверки
make image           # docker build локального образа
make push            # push в ghcr.io (нужен docker login)
make prod-up         # production-стек из опубликованного образа
```

## Переменные окружения

`.env` не коммитится (см. `.gitignore`), шаблон — `.env.example`.

| Переменная | Назначение |
| --- | --- |
| `POSTGRESS_URL` | SQLAlchemy URL (`@db` заменяется на `DB_HOST`) |
| `DB_HOST` | хост PostgreSQL (`db` внутри compose) |
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` | параметры БД и контейнера `postgres` |
| `DB_PORT` | порт PostgreSQL |
| `DEEPSEEK_API_KEY` | ключ DeepSeek для ИИ-агента `/ai` |
| `IMAGE_REPO` / `IMAGE_TAG` | образ и тег для `docker-compose.prod.yml` |
| `WEB_PORT` / `DB_EXPOSED_PORT` | внешние порты production-стека |

## Замечания по безопасности

- production-образ работает от непривилегированного пользователя `app`;
- в образ не копируется `.env` — переменные приходят из `env_file`/окружения;
- gunicorn вместо dev-сервера Flask;
- контейнеры с `restart: unless-stopped` и healthcheck;
- секреты хранятся только в GitHub Secrets, `.env` — в `.gitignore`;
- в workflow используется встроенный `GITHUB_TOKEN` с минимальными правами
  (`contents: read`, `packages: write` только в CD).
