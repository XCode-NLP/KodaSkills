# Внутренние блоки (вложенные)

Используй этот файл, когда твой блок содержит другие блоки (блоки-контейнеры).

## Канонические источники

- руководство по вложенным блокам: https://developer.wordpress.org/block-editor/how-to-guides/block-tutorial/nested-blocks-inner-blocks/
- пакет `@wordpress/block-editor`: https://developer.wordpress.org/block-editor/reference-guides/packages/packages-block-editor/
- возможности блоков: https://developer.wordpress.org/block-editor/reference-guides/block-api/block-supports/

## Практические образцы

- Редактор:
  - используй `useInnerBlocksProps( useBlockProps(), { ... } )`, чтобы объединить
    атрибуты обёртки с внутренними блоками;
  - применяй шаблоны и список разрешённых блоков, только когда есть ясная причина
    в удобстве использования (слишком строгие ограничения раздражают).
- Сохранение:
  - используй `useInnerBlocksProps.save( useBlockProps.save(), { ... } )`, если
    нужны атрибуты обёртки;
  - выводи вложенное содержимое через `<InnerBlocks.Content />`, где это уместно.

## Частые ловушки

- в блоке должен быть только один `InnerBlocks`;
- изменение структуры обёртки, содержащей внутренние блоки, может сделать
  существующее содержимое невалидным: предусмотри устаревшие версии и миграции;
- если нужно ограничить набор допустимых блоков, делай это осознанно и опиши
  причину.
