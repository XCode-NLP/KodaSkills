# Settings API (административные опции)

Используй этот файл, когда добавляешь страницы настроек или хранишь опции,
настраиваемые пользователем.

Основные API:

- `register_setting()`
- `add_settings_section()`
- `add_settings_field()`

Источники:

- обзор Settings API: https://developer.wordpress.org/plugins/settings/settings-api/
- регистрация настроек: https://developer.wordpress.org/plugins/settings/registration/
- поля настроек: https://developer.wordpress.org/plugins/settings/settings-fields/

Практические ограничения:

- используй `sanitize_callback` для проверки и очистки данных;
- проверяй права (обычно `manage_options`) для экранов настроек и сохранения;
- экранируй значения при выводе (`esc_attr`, `esc_html` и другие).
