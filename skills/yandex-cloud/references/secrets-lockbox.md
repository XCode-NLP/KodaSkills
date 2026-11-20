# Lockbox и KMS

Каноническая документация:
- Lockbox — https://github.com/yandex-cloud/docs/tree/master/ru/lockbox
- KMS — https://github.com/yandex-cloud/docs/tree/master/ru/kms

## Lockbox — хранилище секретов

Lockbox хранит **именованные полезные нагрузки секретов** (пары ключ-значение) с версиями. У каждого секрета несколько версий; старые остаются, пока их не уничтожат.

### Создание секрета

```bash
yc lockbox secret create \
  --name app-prod-secrets \
  --description "Prod app secrets" \
  --payload '[{"key":"DATABASE_URL","text_value":"postgres://app:pwd@c-XXX.rw.mdb.yandexcloud.net:6432/appdb?sslmode=verify-full"},
              {"key":"JWT_SECRET","text_value":"'$(openssl rand -hex 32)'"},
              {"key":"OPENAI_API_KEY","text_value":"sk-..."}]'
```

Для бинарных значений используй `binary_value` (в base64). Чтобы не светить содержимое в истории команд: `--payload @payload.json`.

### Чтение секрета (с машины через метаданные)

```bash
TOKEN=$(curl -s -H 'Metadata-Flavor: Google' \
  169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token | jq -r .access_token)

SECRET_ID=$(yc lockbox secret get app-prod-secrets --format value)

curl -s -H "Authorization: Bearer $TOKEN" \
  "https://payload.lockbox.api.cloud.yandex.net/lockbox/v1/secrets/$SECRET_ID/payload" \
  | jq -r '.entries[] | "export \(.key)=\(.text_value)"' > /run/secrets.env

# Использование в юните systemd или в ecosystem PM2:
#   EnvironmentFile=/run/secrets.env
```

У сервисного аккаунта машины должна быть роль `lockbox.payloadViewer`.

### Версии и ротация

```bash
# Добавить новую версию (старая остаётся рабочей, пока её не уничтожат)
yc lockbox secret add-version \
  --name app-prod-secrets \
  --description "rotated 2026-05-16" \
  --payload '[{"key":"JWT_SECRET","text_value":"'$(openssl rand -hex 32)'"}]'

# Список версий
yc lockbox secret list-versions --name app-prod-secrets

# Запланировать уничтожение старой версии (по умолчанию через 7 дней)
yc lockbox secret schedule-version-destruction --name app-prod-secrets --version-id <old-id>

# Отменить уничтожение в пределах окна
yc lockbox secret cancel-version-destruction --name app-prod-secrets --version-id <old-id>
```

Порядок ротации: добавить новую версию → перезапустить развёртывания на чтение новой → запланировать уничтожение старой после стабилизации.

### Монтирование в Kubernetes

Два подхода:

1. **Синхронизация в `Secret` Kubernetes через External Secrets Operator** (рекомендуется): установи `external-secrets`, опиши `SecretStore` на сервисный аккаунт Lockbox, затем `ExternalSecret` на каждый секрет.
2. **Сайдкары-загрузчики**: контейнер читает Lockbox через токен сервера метаданных при старте и пишет файл окружения в общий том.

### Использование в serverless

В Cloud Functions и Serverless Containers при `version create` передавай `--secrets environment-variable=DATABASE_URL,id=$SECRET_ID,key=DATABASE_URL`. YC подставляет значения во время выполнения.

## KMS — симметричные ключи шифрования

Нужен, когда ты шифруешь и расшифровываешь **свои** данные (например, файлы перед загрузкой в Object Storage) на управляемых ключах.

```bash
yc kms symmetric-key create --name app-data-key --default-algorithm aes-256

# Шифрование
yc kms symmetric-crypto encrypt \
  --key-name app-data-key \
  --plaintext-file plain.json \
  --ciphertext-file encrypted.bin

# Расшифровка
yc kms symmetric-crypto decrypt \
  --key-name app-data-key \
  --ciphertext-file encrypted.bin \
  --plaintext-file decrypted.json
```

Для конвертного шифрования (большой файл шифруется ключом данных, ключ данных — через KMS) используй `generate-data-key`.

### Автоматическая ротация

```bash
yc kms symmetric-key update --name app-data-key --rotation-period 30d
```

Старые версии ключа остаются пригодными для расшифровки; новое шифрование идёт на самой свежей.

## Что когда использовать

| Что нужно | Что брать |
|---|---|
| Секрет приложения (URL БД, API-ключ) | Lockbox |
| Шифрование пользовательских данных при хранении | KMS и свой код |
| Сертификаты TLS | Certificate Manager (НЕ Lockbox) |
| Шифрование Object Storage при хранении | YC шифрует автоматически; KMS не обязателен |
| Шифрование бакета своими ключами | KMS-ключ на бакет — поддерживается, см. документацию Object Storage |

## Подводные камни

| Симптом | Причина | Что делать |
|---|---|---|
| `permission denied` при чтении Lockbox с машины | У сервисного аккаунта нет `lockbox.payloadViewer` | Добавь привязку |
| Lockbox возвращает пустую нагрузку | Версия `SCHEDULED_FOR_DESTRUCTION` или уничтожена | Добавь новую версию |
| Секрет виден в выводе `yc compute instance get` | Использован `--metadata KEY=VALUE` для секретов — любой с доступом к машине его увидит | НИКОГДА не клади секреты в метаданные машины; используй Lockbox и токен из метаданных |
| `--payload` попал в историю команд | Использовано значение в строке | `--payload @file.json` и `chmod 600 file.json`, после — удали |
| Расшифровка KMS падает после ротации ключа | Попытка расшифровать не той версией | Старый шифротекст всё равно расшифровывается той версией, которой зашифрован — версия закодирована в заголовке |
