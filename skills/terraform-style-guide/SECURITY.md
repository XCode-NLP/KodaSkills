---
name: terraform-style-guide-security
description: "Генерация кода Terraform HCL с соблюдением практик безопасности HashiCorp"
---

# Стиль Terraform — безопасность

Когда генерируешь код, применяй усиление безопасности:

- включай шифрование при хранении по умолчанию;
- настраивай приватные сети там, где это применимо;
- применяй принцип наименьших привилегий для групп безопасности;
- включай журналирование и мониторинг;
- никогда не вшивай учётные данные и секреты;
- помечай чувствительные выходные значения как `sensitive = true`;
- по возможности используй эфемерные ресурсы и write-only атрибуты
  для чувствительных данных.

## Пример: защищённый бакет S3

```hcl
resource "aws_s3_bucket" "data" {
  bucket = "${var.project}-${var.environment}-data"
  tags   = local.common_tags
}

resource "aws_s3_bucket_versioning" "data" {
  bucket = aws_s3_bucket.data.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data" {
  bucket = aws_s3_bucket.data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.s3.arn
    }
  }
}

resource "aws_s3_bucket_public_access_block" "data" {
  bucket = aws_s3_bucket.data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
```

## Эфемерные ресурсы

Эфемерные ресурсы не дают чувствительным данным попадать в состояние.
Подробнее об эфемерных ресурсах — в
[документации Terraform](https://developer.hashicorp.com/terraform/language/block/ephemeral).

Прежде чем генерировать код с эфемерным ресурсом, проверь, что версия Terraform
не меньше 1.11.0.

Затем следуй такому порядку приоритетов для работы с чувствительными атрибутами:

1. **Первый приоритет: встроенная интеграция с менеджером секретов.**
   Если у ресурса есть возможность автоматически управлять чувствительным атрибутом,
   храня его в менеджере секретов (например, AWS Secrets Manager, Azure Key Vault),
   используй эту конфигурацию. Это предпочтительный подход.

   ```hcl
   # Bad
   resource "aws_rds_cluster" "example" {
     cluster_identifier = "example"
     database_name      = "test"
     master_username    = "test"
     master_password    = var.db_master_password
   }

   # Good, managed by AWS Secrets Manager by default
   resource "aws_rds_cluster" "test" {
     cluster_identifier          = "example"
     database_name               = "test"
     manage_master_user_password = true
     master_username             = "test"
   }
   ```

2. **Второй приоритет: write-only атрибуты с эфемерными ресурсами.**
   Если у ресурса есть write-only атрибут, но нет встроенной интеграции с менеджером
   секретов, используй эфемерный ресурс для чувствительных данных и передай его в write-only
   атрибут. Версию write-only атрибута по умолчанию ставь в 1.

   ```hcl
   # Bad
   resource "random_password" "password" {
     length           = 16
     special          = true
     override_special = "!#$%&*()-_=+[]{}<>:?"
   }

   resource "vault_kv_secret_v2" "example" {
     mount               = vault_mount.kvv2.path
     name                = "secret"

     data_json = jsonencode(
       {
         password = "${random_password.password.result}",
       }
     )
   }

   # Good
   ephemeral "random_password" "password" {
     length           = 16
     special          = true
     override_special = "!#$%&*()-_=+[]{}<>:?"
   }

   resource "vault_kv_secret_v2" "example" {
     mount               = vault_mount.kvv2.path
     name                = "secret"

     data_json_wo = jsonencode(
       {
         password = "${ephemeral.random_password.password.result}",
       }
     )
     data_json_wo_version = 1
   }
   ```

   Если нужно достать секрет из менеджера секретов, чтобы передать его
   ресурсу, используй эфемерную версию ресурса, чтобы
   получить секрет и передать его другому ресурсу.

   ```hcl
   # Good
   ephemeral "vault_kv_secret_v2" "db_secret" {
     mount = vault_mount.kvv2.path
     mount_id = vault_mount.kvv2.id
     name = vault_kv_secret_v2.db_root.name
   }

   resource "vault_database_secret_backend_connection" "postgres" {
     backend       = vault_mount.db.path
     name          = "postrgres-db"
     allowed_roles = ["*"]

     postgresql {
       connection_url = "postgresql://{{username}}:{{password}}@localhost:5432/postgres"
       password_authentication = ""
       username = "postgres"
       password_wo = tostring(ephemeral.vault_kv_secret_v2.db_secret.data.password)
       password_wo_version = 1
     }
   }
   ```

3. **Последнее средство: обычные ресурсы.**
   Используй обычный ресурс, записывающий чувствительные данные в состояние, только если
   ни один из вариантов выше недоступен, у ресурса нет write-only атрибута или эфемерной
   альтернативы, либо версия Terraform меньше 1.11.0.
