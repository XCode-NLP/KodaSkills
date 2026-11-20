# Миграция — с самостоятельного хостинга на управляемые сервисы Яндекс Облака

Каноническая документация:
- Общая миграция — https://github.com/yandex-cloud/docs/tree/master/ru/datatransfer
- Data Transfer Service — https://github.com/yandex-cloud/docs/tree/master/ru/data-transfer

Этот справочник рассчитан на типовой стек: Ubuntu 24.04, Angie, PM2, свой PostgreSQL и Redis на одной или двух машинах Compute → эквивалент на управляемых сервисах YC.

## Дерево решений

```
Сейчас самостоятельно                  →  Эквивалент в YC
─────────────────────────────────────────────────────────
PostgreSQL на машине Compute          →  Managed PostgreSQL  (рекомендуется)
Redis на машине Compute               →  Managed Redis        (рекомендуется)
Angie как обратный прокси на машине   →  Машина Compute с Angie ИЛИ ALB (зависит от задачи)
Node-приложения на PM2 на машине      →  Машина Compute (та же) ИЛИ Serverless Containers (если без состояния)
Статика на диске                      →  Object Storage и CDN
Задания cron на машине                →  Оставить cron ИЛИ Cloud Functions с триггером по таймеру
Резервные копии на второй машине      →  Object Storage с жизненным циклом в cold и ice
```

**Не мигрируй всё сразу.** Сначала самое ценное: хранилища данных (PG, Redis) и статика (Object Storage). Вычисления и прокси могут остаться.

## Фаза 1 — Перенос PostgreSQL в Managed PG

### Подготовка

- Закрепи версию PG управляемого кластера на **ту же мажорную**, что у источника (например, источник PG 18 → целевой Managed PG 17, если 18 ещё не в общем доступе). Перенос между мажорными версиями добавляет сложности.
- Убедись, что на источнике `wal_level = logical` и `max_replication_slots ≥ 2`.
- Создай пользователя репликации на источнике: `CREATE ROLE yc_replicator REPLICATION LOGIN PASSWORD '...'`.
- В `pg_hba.conf`: разреши `yc_replicator` с IP-адресов воркеров Data Transfer (выдаются на шаге 3).

### Перенос через Data Transfer

```bash
# 1. Создать эндпоинты
yc datatransfer endpoint create source-postgres \
  --name pg-source \
  --postgres-source on-premise=hosts=[<source-ip>],port=5432,user=yc_replicator,password=...,database=appdb,tls-mode=disabled

yc datatransfer endpoint create target-postgres \
  --name pg-target \
  --postgres-target managed-cluster-id=$(yc managed-postgresql cluster get prod-pg --format value),database=appdb,user=admin,password=...

# 2. Создать перенос (снимок плюс CDC = переключение без простоя)
yc datatransfer transfer create snapshot-and-increment \
  --name pg-migrate \
  --source-id $(yc datatransfer endpoint get pg-source --format value) \
  --target-id $(yc datatransfer endpoint get pg-target --format value)

# 3. Активировать
yc datatransfer transfer activate pg-migrate

# 4. Следить
yc datatransfer transfer list-operations --id $(yc datatransfer transfer get pg-migrate --format value)
```

### Переключение

Когда начальный снимок готов и отставание CDC стабильно (несколько секунд):

1. Переведи приложение в режим только чтения
2. Дождись репликации последних записей (`SELECT * FROM pg_stat_replication` на источнике)
3. Смени `DATABASE_URL` приложения → FQDN Managed PG (`c-XXX.rw.mdb.yandexcloud.net`)
4. Перезапусти приложение
5. Убедись, что запись идёт в Managed PG и чтение возвращает те же данные
6. `yc datatransfer transfer deactivate pg-migrate`

План отката: держи исходную БД работающей 48 часов; верни `DATABASE_URL`, если всплывёт проблема.

## Фаза 2 — Перенос Redis

Встроенной «живой миграции» у Redis нет. Варианты:

