---
name: beget-s3
description: "Работа с объектным хранилищем Beget: бакеты, загрузка и выгрузка файлов, presigned-ссылки, резервные копии и обслуживание бакетов через MCP или CLI. Используй при задачах про S3 Beget, бакет, выгрузку или обмен файлами."
license: MIT
metadata:
  author: stufently
  source: https://github.com/stufently/beget-s3-mcp-ai-cli
---

# Beget S3

Сначала прочитай `beget-s3://config` и `beget-s3://capabilities`: инструменты зависят от уровней read/write/delete/admin, возможностей провайдера и файлового корня. Если операция не зарегистрирована, объясни нужную настройку владельцу.

Сначала прочитай capabilities: отключённые инструменты не вызывай. При bucket_create/bucket_delete/bucket_config:false создай бакет и управляй его настройками в панели провайдера. При presign:false не предлагай внешнюю подписанную ссылку как проверенный способ обмена.

Для поиска используй `s3_list_buckets`, `s3_list_objects` с токеном продолжения, `s3_head_object`, `s3_preview_object`. Инлайн get/put ограничены 256 КиБ; preview — 64 КиБ. Передавай большие байты через presigned URL, multipart или файловые инструменты. Не помещай большие файлы в контекст модели.

Перед удалением, перемещением, перезаписью, PUT-ссылкой, изменением политики или Object Lock опиши человеку эффект и получи согласие. Следуй политике confirm/elicit/block/allow; `confirm:true` отражает уже полученное согласие. При отказе не меняй политику ради повторной попытки. По умолчанию запись не перезаписывает существующую цель. Если conditional_writes выключен, запись по умолчанию отказывает до S3-запроса: для записи требуется явный overwrite:true после согласия человека; HEAD не заменяет атомарную защиту. Если conditional_delete выключен, move недоступен. Проверяй скоуп и у источника, и у цели.

Не выводи ключи или подпись presigned URL в журналы. Креды задаёт владелец через `beget-s3 auth set`; MCP-конфиги не содержат секретов. Файловые инструменты работают только с относительными путями внутри FILE_ROOT.

Регион подписи и эндпоинт выбираются из профиля; пул по умолчанию — ru1. Проверяй ресурс capabilities перед использованием versioning, CORS, политики, Object Lock или тегов. Официальная документация: https://beget.com/ru/kb/manual/obektnoe-hranilishche-s3-v-beget https://beget.com/ru/kb/faq/cloud/podklyuchenie-k-obektnomu-hranilishchu-s3-pri-pomoshchi-klientov-aws-cli-s3cmd-cyberduck-sdk https://beget.com/ru/cloud/storage. Цены и ограничения с verified:false требуют проверки; эмулятор не подтверждает совместимость облака.

Для соответствующего сценария прочитай:

- [Бэкап и восстановление](references/backup-restore.md).
- [Обмен файлом](references/share-file.md).
- [Минимальные права](references/least-privilege.md).
- [Объём и расходы](references/cost-hygiene.md).
- [Миграция](references/migration.md).
- [Инцидент](references/incident-response.md).
