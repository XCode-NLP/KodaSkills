---
name: selectel-s3
description: "Работа с объектным хранилищем Selectel: бакеты, загрузка и выгрузка файлов, presigned-ссылки, резервные копии и обслуживание бакетов через MCP или CLI. Используй при задачах про S3 Selectel, бакет, выгрузку или обмен файлами."
license: MIT
metadata:
  author: stufently
  source: https://github.com/stufently/selectel-s3-mcp-ai-cli
  tags: [selectel, s3, хранилище, облако]
---

# Selectel S3

Сначала прочитай `selectel-s3://config` и `selectel-s3://capabilities`: инструменты зависят от уровней read/write/delete/admin, возможностей провайдера и файлового корня. Если операция не зарегистрирована, объясни нужную настройку владельцу.

Для поиска используй `s3_list_buckets`, `s3_list_objects` с токеном продолжения, `s3_head_object`, `s3_preview_object`. Инлайн get/put ограничены 256 КиБ; preview — 64 КиБ. Передавай большие байты через presigned URL, multipart или файловые инструменты. Не помещай большие файлы в контекст модели.

Перед удалением, перемещением, перезаписью, PUT-ссылкой, изменением политики или Object Lock опиши человеку эффект и получи согласие. Следуй политике confirm/elicit/block/allow; `confirm:true` отражает уже полученное согласие. При отказе не меняй политику ради повторной попытки. По умолчанию запись не перезаписывает существующую цель. Если conditional_writes выключен, запись по умолчанию отказывает до S3-запроса: для записи требуется явный overwrite:true после согласия человека; HEAD не заменяет атомарную защиту. Если conditional_delete выключен, move недоступен. Проверяй скоуп и у источника, и у цели.

Не выводи ключи или подпись presigned URL в журналы. Креды задаёт владелец через `selectel-s3 auth set`; MCP-конфиги не содержат секретов. Файловые инструменты работают только с относительными путями внутри FILE_ROOT.

Регион подписи и эндпоинт выбираются из профиля; пул по умолчанию — ru-1. Проверяй ресурс capabilities перед использованием versioning, CORS, политики, Object Lock или тегов. Официальная документация: https://docs.selectel.ru/api/object-storage-s3/ https://docs.selectel.ru/s3/manage/domains/ https://docs.selectel.ru/s3/about/limitations/ https://docs.selectel.ru/s3/about/payment/ https://docs.selectel.ru/s3/buckets/create-bucket/ https://docs.selectel.ru/s3/buckets/limits/. Цены и ограничения с verified:false требуют проверки; эмулятор не подтверждает совместимость облака.

Для соответствующего сценария прочитай:

- [Бэкап и восстановление](references/backup-restore.md).
- [Обмен файлом](references/share-file.md).
- [Минимальные права](references/least-privilege.md).
- [Объём и расходы](references/cost-hygiene.md).
- [Миграция](references/migration.md).
- [Инцидент](references/incident-response.md).
