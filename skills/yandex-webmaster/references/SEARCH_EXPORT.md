# PRO SERP экспорт

Экспорт данных по запросам из поисковой выдачи. Часть PRO-функциональности Вебмастера.

## Доступные даты

```bash
bash scripts/search_export.sh --host example.com --action dates
```

Показывает, за какие даты доступны данные для экспорта.

## Лимиты и квоты

```bash
bash scripts/search_export.sh --host example.com --action limits
```

Показывает доступные квоты (бесплатные и PRO), использование, период действия.

## Инициализация экспорта

```bash
bash scripts/search_export.sh --host example.com --action start \
    --dates '"2025-03-01","2025-03-02"' \
    --paths '"/","/catalog/"' \
    --region-ids "213"
```

Ограничение: макс. 100 комбинаций дат + URL.

Параметры:
- `--dates` — даты в формате JSON-строк (из `--action dates`)
- `--paths` — пути страниц (должны начинаться с `/`)
- `--region-ids` — опционально, пустой = все регионы

## Проверка статуса

```bash
bash scripts/search_export.sh --host example.com --action status --task-id <id>
```

Статусы:
- `IN_PROGRESS` — генерация
- `SUCCESS` — готово, ссылка доступна
- `FAILED` — ошибка

Ссылка на скачивание действительна 24 часа.

## API endpoints

| Метод | Endpoint |
|-------|----------|
| GET | `/v4/user/{uid}/hosts/{hid}/pro/serp/dates` |
| GET | `/v4/user/{uid}/hosts/{hid}/pro/limits` |
| POST | `/v4/user/{uid}/hosts/{hid}/pro/serp/queries/download/` |
| GET | `/v4/user/{uid}/hosts/{hid}/pro/serp/queries/download/{tid}` |