| Способ | Когда | Простой |
|---|---|---|
| **Импорт снимка** | Кеш (данные восстановимы) | Минуты — очистка и прогрев |
| **Команда `MIGRATE`** (по ключам) | Небольшие наборы данных | От секунд до минут |
| **Репликация Redis → переключение первичного** | Значимое состояние | Секунды |
| **Двойная запись на уровне приложения** | Максимальная безопасность | Дни работы |

Для **кеша**: проще всего направить приложение в Managed Redis, принять холодный кеш и прогреть его.

Для **хранилища сессий** и другого значимого Redis: используй репликацию. Источник становится первичным; Managed Redis подключается репликой через VPN или пиринг; повышай, когда готов.

ACL в Managed Redis: пользователь приложения с `~* &* +@all -@dangerous` — разумное значение по умолчанию.

## Фаза 3 — Статика в Object Storage

У типового сайта файлы лежат в:
- `/var/www/uploads/`
- `/var/www/static/`

```bash
# Массовое копирование через rclone или aws-cli
aws s3 sync /var/www/uploads/ s3://my-prod-uploads/ \
  --endpoint-url https://storage.yandexcloud.net \
  --storage-class STANDARD

# Переведи приложение на адреса S3 (или подписанные ссылки)
# Поставь CDN спереди для горячих ассетов
```

Для сайтов только со статикой можно обойтись без машины: Object Storage с флагом `--website` и CDN обслуживают всё целиком.

## Фаза 4 — Вычисления (опционально)

Если приложение без состояния, а нагрузка переменная:

```
Было: одна крупная машина с PM2, Angie и всеми приложениями
Станет: ALB → две машины Compute (автомасштабирование через группу машин) с PM2 и Angie
        ИЛИ ALB → Serverless Containers (оплата за запрос, без PM2)
```

Оставь это на конец — это оптимизация, а не фундамент. Многие годами работают на одной машине Compute.

## Сеть до всего перечисленного

1. Создай VPC `prod-net` с тремя зональными подсетями
2. NAT-шлюз для исходящего трафика из частных подсетей
3. Группы безопасности: `app-sg`, `db-sg`, `bastion-sg` с минимальными входящими правилами
4. Бастионная машина с SSH только с IP офиса
5. Обнови `~/.ssh/config` с ProxyJump через бастион

## Смена модели затрат

| Свой сервер | Управляемый YC |
|---|---|
| Фиксированная месячная плата | Оплата по ресурсам: вычисления по часам, диск за ГБ-месяц, исходящий трафик за ГБ |
| Резервные копии вручную (цена — твоё время) | Копии входят в управляемые сервисы (бесплатные окна хранения) |
| Обновления вручную | Автоматически в управляемых сервисах (в окне обслуживания) |
| Отказоустойчивость по зонам стоит вдвое | Отказоустойчивость по зонам в управляемых оценивается обычно; делай с первого дня |

Перед решением посчитай стоимость в калькуляторе [yandex.cloud/ru/prices](https://yandex.cloud/ru/prices).

## Подводные камни

| Симптом | Причина | Что делать |
|---|---|---|
| Data Transfer: «permission denied» на источнике | В `pg_hba.conf` нет IP-адресов воркеров | YC публикует диапазоны воркеров; добавь CIDR или временно `0.0.0.0/0` |
| После переключения задержка приложения выросла вдвое | Приложение ходит в Managed PG через VPN или пиринг, больше хопов | Перенеси приложение на машину Compute в том же VPC, что и Managed PG |
| Скачок счёта за исходящий трафик после миграции | Приложение вне YC тянет образы и данные изнутри | Перенеси клиент в YC или поставь CDN |
| Затраты выше ожидаемых | Забыли удалить старые диски и снимки Compute | `yc compute disk list` и `snapshot list`; почисти лишнее |
| Восстановление из копии заняло часы | Для восстановления выделен слишком маленький диск | Выделяй кластер восстановления с диском не меньше источника |

## Смежные темы

- Проектирование VPC до миграции → `vpc-network.md`
- Сервисные аккаунты для воркеров Data Transfer → `iam-auth.md`
- Тонкости настройки БД → `managed-databases.md`
