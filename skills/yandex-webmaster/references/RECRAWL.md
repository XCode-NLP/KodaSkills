# Переобход страниц

## Квота

```bash
bash scripts/recrawl.sh --host example.com --action quota
```

Показывает дневную квоту и остаток. Данные всегда live (без кеша).

## Отправка URL на переобход

```bash
bash scripts/recrawl.sh --host example.com --action submit --url "https://example.com/updated-page"
```

Ответ включает `task_id` и `quota_remainder`.

Возможные ошибки:
- `INVALID_URL` — невалидный URL
- `URL_ALREADY_ADDED` — URL уже в очереди
- `QUOTA_EXCEEDED` — дневная квота исчерпана

## Статус задачи

```bash
bash scripts/recrawl.sh --host example.com --action status --task-id <id>
```

Состояния:
- `IN_PROGRESS` — в процессе
- `DONE` — завершено
- `FAILED` — ошибка

## Список задач

```bash
bash scripts/recrawl.sh --host example.com --action list --limit 20
bash scripts/recrawl.sh --host example.com --action list --date-from 2025-03-01
```

## Приоритетный переобход сайтмапа

Отдельная функция — см. [SITEMAPS.md](SITEMAPS.md) (`--action recrawl` и `--action recrawl-limit`).

## API endpoints

| Метод | Endpoint |
|-------|----------|
| POST | `/v4/user/{uid}/hosts/{hid}/recrawl/queue` |
| GET | `/v4/user/{uid}/hosts/{hid}/recrawl/queue/{tid}` |
| GET | `/v4/user/{uid}/hosts/{hid}/recrawl/queue` |
| GET | `/v4/user/{uid}/hosts/{hid}/recrawl/quota` |
