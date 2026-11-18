---
name: push-to-registry
description: "Публикация метаданных сборки Packer в реестр HCP Packer для отслеживания и управления жизненным циклом образов. Используй, когда нужно связать сборки Packer с HCP Packer ради контроля версий и управления."
license: MPL-2.0
metadata:
  author: hashicorp
  source: https://github.com/hashicorp/agent-skills
---

# Публикация в реестр HCP Packer

Настрой шаблоны Packer так, чтобы они отправляли метаданные сборки в реестр HCP Packer.

**Справка:** [HCP Packer Registry](https://developer.hashicorp.com/hcp/docs/packer)

> **Замечание:** HCP Packer бесплатен для базового использования. Сборки отправляют только метаданные (не сами образы), накладные расходы минимальны (меньше минуты).

## Базовая настройка реестра

```hcl
packer {
  required_version = ">= 1.7.7"
}

variable "image_name" {
  type    = string
  default = "web-server"
}

locals {
  timestamp = regex_replace(timestamp(), "[- TZ:]", "")
}

source "amazon-ebs" "ubuntu" {
  region        = "us-west-2"
  instance_type = "t3.micro"

  source_ami_filter {
    filters = {
      name = "ubuntu/images/*ubuntu-jammy-22.04-amd64-server-*"
    }
    most_recent = true
    owners      = ["099720109477"]
  }

  ssh_username = "ubuntu"
  ami_name     = "${var.image_name}-${local.timestamp}"
}

build {
  sources = ["source.amazon-ebs.ubuntu"]

  hcp_packer_registry {
    bucket_name = var.image_name
    description = "Ubuntu 22.04 base image for web servers"

    bucket_labels = {
      "os"   = "ubuntu"
      "team" = "platform"
    }

    build_labels = {
      "build-time" = local.timestamp
    }
  }

  provisioner "shell" {
    inline = [
      "sudo apt-get update",
      "sudo apt-get upgrade -y",
    ]
  }
}
```

## Аутентификация

Задай переменные окружения перед сборкой:

```bash
export HCP_CLIENT_ID="your-service-principal-client-id"
export HCP_CLIENT_SECRET="your-service-principal-secret"
export HCP_ORGANIZATION_ID="your-org-id"
export HCP_PROJECT_ID="your-project-id"

packer build .
```

### Создание субъекта-службы HCP

1. Перейди в HCP → Access Control (IAM).
2. Создай субъект-службу (Service Principal).
3. Выдай роль «Contributor» на проект.
4. Сгенерируй секрет клиента.
5. Сохрани идентификатор клиента и секрет.

## Параметры настройки реестра

### bucket_name (обязательный)
Идентификатор образа. Должен оставаться неизменным между сборками!

```hcl
bucket_name = "web-server"  # держи это значение постоянным
```

### bucket_labels (необязательный)
Метаданные уровня бакета. Обновляются с каждой сборкой.

```hcl
bucket_labels = {
  "os"        = "ubuntu"
  "team"      = "platform"
  "component" = "web"
}
```

### build_labels (необязательный)
Метаданные каждой итерации. Неизменяемы после завершения сборки.

```hcl
build_labels = {
  "build-time" = local.timestamp
  "git-commit" = var.git_commit
}
```

## Интеграция с CI/CD

### GitHub Actions

```yaml
name: Build and Push to HCP Packer

on:
  push:
    branches: [main]

env:
  HCP_CLIENT_ID: ${{ secrets.HCP_CLIENT_ID }}
  HCP_CLIENT_SECRET: ${{ secrets.HCP_CLIENT_SECRET }}
  HCP_ORGANIZATION_ID: ${{ secrets.HCP_ORGANIZATION_ID }}
  HCP_PROJECT_ID: ${{ secrets.HCP_PROJECT_ID }}

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: hashicorp/setup-packer@main

      - name: Build and push
        run: |
          packer init .
          packer build \
            -var "git_commit=${{ github.sha }}" \
            .
```

## Запросы из Terraform

```hcl
data "hcp_packer_artifact" "ubuntu" {
  bucket_name  = "web-server"
  channel_name = "production"
  platform     = "aws"
  region       = "us-west-2"
}

resource "aws_instance" "web" {
  ami           = data.hcp_packer_artifact.ubuntu.external_identifier
  instance_type = "t3.micro"

  tags = {
    PackerBucket = data.hcp_packer_artifact.ubuntu.bucket_name
  }
}
```

## Частые проблемы

**Сбой аутентификации**
- Проверь `HCP_CLIENT_ID` и `HCP_CLIENT_SECRET`.
- Убедись, что у субъекта-службы есть роль Contributor.
- Проверь идентификаторы организации и проекта.

**Несовпадение имени бакета**
- Держи `bucket_name` неизменным между сборками.
- Не добавляй в `bucket_name` метки времени.
- При смене имени создаётся новый бакет.

**Сборка падает**
- Packer падает сразу, если не может отправить метаданные.
- Это предотвращает расхождение между артефактами и реестром.
- Проверь сетевую связность с API HCP.

## Рекомендации

- **Постоянные имена бакетов** — никогда не меняй их для одного типа образа.
- **Осмысленные метки** — используй их для версий, команд, соответствия требованиям.
- **Автоматизация CI/CD** — автоматизируй сборки и публикацию в реестр.
- **Неизменяемые метки сборки** — изменяющиеся данные (git SHA, дату) клади в `build_labels`.

## Ссылки

- [Документация HCP Packer](https://developer.hashicorp.com/hcp/docs/packer)
- [Блок hcp_packer_registry](https://developer.hashicorp.com/packer/docs/templates/hcl_templates/blocks/build/hcp_packer_registry)
- [Провайдер HCP Terraform](https://registry.terraform.io/providers/hashicorp/hcp/latest/docs/data-sources/packer_artifact)
