# Object Storage

Каноническая документация: https://github.com/yandex-cloud/docs/tree/master/ru/storage · Публичная: https://yandex.cloud/ru/docs/storage/

Совместим с S3 (в основном). Эндпоинт: `https://storage.yandexcloud.net`. Регион: `ru-central1`.

## Две плоскости управления

| Плоскость | Для чего |
|---|---|
| `yc storage` | Родная для YC: жизненный цикл бакета, метаданные, политики через API YC |
| `aws s3`, `aws s3api`, SDK для S3 | Операции с данными; подпись S3 v4, ACL и политики через API S3 |

Смешивать можно свободно. Для продакшена создавай бакеты через `yc` и Terraform, а операции с данными делай через SDK.

## Авторизация для клиентов S3

Генерируй статические ключи доступа от **сервисного аккаунта**, а не от OAuth пользователя:

```bash
yc iam service-account create --name s3-writer
yc resource-manager folder add-access-binding $YC_FOLDER_ID \
  --role storage.editor --service-account-id $(yc iam service-account get s3-writer --format value)
yc iam access-key create --service-account-name s3-writer
# → выведет access_key и secret — храни в Lockbox или ~/.aws/credentials
```

Затем для `aws-cli`:

```bash
aws configure set aws_access_key_id YCAJ...
aws configure set aws_secret_access_key ...
aws configure set region ru-central1

# Всегда указывай эндпоинт
aws s3 ls --endpoint-url https://storage.yandexcloud.net
```

Для SDK на Node и Python: задай `endpoint: 'https://storage.yandexcloud.net'`, `region: 'ru-central1'`, `forcePathStyle: false` (стиль с хостом в имени работает).

## Создание бакета

```bash
yc storage bucket create \
  --name my-prod-uploads \
  --default-storage-class standard \
  --max-size 107374182400 \
  --acl private \
  --versioning versioning-enabled

# Разрешить хостинг сайта
yc storage bucket update --name my-prod-uploads \
  --website index-file=index.html,error-file=404.html
```

## Классы хранения

| Класс | Когда | Стоимость извлечения |
|---|---|---|
| `standard` | Горячие данные | Бесплатно |
| `cold` | Реже одного обращения в месяц | Платно за каждый извлечённый гигабайт |
| `ice` | Архив (редко, раз в 1–90 дней) | Дороже извлечение и минимум 90 дней хранения |

Переводи данные автоматически политикой жизненного цикла: через 30 дней → `cold`, через 180 → `ice`.

## Политика бакета (JSON в формате S3)

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "PublicReadGetObject",
    "Effect": "Allow",
    "Principal": "*",
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::my-prod-uploads/public/*"
  }]
}
```

Применяй через `yc storage bucket update --name X --policy-file policy.json` или через `aws-cli s3api put-bucket-policy`.

## Presigned-ссылки

Подписывай по S3 v4 — большинство SDK работают сразу, только передай эндпоинт YC:

```ts
// Node (AWS SDK v3)
import { S3Client, GetObjectCommand } from '@aws-sdk/client-s3';
import { getSignedUrl } from '@aws-sdk/s3-request-presigner';

const s3 = new S3Client({
  endpoint: 'https://storage.yandexcloud.net',
  region: 'ru-central1',
  credentials: { accessKeyId, secretAccessKey },
});

const url = await getSignedUrl(
  s3,
  new GetObjectCommand({ Bucket: 'my-prod-uploads', Key: 'foo.pdf' }),
  { expiresIn: 600 }
);
```

## CORS

Конфигурация в JSON, задаётся через API S3 `put-bucket-cors` или в консоли YC.

```json
{
  "CORSRules": [{
    "AllowedOrigins": ["https://app.example.com"],
    "AllowedMethods": ["GET", "PUT", "POST"],
    "AllowedHeaders": ["*"],
    "MaxAgeSeconds": 3000,
    "ExposeHeaders": ["ETag"]
  }]
}
```

## Статический хостинг сайта

```bash
yc storage bucket update --name my-site \
  --website index-file=index.html,error-file=404.html \
  --acl public-read
# Адрес сайта: https://my-site.website.yandexcloud.net
```

Для своего домена с TLS поставь спереди **Yandex CDN** или **Application Load Balancer** с сертификатом.

## Отличия от S3

| Возможность | Поведение в YC |
|---|---|
| **Multipart upload** | Поддерживается, тот же API |
| **Шифрование на стороне сервера** | YC шифрует при хранении по умолчанию; заголовок `x-amz-server-side-encryption` молча игнорируется |
| **`s3:CopyObject` между регионами** | В YC один регион (`ru-central1`) — не применимо |
| **Object Lock (WORM)** | Не поддерживается |
| **Отчёты инвентаризации** | Не поддерживаются |
| **Уведомления о событиях в Lambda** | Используй триггер Cloud Functions — другой API |
| **Requester Pays** | Не поддерживается |

## Подводные камни

| Симптом | Причина | Что делать |
|---|---|---|
| `SignatureDoesNotMatch` | Неверный эндпоинт или регион | Эндпоинт `storage.yandexcloud.net`, регион `ru-central1` |
| `403 AccessDenied` при верных ключах | У сервисного аккаунта нет роли `storage.editor` на каталоге | Добавь привязку |
| Список отдаёт по одному файлу | Забыл пагинацию | `aws s3api list-objects-v2 --max-items 1000 --starting-token ...` |
| Политика бакета «применяется», но не работает | Конфликт с ACL объекта или синтаксическая ошибка, молча отклонённая старым эндпоинтом | Проверь через `yc storage bucket get`; проверь curl |
| Скачок счёта за исходящий трафик | Приложение часто забирает файлы извне YC | Поставь CDN спереди, агрессивно кэшируй, используй ссылки с большим сроком |
