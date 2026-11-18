# Схема и проверка аргументов (кратко)

## Схема JSON в WordPress

- REST API использует схему JSON (подмножество черновика 4) для описания ресурсов и
  аргументов;
- задавай схему через `get_item_schema()` в контроллерах или обратные вызовы
  `schema` в маршрутах;
- схема даёт обнаружение (`OPTIONS`) и проверку.

## Проверка и очистка

- используй `rest_validate_value_from_schema( $value, $schema )`, затем
  `rest_sanitize_value_from_schema( $value, $schema )`;
- если переопределяешь `sanitize_callback`, встроенная проверка по схеме не
  выполнится; чтобы её сохранить, используй `rest_validate_request_arg`;
- `WP_REST_Controller::get_endpoint_args_for_item_schema()` подключает проверку
  автоматически.

## Кэширование схемы

- кэшируй сгенерированную схему в экземпляре контроллера (`$this->schema`), чтобы
  не пересчитывать её.

## Форматы и типы

- частые форматы: `date-time`, `uri`, `email`, `ip`, `uuid`, `hex-color`;
- для типов `array` и `object` нужно описывать схемы `items` и `properties`.
