# YML-фиды

## Обзор

YML-фиды используются для улучшенного представления товаров, услуг, объектов недвижимости и др. в поиске Яндекса. Только HTTPS.

Поддерживаемые форматы файлов: `.xml`, `.yml`, gzip-архивы.

## Типы фидов

| Тип | Описание |
|-----|----------|
| `REALTY` | Недвижимость |
| `VACANCY` | Вакансии |
| `GOODS` | Товары |
| `DOCTORS` | Врачи |
| `CARS` | Автомобили |
| `SERVICES` | Услуги |
| `EDUCATION` | Образование |
| `ACTIVITY` | Мероприятия |

## Список фидов

```bash
bash scripts/feeds.sh --host example.com --action list
```

## Добавление фида

```bash
bash scripts/feeds.sh --host example.com --action add \
    --url "https://example.com/feed.yml" \
    --type GOODS \
    --region-ids "225,213"
```

Регион по умолчанию: 225 (Россия).

Загрузка асинхронная. Проверка статуса:

```bash
bash scripts/feeds.sh --host example.com --action add-status --request-id <id>
```

Статусы: `OK`, `IN_PROGRESS`.

## Изменение регионов

```bash
bash scripts/feeds.sh --host example.com --action change \
    --url "https://example.com/feed.yml" \
    --region-ids "213,2"
```

## Основные регионы

| ID | Регион |
|----|--------|
| 225 | Россия |
| 213 | Москва |
| 2 | Санкт-Петербург |
| 54 | Екатеринбург |
| 43 | Казань |
| 66 | Нижний Новгород |
| 56 | Новосибирск |

Полный список: [Справочник регионов](https://yandex.ru/dev/webmaster/doc/ru/reference/feeds-regions)

## Лимиты

- Макс. 5000 фидов на сайт
- Макс. 50 фидов в batch-запросе
- Макс. 50 одновременных асинхронных загрузок

## API endpoints

| Метод | Endpoint |
|-------|----------|
| GET | `/v4/user/{uid}/hosts/{hid}/feeds/list` |
| POST | `/v4/user/{uid}/hosts/{hid}/feeds/add/start` |
| GET | `/v4/user/{uid}/hosts/{hid}/feeds/add/info` |
| POST | `/v4/user/{uid}/hosts/{hid}/feeds/batch/add` |
| POST | `/v4/user/{uid}/hosts/{hid}/feeds/change` |
