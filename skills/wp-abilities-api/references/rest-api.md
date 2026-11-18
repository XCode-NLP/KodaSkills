# Краткое руководство по REST API (`wp-abilities/v1`)

Abilities API публикует эндпоинты в пространстве имён REST:

- `wp-abilities/v1/abilities`
- `wp-abilities/v1/categories`

Контрольный список отладки:

- убедись, что маршрут существует по адресу `wp-json/wp-abilities/v1/...`;
- проверь, что возможность или категория есть в ответах REST;
- если их нет, проверь, что для этой возможности включён `meta.show_in_rest`.
