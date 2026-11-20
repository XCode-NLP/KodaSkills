# Управление сайтмапами

## Список всех сайтмапов

```bash
bash scripts/sitemaps.sh --host example.com --action list --limit 50
```

Показывает все обнаруженные сайтмапы (из robots.txt, добавленные пользователем, индексные).

Источники (`sources`): `ROBOTS_TXT`, `WEBMASTER`, `INDEX_SITEMAP`.
Типы: `SITEMAP`, `INDEX_SITEMAP`.

## Пользовательские сайтмапы

```bash
bash scripts/sitemaps.sh --host example.com --action user-list
```

Только добавленные вручную через Вебмастер.

## Детали сайтмапа

```bash
bash scripts/sitemaps.sh --host example.com --action info --sitemap-id <id>
```

## Добавление сайтмапа

```bash
bash scripts/sitemaps.sh --host example.com --action add --url https://example.com/sitemap.xml
```

## Приоритетный переобход сайтмапа

### Проверка лимитов

```bash
bash scripts/sitemaps.sh --host example.com --action recrawl-limit
```

Показывает месячный лимит, использованные запросы и ближайшую доступную дату.

### Отправка на переобход

```bash
bash scripts/sitemaps.sh --host example.com --action recrawl --sitemap-id <id>
```

**Важно**: использует API v4.1 (не v4). Ограничение — месячная квота на приоритетный переобход.

## API endpoints

| Метод | Endpoint | Версия |
|-------|----------|--------|
| GET | `/v4/user/{uid}/hosts/{hid}/sitemaps` | v4 |
| GET | `/v4/user/{uid}/hosts/{hid}/sitemaps/{sid}` | v4 |
| GET | `/v4/user/{uid}/hosts/{hid}/user-added-sitemaps` | v4 |
| GET | `/v4/user/{uid}/hosts/{hid}/user-added-sitemaps/{sid}` | v4 |
| POST | `/v4/user/{uid}/hosts/{hid}/user-added-sitemaps` | v4 |
| GET | `/v4.1/user/{uid}/hosts/{hid}/sitemaps/recrawl` | v4.1 |
| POST | `/v4.1/user/{uid}/hosts/{hid}/sitemaps/{sid}/recrawl` | v4.1 |
