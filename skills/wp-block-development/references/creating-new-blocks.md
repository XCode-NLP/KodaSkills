# Создание новых блоков (заготовка)

Используй этот файл, когда создаёшь новый блок или плагин блока с нуля.

## Предпочтительный путь: `@wordpress/create-block`

`@wordpress/create-block` создаёт современную заготовку блока, которая обычно
следует текущим лучшим практикам.

Что стоит решить сразу:

- TypeScript или JavaScript;
- статический или динамический блок (`render.php` и отрисовка на сервере);
- должен ли блок быть интерактивным на лицевой части.

Каноническая документация:

- https://developer.wordpress.org/block-editor/reference-guides/packages/packages-create-block/

## Самые современные интерактивные блоки

Для современного интерактивного блока предпочитай официальный шаблон Interactivity
API:

- шаблон: `@wordpress/create-block-interactive-template`.

Этот шаблон рассчитан на сочетание:

- директив Interactivity API (`data-wp-*`);
- скриптов лицевой части на модулях (`viewScriptModule`);
- отрисовки на сервере (`render.php`).

Источники:

- https://developer.wordpress.org/block-editor/reference-guides/packages/packages-create-block/
- https://make.wordpress.org/core/2024/03/04/a-first-look-at-the-interactivity-api-in-wordpress-6-5/

## Ручной путь (когда заготовку создать нельзя)

Если запустить `create-block` нельзя (нет инструментов Node или сеть ограничена):

1. Создай место в плагине или теме, которое будет регистрировать блок.
2. Создай каталог блока с корректным `block.json`.
3. Зарегистрируй блок через `register_block_type_from_metadata()` в PHP.
4. Добавь JavaScript редактора и, при необходимости, ресурсы лицевой части.

Затем следуй остальным разделам навыка `wp-block-development`: метаданные,
регистрация, сериализация.
