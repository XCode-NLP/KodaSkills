# Шаблон вспомогательной функции делегирования

Когда ты решил, что делегирование — верная форма для возможности (то есть контроллер REST
в основе только читает данные, операция — чтение, а возможность выполняется преимущественно
в контекстах REST; о случае «нет, лучше выделить общий сервис» см.
`shared-core-service.md`), вынеси вспомогательную функцию
`delegate_to_rest_controller` вместо того, чтобы в каждом колбэке выполнения вручную
собирать, отправлять и разворачивать запрос. Здесь описан один рабочий вариант такой
функции, три проверки, нужные любой реализации, разворачивание двух форм ответа и случаи,
когда функцию лучше НЕ использовать. Подгоняй точную сигнатуру под свой плагин — проверки и
разворачивание важнее списка параметров.

Сначала прочитай `plugin-family-patterns.md`: точная форма функции зависит от того, как
устроен контроллер в основе (общий клиент API или отсутствие аргументов).

## Зачем нужна эта функция

Возможности чтения со списками обычно повторяют в каждом колбэке одни и те же четыре шага:

1. Проверить, что плагин инициализирован (класс есть, зависимости разрешены).
2. Собрать `WP_REST_Request` и перенести в него `$input` возможности как параметры.
3. Создать контроллер в основе и вызвать нужный метод.
4. Развернуть ответ (контроллеры возвращают либо сырой массив, либо `WP_REST_Response`).

Четыре возможности, умноженные на это повторение, — и обвязка занимает всё тело колбэка.
Выделение функции оставляет каждый колбэк выполнения в 3–4 строки, читающиеся как
псевдокод.

## Когда выделять

После того как появилась **вторая** возможность со списком. До добавления третьей вынеси
дублирующийся код из первых двух колбэков в приватную статическую функцию. Дальнейшие
возможности переводи на неё по мере добавления.

Если плагин выпускает всего одну-две возможности, пиши код на месте. Выгода функции
проявляется при трёх и более вызывающих.

## Форма функции

```php
/**
 * Delegate an ability's execute callback to a REST controller.
 *
 * Builds a WP_REST_Request from the ability's input, instantiates the
 * backing controller with the plugin's shared API client, invokes the
 * named method, and normalizes the return so callers always see
 * array|\WP_Error. Controllers in this plugin return either a
 * WP_REST_Response or a raw array; the helper unwraps both shapes.
 *
 * Not used by zero-arg abilities — those call their controller directly
 * so we don't synthesize a WP_REST_Request just to discard it.
 *
 * @param string     $controller_class Fully-qualified controller class (no leading backslash).
 * @param string     $method           Controller method to invoke on the built request.
 * @param string     $route            REST route string used when constructing WP_REST_Request.
 * @param array|null $input            Ability input; each key/value becomes a request param.
 * @param string     $http_method      HTTP method for WP_REST_Request. Defaults to 'GET'; writes pass 'POST'.
 * @return array|\WP_Error             Response payload as an array, or WP_Error on failure.
 */
private static function delegate_to_rest_controller(
    $controller_class,
    $method,
    $route,
    $input,
    $http_method = 'GET'
) {
    $fqcn = '\\' . $controller_class;

    // Guard 1: controller class is loaded.
    if ( ! class_exists( $fqcn ) ) {
        return new \WP_Error(
            '<plugin>_not_initialized',
            __( '<Plugin> is not initialized.', '<text-domain>' )
        );
    }

    // Guard 2: shared API client is available.
    $api_client = null;
    if ( class_exists( '\<Plugin_Main_Class>' ) && method_exists( '\<Plugin_Main_Class>', 'get_<client_accessor>' ) ) {
        $api_client = \<Plugin_Main_Class>::get_<client_accessor>();
    }
    if ( null === $api_client ) {
        return new \WP_Error(
            '<plugin>_not_initialized',
            __( '<Plugin> is not initialized.', '<text-domain>' )
        );
    }

    // Build the request.
    $request = new \WP_REST_Request( $http_method, $route );
    if ( null !== $input ) {
        foreach ( $input as $param => $value ) {
            $request->set_param( $param, $value );
        }
    }

    // Invoke + guard 3: WP_Error short-circuit + dual-shape unwrap.
    $controller = new $fqcn( $api_client );
    $response   = $controller->{$method}( $request );

    if ( is_wp_error( $response ) ) {
        return $response;
    }
    if ( $response instanceof \WP_REST_Response ) {
        $data = $response->get_data();
        return is_array( $data ) ? $data : [];
    }
    return is_array( $response ) ? $response : [];
}
```

