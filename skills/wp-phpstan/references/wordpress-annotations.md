# Аннотации типов под WordPress

Эти образцы помогают PHPStan понимать код WordPress там, где поведение во время
выполнения и динамическая типизация затрудняют вывод типов.

## Типизация запросов REST API

PHPStan не может вывести допустимые параметры запроса из схем REST API. Указывай
явные подсказки типов для параметров запроса.

```php
/**
 * Обработать запрос REST API.
 *
 * @param WP_REST_Request $request Полные сведения о запросе.
 * @return WP_REST_Response|WP_Error Объект ответа при успехе, ошибка при сбое.
 *
 * @phpstan-param WP_REST_Request<array{
 *     post?: int,
 *     orderby?: string,
 *     meta_key?: string,
 *     per_page?: int,
 *     status?: array<string>
 * }> $request
 */
public function get_items( $request ) {
    $post_id = $request->get_param( 'post' );
    // Теперь PHPStan знает, что $post_id имеет тип int|null.
}
```

Для сложных схем определяй переиспользуемые типы.

```php
/**
 * @phpstan-type PostRequestParams array{
 *     title?: string,
 *     content?: string,
 *     status?: 'publish'|'draft'|'private',
 *     meta?: array<string, mixed>
 * }
 *
 * @phpstan-param WP_REST_Request<PostRequestParams> $request
 */
```

## Обратные вызовы хуков

```php
/**
 * Обработать смену статуса.
 *
 * @param string $new_status
 * @param string $old_status
 * @param WP_Post $post
 */
function handle_transition( string $new_status, string $old_status, WP_Post $post ): void {
    // ...
}

add_action( 'transition_post_status', 'handle_transition', 10, 3 );
```

## База данных и перебираемые значения

```php
/**
 * @return array<WP_Post> Объекты WP_Post.
 */
function get_custom_posts(): array {
    $posts = get_posts( [ 'post_type' => 'custom_type', 'numberposts' => -1 ] );
    return $posts;
}

/**
 * @return array<object{id: int, name: string}> Результаты запроса к базе.
 */
function get_user_data(): array {
    global $wpdb;

    $results = $wpdb->get_results( "SELECT id, name FROM users", OBJECT );
    return $results ?: [];
}
```

## Хуки (`apply_filters()` и `do_action()`)

Блоки документации у `apply_filters()` и `do_action()` проверяются. Тип первого
`@param` считается окончательным.

Если сторонний код возвращает для фильтра неверный тип, ошибка PHPStan ожидаема и
не требует защитного кода.

```php
/**
 * Позволяет влиять на форматирование цены.
 *
 * @param string $formatted Отформатированная цена.
 * @param float  $price     Исходная цена.
 * @param string $locale    Локаль для отображения цены.
 * @param string $currency  Символ валюты.
 */
return apply_filters( 'autoscout_vehicle_price_formatted', $formatted, $price, $locale, $currency );
```

## Формы аргументов Action Scheduler

```php
/**
 * Обработать запланированное письмо.
 *
 * @param array{user_id: int, email: string, data: array<string, mixed>} $args
 */
function process_scheduled_email( array $args ): void {
    $user_id = $args['user_id'];
    // ...
}

as_schedule_single_action(
    time() + 3600,
    'process_scheduled_email',
    [
        'user_id' => 123,
        'email' => 'user@example.com',
        'data' => [ 'key' => 'value' ],
    ]
);
```
