# Managed Service for Kubernetes

Каноническая документация: https://github.com/yandex-cloud/docs/tree/master/ru/managed-kubernetes · Публичная: https://yandex.cloud/ru/docs/managed-kubernetes/

## Понятия

| Термин | Что это |
|---|---|
| **Кластер** | Плоскость управления (мастер) — управляется YC, отказоустойчивость опциональна, региональный или зональный |
| **Группа узлов** | Пул рабочих машин с одинаковым пресетом — в кластере может быть несколько групп |
| **Канал релизов мастера** | `RAPID` (самый свежий), `REGULAR` (по умолчанию), `STABLE` (близко к LTS) |
| **CNI** | `CALICO` (по умолчанию) или `Cilium` |
| **Container Registry** | Родной реестр YC для образов; загрузка через сервисный аккаунт |

## Создание кластера

```bash
# Сервисные аккаунты для мастера и узлов
yc iam service-account create --name mk8s-master
yc iam service-account create --name mk8s-nodes
yc resource-manager folder add-access-binding $YC_FOLDER_ID \
  --role k8s.clusters.agent --service-account-id $(yc iam sa get mk8s-master --format value)
yc resource-manager folder add-access-binding $YC_FOLDER_ID \
  --role vpc.publicAdmin --service-account-id $(yc iam sa get mk8s-master --format value)
yc resource-manager folder add-access-binding $YC_FOLDER_ID \
  --role container-registry.images.puller --service-account-id $(yc iam sa get mk8s-nodes --format value)

yc managed-kubernetes cluster create \
  --name prod-mk8s \
  --network-name prod-net \
  --master-version 1.31 \
  --zonal zone=ru-central1-a,subnet-name=prod-ru-central1-a \
  --service-account-name mk8s-master \
  --node-service-account-name mk8s-nodes \
  --release-channel REGULAR \
  --public-ip                # мастер доступен через публичный эндпоинт; ограничь список разрешённых адресов

# Для продакшена переходи на отказоустойчивый региональный вариант (3 реплики мастера по зонам)
#   --regional region=ru-central1,location=zone=ru-central1-a,subnet-name=...,location=...,location=...
```

## Группы узлов

```bash
yc managed-kubernetes node-group create \
  --name workers-a \
  --cluster-name prod-mk8s \
  --platform standard-v3 \
  --cores 4 --memory 16 \
  --disk-type network-ssd --disk-size 64 \
  --location zone=ru-central1-a,subnet-name=prod-ru-central1-a \
  --auto-scale min=2,max=10,initial=3 \
  --auto-upgrade  --auto-repair
```

Для отказоустойчивости создавай по группе узлов на зону. Планировщик кластера распределяет поды по узлам; поды переживут отказ зоны, если упадёт группа узлов.

## Получение kubeconfig

```bash
yc managed-kubernetes cluster get-credentials prod-mk8s --external --force
# Запишет в ~/.kube/config, контекст = yc-prod-mk8s
kubectl get nodes
```

`--external` добавляет публичный эндпоинт; `--internal` работает только внутри VPC.

## Сеть

- **CIDR подов** и **CIDR сервисов** задаются при создании кластера и не меняются. Выбирай непересекающиеся с VPC и локальной сетью.
- **Группа безопасности мастера** ограничивает, кто может достучаться до API-сервера (порт 443). Задай её для продакшена — не выставляй на `0.0.0.0/0`.
- **NLB** для `Service type=LoadBalancer` создаётся автоматически; YC тарифицирует каждый NLB.
- **ALB** через **ALB Ingress Controller** для маршрутизации L7; ставится чартом Helm.

## ALB Ingress

```bash
# Установка контроллера
helm repo add yc-alb https://yandex-cloud.github.io/alb-ingress-controller
helm install alb-ic yc-alb/yc-alb-ingress-controller -n alb-system --create-namespace \
  --set folderID=$YC_FOLDER_ID

# Ресурс Ingress
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api-ingress
  annotations:
    ingress.alb.yc.io/subnets: <subnet-a-id>,<subnet-b-id>
    ingress.alb.yc.io/security-groups: <sg-id>
    ingress.alb.yc.io/external-ipv4-address: auto
spec:
  ingressClassName: alb
  rules:
    - host: api.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: api-svc
                port: { number: 80 }
EOF
```

## Container Registry

```bash
yc container registry create --name prod
REG_ID=$(yc container registry get prod --format value --jq .id)

# Загрузка с ноутбука (использует OAuth-токен yc)
yc container registry configure-docker
docker tag myapp:v1 cr.yandex/$REG_ID/myapp:v1
docker push cr.yandex/$REG_ID/myapp:v1
```

Узлы кластера забирают образы автоматически, когда у их сервисного аккаунта есть `container-registry.images.puller` на каталоге.

## Рабочая идентичность (сервисный аккаунт в подах)

Вместо монтирования файлов ключей сервисного аккаунта привяжи сервисный аккаунт YC к `ServiceAccount` Kubernetes через механизм федерации — поды получают IAM-токены автоматически. Рекомендуется для новых кластеров.

## Обновления

| Что | Как |
|---|---|
| **Мастер** | Автоматически (канал релизов и окно обслуживания) ИЛИ `yc managed-kubernetes cluster update --master-version 1.31` |
| **Узлы** | Автоматически с `--auto-upgrade` (узлы пересоздаются пакетами) ИЛИ вручную `node-group update --version 1.31` |
| **Перескок через версию** | НЕ поддерживается — обновляй по одной минорной версии (1.29 → 1.30 → 1.31) |

Сначала тестируй обновления в нерабочем кластере. Проверяй использование устаревших API через `kubectl get --raw /metrics | grep apiserver_requested_deprecated_apis`.

## Подводные камни

| Симптом | Причина | Что делать |
|---|---|---|
| `ImagePullBackOff` с `cr.yandex/...` | У сервисного аккаунта узлов нет `images.puller` | Добавь привязку |
| `Service type=LoadBalancer` висит в `<pending>` | У сервисного аккаунта мастера нет `vpc.publicAdmin` и `loadbalancer.admin` | Добавь привязки |
| `kubectl` уходит в таймаут | Публичный эндпоинт выключен или группа безопасности блокирует твой IP | `--internal` с машины в VPC ИЛИ открой группу |
| Под не видит Managed PG | Группа безопасности кластера БД не разрешает подсеть узлов | Разреши CIDR подсети узлов или по ссылке на группу |
| Автоскейлер не добавляет узлы | Достигнута квота в каталоге | `yc quota-manager quota get --service compute` |
| Обновление мастера застряло | PDB рабочих нагрузок блокирует вытеснение подов | Поправь PodDisruptionBudget или используй `--no-drain` (рискованно) |

## Смежные темы

- VPC для планирования CIDR кластера и подов → `vpc-network.md`
- Подключение к управляемым БД из подов → `managed-databases.md`
- Секреты в подах через Lockbox → `secrets-lockbox.md`
