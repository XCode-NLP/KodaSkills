# Возможности блока и атрибуты обёртки

Используй этот файл, когда меняешь `supports` или когда оформление обёртки блока
ведёт себя неожиданно.

## Обязательные образцы

- в `edit()` используй `useBlockProps()`;
- в `save()` используй `useBlockProps.save()`.

Если блок динамический (отрисовка на PHP), используй:

- `get_block_wrapper_attributes()`.

Источники:

- https://developer.wordpress.org/block-editor/reference-guides/block-api/block-supports/
- https://developer.wordpress.org/reference/functions/get_block_wrapper_attributes/
