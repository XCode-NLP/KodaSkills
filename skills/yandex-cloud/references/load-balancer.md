# Балансировщики — ALB (L7) и NLB (L4)

Каноническая документация:
- ALB — https://github.com/yandex-cloud/docs/tree/master/ru/application-load-balancer
- NLB — https://github.com/yandex-cloud/docs/tree/master/ru/network-load-balancer

## ALB против NLB

| | **ALB (Application LB)** | **NLB (Network LB)** |
|---|---|---|
| Уровень | L7 (HTTP/1.1, HTTP/2, gRPC, WebSocket) | L4 (TCP, UDP) |
| Маршрутизация по пути | ✅ Да | ❌ Нет |
| Маршрутизация по хосту | ✅ Да | ❌ Нет |
| Завершение TLS | ✅ С сертификатами из Certificate Manager | ❌ Только проброс |
| WebSocket | ✅ | ✅ |
| gRPC | ✅ | ✅ (как TCP) |
| Автомасштабирование бэкендов | ✅ через целевые группы | ✅ через целевые группы |
| Задержка | Порядка миллисекунд (больше обработки) | Меньше миллисекунды |
| Для чего | API-шлюз, сайты, микросервисы под одним доменом | Фронт БД, сырой TCP, максимальная пропускная способность |

**Правило**: нагрузка по HTTP и HTTPS → ALB. Всё остальное → NLB.

## Структура ALB

```
Балансировщик (слушатель фронтенда :443)
  └── HTTP-роутер (правила: хост и путь → группа бэкендов)
      └── Группа бэкендов (именованный пул)
          └── Цели:
              ├── Целевая группа (машины Compute, поды Kubernetes по IP) → с проверкой здоровья
              └── ИЛИ статические эндпоинты и прямые IP
```

Проверка здоровья обязательна для каждой группы бэкендов. Рекомендуется: HTTP GET `/healthz`, интервал 5 с, порог нездоровья 3.

## Быстрый старт ALB

```bash
# 1. Сертификат из Certificate Manager (Let's Encrypt или импортированный)
yc certificate-manager certificate request \
  --name api-cert --domains api.example.com --challenge-type dns

# Дождись статуса ISSUED, затем пройди DNS-валидацию по выводу

# 2. Целевая группа (например, машины в двух зонах)
yc alb target-group create --name api-tg \
  --target subnet-name=prod-ru-central1-a,address=10.10.0.5 \
  --target subnet-name=prod-ru-central1-b,address=10.10.16.5

# 3. Группа бэкендов с проверкой здоровья
yc alb backend-group create --name api-bg \
  --http-backend "name=app,target-group-id=$(yc alb target-group get api-tg --format value),port=8080,healthcheck-port=8080,healthcheck-path=/healthz,healthcheck-interval=5s"

# 4. HTTP-роутер (путь → бэкенд)
yc alb http-router create --name api-router
yc alb virtual-host create --name api-vh --router-name api-router \
  --authority "api.example.com"
yc alb http-router-rule create ... # сопоставь пути с api-bg

# 5. Балансировщик
yc alb load-balancer create --name api-lb \
  --network-name prod-net \
  --location subnet-name=prod-ru-central1-a,zone=ru-central1-a \
  --location subnet-name=prod-ru-central1-b,zone=ru-central1-b \
  --listener "name=https,external-ipv4-endpoint=auto,port=443,tls-cert-id=$(yc certificate-manager certificate get api-cert --format value),http-router-id=$(yc alb http-router get api-router --format value)"
```

## Быстрый старт NLB

```bash
# Целевая группа (машины)
yc load-balancer target-group create --name pg-tg \
  --region ru-central1 \
  --target subnet-name=prod-ru-central1-a,address=10.10.0.10 \
  --target subnet-name=prod-ru-central1-b,address=10.10.16.10

# NLB с TCP-слушателем
yc load-balancer network-load-balancer create --name pg-nlb \
  --region ru-central1 \
  --listener name=pg,port=5432,target-port=5432,protocol=tcp,external-ipv4-endpoint=auto \
  --attached-target-group "target-group-id=$(yc load-balancer target-group get pg-tg --format value),healthcheck-name=tcp,healthcheck-tcp-port=5432"
```

## Внешний и внутренний

- **Внешний** (`external-ipv4-endpoint=auto`) — публичный IP, доступен из интернета
- **Внутренний** (`internal-ipv4-endpoint=...,subnet-name=...`) — только внутри VPC; хорош для трафика между сервисами

## TLS и сертификаты

Два источника:
1. **Yandex Certificate Manager, управляемый** (бесплатно, Let's Encrypt): YC сам продлевает. Для публичных доменов.
2. **Импортированный сертификат** (свой или wildcard от корпоративного CA): загружаешь и ротируешь сам. Для внутренних CA.

У слушателя может быть несколько сертификатов (SNI): `tls-cert-id=cert1,tls-cert-id=cert2,...`.

## Подводные камни

| Симптом | Причина | Что делать |
|---|---|---|
| ALB отдаёт 503 при здоровых бэкендах | К группе бэкендов не привязан `http-router` или правила HTTP не совпадают с хостом | Проверь, что `yc alb load-balancer get` показывает роутер; сверь маршрутизацию по заголовку `Host:` |
| Проверка здоровья не проходит — цель UNHEALTHY | Группа безопасности на целевых машинах не разрешает адреса проверок балансировщика | Добавь входящее правило для группы безопасности целевой группы ALB |
| NLB отдаёт 502 на HTTP-трафике | Используется NLB для HTTP — проброс не умеет проверки на уровне приложения | Перейди на ALB ИЛИ аккуратно настрой TCP-проверку |
| Сертификат не выпускается | Нет DNS-записи для проверки | Добавь CNAME из вывода cert-manager в свой DNS-провайдер; или `--challenge-type http` |
| `tls handshake failure` | Сертификат в другом каталоге, не в каталоге ALB | Перенеси сертификат ИЛИ перевыпусти в каталоге ALB |
| WebSocket рвётся каждую минуту | Таймаут простоя ALB по умолчанию 60 с | Увеличь `idle-timeout` слушателя |
