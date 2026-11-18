# Инструменты и тестирование

Используй этот файл, когда решаешь, какие команды запускать и что считать хорошей
проверкой.

## Частые наборы инструментов

- `@wordpress/scripts` для сборки, линтера и тестов:
  https://developer.wordpress.org/block-editor/reference-guides/packages/packages-scripts/
- `@wordpress/create-block` для создания заготовок блоков:
  https://developer.wordpress.org/block-editor/reference-guides/packages/packages-create-block/
- шаблон Interactivity API для `create-block`:
  https://www.npmjs.com/package/@wordpress/create-block-interactive-template
- `@wordpress/env` (wp-env) для локального окружения WordPress:
  https://developer.wordpress.org/block-editor/reference-guides/packages/packages-env/

## Контрольный список проверки

- `npm run build` (или аналог в репозитории) проходит;
- линтер JavaScript проходит (по правилам репозитория);
- сквозные тесты проходят, если они есть;
- вручную: вставить блок, сохранить запись, перезагрузить редактор и убедиться, что
  нет «невалидного блока».
