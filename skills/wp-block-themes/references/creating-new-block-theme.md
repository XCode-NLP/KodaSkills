# Создание новой блочной темы

Используй этот файл, когда нужно создать новую блочную тему или перевести тему в
блочную структуру.

## Две практичные отправные точки

1. **Экспорт из окружения WP**
   - Используй официальный плагин «Create Block Theme», чтобы сформировать и
     экспортировать тему из редактора сайта.
   - Обычно он даёт структуру, соответствующую текущему поведению WordPress.

2. **Создай минимальную файловую структуру**
   - Создай директорию темы с файлами:
     - `style.css` (заголовок темы);
     - `theme.json` (глобальные настройки и стили);
     - `templates/index.html` (минимально рабочий шаблон);
     - `parts/header.html` и `parts/footer.html` (рекомендуется).

## Ссылки

- Плагин Create Block Theme:
  - https://wordpress.org/plugins/create-block-theme/
- Структура блочной темы:
  - https://developer.wordpress.org/themes/block-themes/theme-structure/
- Обязательные шаблоны:
  - https://developer.wordpress.org/themes/block-themes/templates-and-template-parts/

## Выбор версии theme.json (совместимость)

У `theme.json` есть версии схемы. Выбирай наибольшую версию, соответствующую
минимальной поддерживаемой версии WordPress.

Ссылки:

- Введение Theme Handbook:
  - https://developer.wordpress.org/themes/global-settings-and-styles/introduction-to-theme-json/
- Заметка о версии 3 theme.json:
  - https://make.wordpress.org/core/2024/06/19/theme-json-version-3/