Аргументы позиционные (не именованные) намеренно: функцию вызывают из каждой возможности со
списком, а именованные аргументы PHP 8 добавили бы визуальный шум. Порядок тоже намеренный:
контроллер, метод, маршрут, ввод, http_method (хвост с значением по умолчанию).

## Три проверки

### 1. `class_exists` для контроллера

Колбэки выполнения могут вызываться на сайтах, где классы плагина не загружены (тесты,
WP-CLI с ограниченной загрузкой, страницы админки с условной автозагрузкой). Проверка
дешёвая; без неё отсутствующий класс даёт фатальную ошибку.

Обрати внимание на `'\\' . $controller_class`: принимай имена классов контроллеров без
ведущей обратной косой черты (так читаемее в массивах конфигурации) и добавляй её, чтобы и
`class_exists`, и `new $fqcn(...)` разрешались от корня.

### 2. Проверка обязательной зависимости (клиента API) на null

Когда контроллер принимает общий клиент API аргументом конструктора, аксессор обычно
представляет собой `public static` метод главного класса плагина. Проверяй и `class_exists`
для класса плагина, и `method_exists` для аксессора, потому что при частичной загрузке может
отсутствовать и то и другое. Считай `null` от аксессора признаком «не инициализировано».

Пропуск этого аргумента даёт
`ArgumentCountError: Too few arguments to function <Controller>::__construct(), 0 passed` —
фатальную ошибку PHP. Стандартизованный код `<plugin>_not_initialized` описан в
`error-code-vocabulary.md`.

Когда контроллер не принимает аргументов конструктора, пропускай эту проверку целиком.
Когда он принимает только простые скаляры (например, строку типа записи), передавай их
через необязательный параметр `constructor_args` функции.

### 3. Короткое замыкание по `is_wp_error`

Прежде чем разворачивать ответ, проверь, не является ли он уже `WP_Error`. Многие
контроллеры возвращают `WP_Error` и при ошибках валидации, и при ошибках поставщика; эта
ошибка должна пройти насквозь без изменений, чтобы агент увидел код поставщика.

## Разворачивание двух форм ответа

```php
if ( $response instanceof \WP_REST_Response ) {
    $data = $response->get_data();
    return is_array( $data ) ? $data : [];
}
return is_array( $response ) ? $response : [];
```

Настоящие контроллеры REST WordPress возвращают либо:

- `WP_REST_Response` (результат `rest_ensure_response( ... )` или
  `new WP_REST_Response( ... )`), либо
- сырой массив (типично, когда контроллер делегирует внутреннему классу-обработчику
  запроса, который возвращает раскодированные данные транспорта напрямую).

Бывает и то и другое. Функция разворачивает `WP_REST_Response` через `get_data()` и
пропускает сырые массивы как есть. Приведение `is_array(...) ? ... : []` защищает от
возврата не-массива, который `output_schema` возможности всё равно отвергла бы дальше:
возврат `[]` завершается безопасно, а не утекает неожиданным типом.

## Когда функцию использовать НЕ нужно

Три категории возможностей обходят функцию и обращаются к источнику напрямую.

### Класс запроса можно вызвать без контроллера

Если единственная роль контроллера REST — перевести `WP_REST_Request` в вызов лежащего в
основе класса запроса (например,
`Things_Request::from_rest_request( $request )->execute()`) и он не добавляет валидацию,
логику прав или оркестрацию, обойди контроллер и вызови класс запроса напрямую:

```php
public static function execute_get_things( $input = null ) {
    if ( ! class_exists( '\My_Plugin\Things_Request' ) ) {
        return new \WP_Error( '<plugin>_not_initialized', __( '<Plugin> is not initialized.', '<text-domain>' ) );
    }

    $request = new \WP_REST_Request( 'GET', '/my-plugin/v1/things' );
    foreach ( (array) $input as $param => $value ) {
        $request->set_param( $param, $value );
    }

    $things_request = \My_Plugin\Things_Request::from_rest_request( $request );
    $rows           = $things_request->execute();

    return is_array( $rows ) ? $rows : [];
}
```

