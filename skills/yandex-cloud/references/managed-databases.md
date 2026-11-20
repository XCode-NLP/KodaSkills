# Управляемые базы данных

Каноническая документация по сервисам:
- PostgreSQL — https://github.com/yandex-cloud/docs/tree/master/ru/managed-postgresql
- MySQL — https://github.com/yandex-cloud/docs/tree/master/ru/managed-mysql
- Redis — https://github.com/yandex-cloud/docs/tree/master/ru/managed-redis
- ClickHouse — https://github.com/yandex-cloud/docs/tree/master/ru/managed-clickhouse
- MongoDB — https://github.com/yandex-cloud/docs/tree/master/ru/managed-mongodb
- Kafka — https://github.com/yandex-cloud/docs/tree/master/ru/managed-kafka
- Greenplum — https://github.com/yandex-cloud/docs/tree/master/ru/managed-greenplum
- OpenSearch — https://github.com/yandex-cloud/docs/tree/master/ru/managed-opensearch

## Общий шаблон

У любого управляемого кластера одна форма:

1. **Кластер** — сущность верхнего уровня, владеет сетью, IAM и политикой резервного копирования
2. **Хосты** — N реплик по зонам, одна из них первичная (PG, MySQL, Mongo) или все равны (кластер Redis, шарды ClickHouse)
3. **Базы и пользователи** — создаются внутри кластера
4. **Подключение** — по частному FQDN вида `c-<cluster-id>.rw.mdb.yandexcloud.net` (чтение и запись) или `.ro.` (реплика)
5. **Окно обслуживания** — недельный слот, когда YC ставит обновления; по умолчанию любое время, для продакшена задай явно

## Managed PostgreSQL — быстрый старт

```bash
yc managed-postgresql cluster create \
  --name prod-pg \
  --environment production \
  --network-name default \
  --host zone-id=ru-central1-a,subnet-name=default-ru-central1-a,assign-public-ip=false \
  --host zone-id=ru-central1-b,subnet-name=default-ru-central1-b,assign-public-ip=false \
  --resource-preset s3-c2-m8 \
  --disk-type network-ssd --disk-size 100 \
  --postgresql-version 17 \
  --user name=app,password=$(openssl rand -base64 32) \
  --database name=appdb,owner=app \
  --backup-window-start hours=2,minutes=0 \
  --security-group-ids enz...

# Получить FQDN для подключения
yc managed-postgresql host list --cluster-name prod-pg

# Подключение (изнутри сети YC или по VPN)
psql "host=c-CLUSTER.rw.mdb.yandexcloud.net port=6432 \
      sslmode=verify-full sslrootcert=/etc/ssl/certs/YandexInternalRootCA.crt \
      dbname=appdb user=app"
```

## Особенность пула соединений

Каждый кластер Managed PG поставляется с пулом соединений **Odyssey** спереди (порт 6432). Подключения приложения идут в Odyssey, а не напрямую в Postgres. Следствия:

- `pg_stat_activity` показывает сессии пула, а не сессии приложения
- Долгоживущим подготовленным выражениям нужен `pool_mode = session` в параметрах пула (по умолчанию `transaction`)
- Ставь пул приложения меньше лимита Odyssey — согласовывай размеры пулов по цепочке

## Резервное копирование

| Тип | Когда | Как восстановить |
|---|---|---|
| **Автоматическое** | Ежедневно в окне копирования, хранится 7 дней (бесплатно) или 30 и 90 дней (платно) | `yc managed-postgresql cluster restore --backup-id <id> --name prod-pg-restored ...` (НОВЫЙ кластер, на месте нельзя) |
| **Ручное, по требованию** | Перед рискованным изменением | `yc managed-postgresql cluster backup --name prod-pg` |
| **PITR по архиву WAL** | Непрерывно | Восстановление на любой момент в пределах окна хранения |

**Правило**: всегда `yc managed-postgresql cluster backup` ДО обновления версии или смены конфигурации. Восстановление идёт в НОВЫЙ кластер — планируй простой соответственно.

## Подключение извне YC

Управляемые кластеры по умолчанию доступны **только по частному FQDN**. Чтобы подключиться с ноутбука:

1. **VPN в YC** — рекомендуется; бастион или WireGuard на машине Compute в том же VPC
2. **Публичный IP** — `assign-public-ip=true` на хост; группа безопасности должна разрешить твой IP; исходящий трафик дорогой
3. **Бастионная машина** — `ssh -L 6432:c-XXX.rw.mdb.yandexcloud.net:6432 user@bastion`; безопасно и просто

Никогда не открывай Managed PG и Redis на `0.0.0.0/0`, даже с сильными паролями; группы безопасности должны запрещать входящий трафик по умолчанию.

## Особенности Managed Redis

- Не все ключи меняются через `CONFIG SET` — часть задаётся в `update --config` кластера
- Режим Sentinel и кластерный выбираются при создании кластера
- `maxmemory-policy` настраивается; `noeviction` (по умолчанию) блокирует запись при заполнении — для кеша ставь `allkeys-lru`
- TLS: `--config tls-port=6379,port=0`, чтобы оставить только TLS

## Managed ClickHouse — шарды и реплики

Два измерения: шард (разбиение данных) и реплика (отказоустойчивость). Для большинства проектов: 1 шард, 2–3 реплики. Несколько шардов — только при объёмах больше терабайт.

```bash
yc managed-clickhouse cluster create ... \
  --shard-name shard1 \
  --host type=clickhouse,zone-id=ru-central1-a,shard-name=shard1 \
  --host type=clickhouse,zone-id=ru-central1-b,shard-name=shard1 \
  --host type=zookeeper,zone-id=ru-central1-a \
  --host type=zookeeper,zone-id=ru-central1-b \
  --host type=zookeeper,zone-id=ru-central1-d
```

Хосты ZooKeeper обязательны, если реплик на шард больше одной.

## Что учитывать в биллинге

- **Диск** тарифицируется непрерывно, даже когда кластер в состоянии `STOPPED`
- **Публичный IP** и **исходящий трафик** в болтливых нагрузках могут перекрыть стоимость вычислений
- **Копии старше 7 дней** платные за гигабайт
- **Сессии пула** занимают квоту `max_connections` хоста; завышенный пул приложения = кластер исчерпал соединения

## Подводные камни

| Симптом | Причина | Что делать |
|---|---|---|
| `FATAL: no pg_hba.conf entry` | Пользователь есть, но у него нет доступа к базе | `yc managed-postgresql user grant-permission --cluster-name X --user-name app --database-name appdb` |
| Медленный запрос внезапно замедлился после обновления | Регрессия плана после смены версии PG | Смотри `pg_stat_statements`, возможно `ANALYZE`, откатись к прежней версии восстановлением |
| Растёт отставание реплики | Сеть или долгая пишущая транзакция на первичном | `pg_stat_replication`; проверь долгие запросы; возможно, нужен пресет больше |
| Соединение к `host=...rw.mdb.yandexcloud.net` с машины отклонено | Группа безопасности машины не разрешает исходящий трафик, либо группа БД не разрешает подсеть машины | Открой обе группы |
| В кластере Redis клиент путается от ответа `MOVED` | Приложение не настроено на кластерный режим | Используй `redis-cli -c` или кластерный режим ioredis |
