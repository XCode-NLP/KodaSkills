# Активация, деактивация, удаление

Используй этот файл для изменений жизненного цикла и очистки данных.

## Хуки активации и деактивации

- `register_activation_hook( __FILE__, 'callback' )`
- `register_deactivation_hook( __FILE__, 'callback' )`

Ограничения:

- эти хуки нужно регистрировать на верхнем уровне, а не внутри других хуков;
- если сбрасываешь правила перезаписи, сначала убедись, что правила
  зарегистрированы (часто через общую функцию, вызываемую и на `init`, и при
  активации).

Источник:

- https://developer.wordpress.org/plugins/plugin-basics/activation-deactivation-hooks/

## Удаление

Предпочтительные подходы:

- `uninstall.php` (выполняется только при удалении);
- `register_uninstall_hook()`.

Ограничения:

- проверь `WP_UNINSTALL_PLUGIN` перед разрушительной очисткой.

Источник:

- https://developer.wordpress.org/plugins/plugin-basics/uninstall-methods/
