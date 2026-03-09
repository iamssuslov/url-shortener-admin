# URL Shortener Admin Service

Мини-сервис сокращения ссылок с UI-админкой, API, soft delete, TTL, лимитами кликов, аудитом переходов и автотестами API/UI.

## Функциональность

- создание коротких ссылок
- custom aliases
- TTL и max_clicks
- редиректы и учёт кликов
- аудит переходов
- админка для поиска, фильтрации, блокировки и удаления ссылок
- API keys для API
- soft delete
- healthcheck
- X-Request-ID middleware
- экспорт CSV
- пагинация и сортировка

## Технологии

- FastAPI
- SQLModel / SQLite
- Jinja2
- Pytest
- Playwright
- Docker
- GitHub Actions

## Запуск локально

```bash
python -m venv .venv
source .venv/bin/activate
make install
make upgrade
make run
```

## Миграции

```bash
make upgrade
make migrate
make downgrade
```

## Parallel run

```bash
make test-parallel
```