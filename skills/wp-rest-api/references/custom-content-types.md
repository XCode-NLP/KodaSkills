# Свои типы содержимого (кратко)

## Свои типы записей

- задай `show_in_rest => true` в `register_post_type()`, чтобы показать тип в
  `wp/v2`;
- используй `rest_base`, чтобы изменить часть адреса;
- при необходимости задай `rest_controller_class` (класс должен наследовать
  `WP_REST_Controller`).

## Свои таксономии

- задай `show_in_rest => true` в `register_taxonomy()`;
- используй `rest_base` и при необходимости `rest_controller_class` (по умолчанию
  `WP_REST_Terms_Controller`).

## Поддержка REST для существующих типов

- используй фильтры `register_post_type_args` или `register_taxonomy_args`, чтобы
  включить `show_in_rest` для типов, которые тебе не принадлежат.

## Ссылки обнаружения для своих контроллеров

- если используешь свой класс-контроллер, применяй фильтры `rest_route_for_post`
  или `rest_route_for_term`, чтобы связать объекты с маршрутами.