Объект `WP_REST_Request` существует только чтобы удовлетворить контракт параметра
`from_rest_request()`: его ничто не отправляет. Это самый короткий путь через уровни: без
создания контроллера, без побочных эффектов контроллера и (когда класс запроса вызывается
до любого трафика REST в жизненном цикле) без стоимости `rest_api_init`. Более широкое
обсуждение побочных эффектов пути REST и стоимости первой инициализации на холодных путях
см. в `shared-core-service.md`.

Компромисс реальный: обход контроллера обходит и всё, что контроллер делает. Если контроллер
выполняет валидацию, которой нет в классе запроса, или вызывает хук аудита, которого нет в
классе запроса, эта работа теряется на пути возможности. Используй эту форму, когда
контроллер действительно тонкая обёртка, а не когда он делает работу, которую хотелось бы
сохранить.

### Методы источника без аргументов

Если метод источника не принимает `WP_REST_Request`, не создавай запрос только чтобы его
отбросить. Вызывай метод напрямую:

```php
public static function execute_get_overview( $input = null ) {
    if ( ! class_exists( '\My_Plugin_REST_Overview_Controller' ) ) {
        return new \WP_Error( '<plugin>_not_initialized', __( '<Plugin> is not initialized.', '<text-domain>' ) );
    }

    $api_client = /* ... та же проверка аксессора ... */;
    if ( null === $api_client ) {
        return new \WP_Error( '<plugin>_not_initialized', __( '<Plugin> is not initialized.', '<text-domain>' ) );
    }

    $controller = new \My_Plugin_REST_Overview_Controller( $api_client );
    $response   = $controller->get_overview(); // Без аргумента $request.

    if ( is_wp_error( $response ) ) {
        return $response;
    }
    return is_array( $response ) ? $response : [];
}
```

### Возможности, использующие сервис вне REST

Если колбэк выполнения обращается к сервису напрямую (например,
`My_Plugin::get_account_service()->get_cached_account_data()`), а не к контроллеру REST,
оставайся на прямом пути. Возможность не опирается на REST, и функция добавила бы шаг
создания без пользы.

## Практическое правило

**Если метод источника принимает `WP_REST_Request`, а контроллер добавляет что-то помимо
делегирования классу запроса (валидацию, права, оркестрацию, нужные тебе побочные
эффекты), используй функцию. Если контроллер — тонкая обёртка над классом запроса, вызывай
класс запроса напрямую. В остальных случаях — прямой путь.**

## Образец преобразования — до и после

До выделения (на месте в колбэке выполнения):

```php
public static function execute_get_things( $input = null ) {
    if ( ! class_exists( '\My_Plugin_REST_Things_Controller' ) ) {
        return new \WP_Error( '<plugin>_not_initialized', __( '<Plugin> is not initialized.', '<text-domain>' ) );
    }
    $api_client = \My_Plugin::get_api_client();
    if ( ! $api_client ) {
        return new \WP_Error( '<plugin>_not_initialized', __( '<Plugin> is not initialized.', '<text-domain>' ) );
    }
    $request = new \WP_REST_Request( 'GET', '/my-plugin/v1/things' );
    foreach ( (array) $input as $param => $value ) {
        $request->set_param( $param, $value );
    }
    $controller = new \My_Plugin_REST_Things_Controller( $api_client );
    $response   = $controller->get_things( $request );
    // ... разворачивание ...
}
```

После выделения:

```php
public static function execute_get_things( $input = null ) {
    return self::delegate_to_rest_controller(
        'My_Plugin_REST_Things_Controller',
        'get_things',
        '/my-plugin/v1/things',
        is_array( $input ) ? $input : null
    );
}
```

Обрати внимание на `is_array( $input ) ? $input : null`: сигнатура функции — `?array`, и
`null` говорит ей собрать запрос вообще без параметров. Это важно, потому что Abilities API
иногда вызывает колбэк без объекта ввода.

## Связанные справочники

- `plugin-family-patterns.md` — выбор формы конструктора для функции.
- `error-code-vocabulary.md` — код `<plugin>_not_initialized` и его соседи.
- `input-schema-gotchas.md` — колбэкам возможностей со списками часто нужно перевести
  пагинацию `per_page` ДО вызова функции.
