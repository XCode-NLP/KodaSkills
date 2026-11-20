# Compute Cloud

Каноническая документация: https://github.com/yandex-cloud/docs/tree/master/ru/compute · Публичная: https://yandex.cloud/ru/docs/compute/

## Понятия

| Термин | Что это |
|---|---|
| **Каталог** | Логическая группа ресурсов внутри облака — здесь живут биллинг, IAM и квоты |
| **Зона** | Зона доступности — `ru-central1-a`, `ru-central1-b`, `ru-central1-d` (зоны `-c` больше нет) |
| **Платформа** | Семейство железа — `standard-v3` (Intel Ice Lake), `standard-v2` (Cascade Lake), `gpu-standard-v3` (NVIDIA), `memory-optimized-v3` |
| **Преcет** | Пара CPU и RAM — `s3-c2-m4` = standard-v3, 2 vCPU, 4 ГБ RAM |
| **Образ и диск** | Загрузочный диск из публичного образа (Ubuntu 24.04 LTS, Debian 12 и т. д.) или своего снимка |
| **Группа размещения** | Разнесение или разделение для защиты от отказа стойки |
| **Прерываемая** | Дешевле примерно на 70 %, но может быть отозвана в течение 24 часов |
| **Файловая система** | Постоянное файловое хранилище, подключаемое по протоколу вроде NFS |

## Частые операции

### Создание машины (Ubuntu 24.04)

```bash
yc compute instance create \
  --name app-1 \
  --zone ru-central1-a \
  --platform standard-v3 \
  --cores 2 --memory 4 --core-fraction 100 \
  --create-boot-disk image-folder-id=standard-images,image-family=ubuntu-2404-lts,size=20,type=network-ssd \
  --network-interface subnet-name=default-ru-central1-a,nat-ip-version=ipv4 \
  --metadata-from-file user-data=cloud-init.yaml,ssh-keys=ssh-keys.txt \
  --service-account-name worker-sa \
  --hostname app-1
```

### Остановка, запуск, удаление

```bash
yc compute instance stop  app-1     # биллинг вычислений останавливается (диск всё равно тарифицируется)
yc compute instance start app-1
yc compute instance delete app-1    # НЕОБРАТИМО; подтверди с пользователем
```

### Снимок и восстановление

```bash
yc compute snapshot create --source-disk-name app-1-boot --name app-1-pre-upgrade
yc compute disk create --source-snapshot-name app-1-pre-upgrade --type network-ssd --size 20
# Затем создай новую машину с --attach-disk-name ...
```

## Типы дисков

| Тип | Для чего | Гарантии IOPS |
|---|---|---|
| `network-hdd` | Холодные резервные копии, разработка | Низкие |
| `network-ssd` | По умолчанию для приложений и БД | Хорошие, растут с размером |
| `network-ssd-nonreplicated` | Нужны высокие IOPS и своя репликация | Самые высокие, но без внутренней репликации |
| `network-ssd-io-m3` | Критичные БД | Уровень с оптимизацией задержки |

Для PostgreSQL на машине Compute: `network-ssd` от 100 ГБ; при высоком TPS — `network-ssd-nonreplicated` с WAL-G в Object Storage. Но лучше взять Managed PostgreSQL.

## cloud-init

Задай конфигурацию первого запуска через `--metadata-from-file user-data=cloud-init.yaml`. Пример:

```yaml
#cloud-config
users:
  - name: ubuntu
    sudo: ALL=(ALL) NOPASSWD:ALL
    ssh_authorized_keys:
      - ssh-ed25519 AAAA...
package_update: true
package_upgrade: true
packages: [angie, postgresql-client, ufw]
runcmd:
  - ufw default deny incoming
  - ufw allow 22/tcp
  - ufw allow 80,443/tcp
  - ufw --force enable
```

## Сервисный аккаунт на машине (рекомендуется)

Привяжи сервисный аккаунт при создании → внутри машины вызывай `169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token`, чтобы получить свежий IAM-токен без хранения ключей. Именно так приложения в YC должны авторизоваться в Object Storage, Lockbox и управляемых БД.

## Подводные камни

| Симптом | Причина | Что делать |
|---|---|---|
| `yc compute instance create` зависает на «PROVISIONING» | В подсети нет NAT-шлюза или публичный IP запрошен, но выключен | Добавь `nat-ip-version=ipv4` или привяжи NAT-шлюз к таблице маршрутов |
| SSH не отвечает после перезагрузки | UFW включён до разрешения 22 в cloud-init | Всегда `ufw allow 22/tcp` ДО `ufw --force enable` |
| Прерываемая машина исчезла через 24 часа | Так и задумано | Для значимых нагрузок бери непрерываемую |
| Диск полон, но `df` показывает свободное место | Кончились inode (много мелких файлов) | `df -i`; чисти `/var/log/journal`, старые контейнеры |
| Машина в зоне `ru-central1-c` не создаётся | Зона выведена | Используй `-a`, `-b` или `-d` |

## Смежные темы

- Машина за ALB → `load-balancer.md`
- Managed PG вместо своего PostgreSQL на машине → `managed-databases.md`
- Получение секретов с машины через метаданные → `secrets-lockbox.md`
- Настройка ОС внутри машины → навык `linux-sysadmin`
