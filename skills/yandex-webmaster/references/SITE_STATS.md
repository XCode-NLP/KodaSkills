# Статистика сайта и индексация

## Сводка по сайту

```bash
bash scripts/summary.sh --host example.com
```

Возвращает:
- **SQI** (Site Quality Index) — индекс качества сайта
- **Searchable pages** — страницы, доступные в поиске
- **Excluded pages** — исключённые страницы
- **Problems** по уровням серьёзности:
  - `FATAL` — может привести к исключению из поиска
  - `CRITICAL` — SSL, битые ссылки, время ответа
  - `POSSIBLE_PROBLEM` — сайтмапы, robots.txt, дубли
  - `RECOMMENDATION` — рекомендации по оптимизации

## История SQI

> По умолчанию все history-скрипты запрашивают последние 90 дней. Для полной истории укажите `--date-from` явно.

```bash
bash scripts/sqi_history.sh --host example.com --date-from 2025-01-01
```

История индекса качества за последний год.

## Диагностика проблем

```bash
bash scripts/diagnostics.sh --host example.com
```

Всегда live (без кеша). Возвращает все проблемы с severity и state (`PRESENT`/`ABSENT`/`UNDEFINED`).

Типичные проблемы:
- FATAL: `SITE_ACCESS_FAILED`, `DNS_ERROR`, `ROBOTS_BLOCKED`, `SECURITY_THREAT`
- CRITICAL: `SSL_ERROR`, `SLOW_RESPONSE`, `HTTP_4XX`, `DUPLICATE_CONTENT`
- POSSIBLE: `NO_SITEMAP`, `ROBOTS_ERROR`, `SOFT_404`

## История индексации

```bash
bash scripts/indexing.sh --host example.com --action history --date-from 2025-03-01
```

Разбивка по HTTP-кодам: 2xx, 3xx, 4xx, 5xx, OTHER.

## Сэмплы индексации

```bash
bash scripts/indexing.sh --host example.com --action samples --limit 50
```

Список URL с их статусом индексации. Макс. 50 000 URL через API.

## Важные URL

```bash
bash scripts/important_urls.sh --host example.com --action list
```

Отслеживаемые URL с изменениями. Для истории конкретного URL:

```bash
bash scripts/important_urls.sh --host example.com --action history --url "https://example.com/page"
```

Индикаторы изменений: `INDEXING_HTTP_CODE`, `SEARCH_STATUS`, `TITLE`, `DESCRIPTION`.

Статусы исключения из поиска: `DUPLICATE`, `LOW_QUALITY`, `REDIRECT_NOTSEARCHABLE`, `ROBOTS_URL_ERROR`, `NO_INDEX` и другие.

## Экспорт всех страниц

```bash
bash scripts/archive_export.sh --host example.com --action start
bash scripts/archive_export.sh --host example.com --action status --task-id <id>
```

Генерация занимает от 10 секунд до 3 минут. Ссылка на скачивание действительна 24 часа.

## API endpoints

| Метод | Endpoint |
|-------|----------|
| GET | `/v4/user/{uid}/hosts/{hid}/summary` |
| GET | `/v4/user/{uid}/hosts/{hid}/sqi-history` |
| GET | `/v4/user/{uid}/hosts/{hid}/diagnostics` |
| GET | `/v4/user/{uid}/hosts/{hid}/indexing/history` |
| GET | `/v4/user/{uid}/hosts/{hid}/indexing/samples` |
| GET | `/v4/user/{uid}/hosts/{hid}/important-urls` |
| GET | `/v4/user/{uid}/hosts/{hid}/important-urls/history` |
| POST | `/v4/user/{uid}/hosts/{hid}/indexing/archive/` |
| GET | `/v4/user/{uid}/hosts/{hid}/indexing/archive/{tid}` |
