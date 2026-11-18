# Шаблоны семейств плагинов

Этот файл описывает общую *механику* реализации: форму вызова, которой следуют колбэки
выполнения, передавая работу существующей бизнес-логике. Две формы достаточно
распространены в реальных плагинах WordPress, чтобы их назвать; какая подходит, определяется
тем, как устроен контроллер в основе, а не выбором, который ты делаешь заранее. Выбор всё
равно отражается на вспомогательной функции делегирования, тестах и кодах ошибок, поэтому
его стоит подтвердить пораньше.

Соглашения *регистрации*, специфичные для семейства (путь загрузчика, категория
возможностей, умолчания публикации через MCP, стиль префикса кодов ошибок), живут в
отдельных наложениях для семейств (например, наложение для расширений WooCommerce), а не
здесь. Применяй подходящее наложение до того, как создавать заготовку регистрации. Шаблоны
ниже должны оставаться переносимыми: они описывают, как колбэк выполнения общается с кодом в
основе, а не то, как должны выглядеть метаданные регистрации в твоём семействе плагинов.

Есть и третий вариант, лежащий *вне* этой дихотомии. Если у операции ещё нет общего класса
сервиса — или если можно к нему отрефакторить — выделение сервиса, который используют
возможность, контроллер REST и интерфейс, является умолчанием согласно
`shared-core-service.md`. Делегирование через существующий контроллер REST (любая из форм
ниже) — условное сокращение для малозначимых чтений, а не отправная точка. Подтверди, что
форма верна, прежде чем прибегать к одной из них.

## Форма: общий клиент API

Распространена в плагинах, которые обращаются к удалённому сервису (Stripe, собственный
SaaS, внешний API). Плагин инициализирует один клиент API, открывает его через статический
аксессор в главном классе плагина, и каждый контроллер REST принимает этот клиент
аргументом конструктора.

### Как определить

```bash
# Посмотреть сигнатуру __construct контроллера REST в основе.
grep -n "public function __construct" <path/to/rest-controller.php>
```

Если конструктор принимает обязательный типизированный аргумент (например,
`My_Plugin_API_Client $api_client`), это форма общего клиента API. Подтверди, что у плагина
есть центральный аксессор:

```bash
grep -rn "get_api_client\|get_.*_api_client\|get_service" <path/to/plugin/main-class.php>
```

Ты ищешь `public static function get_<something>()`, возвращающую общий клиент.

### Минимальный каркас

```php
<?php
namespace My_Plugin\Abilities;

class Abilities_Registrar {

    const CATEGORY_SLUG = 'my-plugin';

    public static function init() {
        add_action( 'wp_abilities_api_categories_init', [ __CLASS__, 'register_category' ] );
        add_action( 'wp_abilities_api_init', [ __CLASS__, 'register_abilities' ] );
    }

    public static function register_abilities() {
        wp_register_ability(
            'my-plugin/get-things',
            [
                'label'               => __( 'Get things', 'my-plugin' ),
                'description'         => __( 'List things with filters.', 'my-plugin' ),
                'category'            => self::CATEGORY_SLUG,
                'input_schema'        => [ /* ... */ ],
                'execute_callback'    => [ __CLASS__, 'execute_get_things' ],
                'permission_callback' => [ __CLASS__, 'current_user_has_capability' ],
                'meta'                => [
                    'annotations'  => [ 'readonly' => true, 'destructive' => false, 'idempotent' => true ],
                    'show_in_rest' => true,
                ],
            ]
        );
    }

    public static function execute_get_things( $input = null ) {
        return self::delegate_to_rest_controller(
            'My_Plugin_REST_Things_Controller',
            'get_things',
            '/my-plugin/v1/things',
            is_array( $input ) ? $input : null
        );
    }

    private static function delegate_to_rest_controller( $controller_class, $method, $route, $input, $http_method = 'GET' ) {
        $fqcn = '\\' . $controller_class;
        if ( ! class_exists( $fqcn ) ) {
            return new \WP_Error( 'my_plugin_not_initialized', __( 'My Plugin is not initialized.', 'my-plugin' ) );
        }

        // Особенность формы: получаем общий клиент API и проверяем на null.
        $api_client = null;
        if ( class_exists( '\My_Plugin' ) && method_exists( '\My_Plugin', 'get_api_client' ) ) {
            $api_client = \My_Plugin::get_api_client();
        }
        if ( null === $api_client ) {
            return new \WP_Error( 'my_plugin_not_initialized', __( 'My Plugin is not initialized.', 'my-plugin' ) );
        }

        $request = new \WP_REST_Request( $http_method, $route );
        if ( is_array( $input ) ) {
            foreach ( $input as $param => $value ) {
                $request->set_param( $param, $value );
            }
        }

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
}
```

### Что это значит для тестов

- **Подменам при инициализации нужен клиент API.** Модульные тесты, создающие контроллеры,
  должны передавать замоканный или заглушечный клиент, иначе конструктор падает с
  `ArgumentCountError: Too few arguments`.
- **Путь ошибки «не инициализировано» достижим и должен быть покрыт.** Один модульный тест
  должен подменить аксессор так, чтобы он вернул null, и проверить, что возможность
  возвращает `<plugin>_not_initialized`. Это частая ошибка при частичной загрузке (WP-CLI с
  ограниченной загрузкой, тестовые стенды, страницы админки с условной автозагрузкой).
- **Интеграционным тестам нужен реальный или поддельный HTTP.** Контроллер в основе
  обратится к внешнему сервису, если клиент API не замокан, поэтому интеграционные стенды
  обычно направляют трафик через поддельный транспорт.

Разобранный пример: плагин, работающий с внешним SaaS или внешним HTTP-сервисом, обычно
следует этому шаблону. Главный класс плагина открывает клиент API через статический аксессор
(например, `Plugin_Main::get_api_client()`); контроллеры REST наследуют базовый класс, чей
конструктор принимает этот клиент типизированным аргументом; регистратор возможностей
получает клиент через тот же аксессор перед созданием контроллеров.

## Форма: контроллеры без аргументов

Распространена в плагинах и пакетах, которые в основном делегируют механизмам ядра WordPress
(пользовательские типы записей, опции, метаданные) и не держат единого общего клиента API.
Контроллеры создаются без графа зависимостей.

### Как определить

```bash
grep -n "public function __construct" <path/to/rest-controller.php>
```

Если конструктор не принимает обязательных аргументов или принимает только простые скаляры,
которые можно зашить в месте вызова возможности (например, строку типа записи), это форма
без аргументов.

Также проверь главный класс инициализации плагина на отсутствие синглтонного аксессора API:
если его нет, форма без аргументов — честный выбор.

### Минимальный каркас

```php
<?php
namespace My_Plugin\Abilities;

class Abilities_Registrar {

    const CATEGORY_SLUG = 'my-plugin';

    public static function init() {
        add_action( 'wp_abilities_api_categories_init', [ __CLASS__, 'register_category' ] );
        add_action( 'wp_abilities_api_init', [ __CLASS__, 'register_abilities' ] );
    }

    public static function register_abilities() {
        wp_register_ability(
            'my-plugin/get-things',
            [
                /* ... */
                'execute_callback' => [ __CLASS__, 'execute_get_things' ],
                /* ... */
            ]
        );
    }

    public static function execute_get_things( $input = null ) {
        $input    = is_array( $input ) ? $input : [];
        $endpoint = new \My_Plugin_Things_Endpoint();
        $request  = new \WP_REST_Request( 'GET', '/my-plugin/v1/things' );

        foreach ( [ 'page', 'per_page', 'status', 'search' ] as $key ) {
            if ( isset( $input[ $key ] ) ) {
                $request->set_param( $key, $input[ $key ] );
            }
        }

        $response = $endpoint->get_items( $request );
        if ( is_wp_error( $response ) ) {
            return $response;
        }
        return $response instanceof \WP_REST_Response ? $response->get_data() : $response;
    }
}
```

Вспомогательная функция не нужна: шаг создания — одна строка, и код на месте остаётся
читаемым. Если ты всё же выделяешь функцию, она принимает параметр `constructor_args`,
потому что класс контроллера не постоянен для разных возможностей:

```php
/**
 * @param string     $controller_class Fully-qualified controller class.
 * @param string     $method           Method to invoke on the request.
 * @param string     $route            REST route used when constructing WP_REST_Request.
 * @param array|null $input            Ability input (or null).
 * @param string     $http_method      HTTP method. Defaults to 'GET'.
 * @param array      $constructor_args Optional scalar args for the controller's constructor.
 * @return array|\WP_Error
 */
private static function delegate_to_rest_controller(
    $controller_class,
    $method,
    $route,
    $input,
    $http_method = 'GET',
    $constructor_args = array()
) {
    /* ... */
}
```

Форма возврата `array|\WP_Error` указана в phpDoc; сама сигнатура функции остаётся без типа
возврата, чтобы фрагмент разбирался на PHP 7.2+.

Полную сигнатуру функции и проверки см. в `delegate-helper-pattern.md`.

### Что это значит для тестов

- **Мок клиента API не нужен.** Модульные тесты создают регистратор возможностей напрямую и
  вызывают `execute_*` с массивами ввода.
- **Когда возможно, тестируй на уровне `wp_get_ability()`.** При контроллерах без аргументов
  источник часто находится на территории ядра WordPress (например, пользовательские типы
  записей), поэтому интеграционные тесты могут пройти весь конвейер без поддельного
  транспорта.
- **Отказ `<plugin>_not_initialized` менее частый.** Он всё ещё существует: если пакет не
  загружен, `class_exists` для контроллера в основе тоже не проходит, но поверхность меньше.

Разобранный пример: плагин, чьи контроллеры REST оборачивают пользовательский тип записи,
таксономию, опцию или метаданные, обычно следует этому шаблону. Каждый колбэк выполнения
создаёт контроллер на месте (например, `new My_CPT_Endpoint( 'my_cpt' )`), передавая нужный
скаляр (слаг типа записи, имя таксономии). Общей функции в регистраторе нет: шаг создания
достаточно мал, чтобы писать его на месте.

## Смешанные случаи

Один плагин может законно использовать оба шаблона для разных возможностей:

- возможность в форме общего клиента API — для контроллеров, обращающихся к внешнему
  сервису;
- возможность в форме без аргументов — для контроллеров, работающих только с ядром WP
  (например, эндпоинт настроек на основе типа записи в том же плагине).

Если так случилось, функция из `delegate-helper-pattern.md` поддержит оба варианта через
необязательный `constructor_args`, но сопротивляйся соблазну усложнять, пока у тебя не
появится хотя бы две возможности без аргументов, которые будут делить функцию.

## Антишаблон — изобретать клиент API, которого нет

Не вводи фиктивный общий клиент API только чтобы подогнать плагин под форму с общим
клиентом. Если плагин действительно не хранит состояния и работает на пользовательских типах
записей, честный ответ — создавать контроллер на месте. Функция — это обвязка, которая
окупается, когда у тебя 4+ возможности используют общий поток «собрать запрос → создать
контроллер → развернуть ответ»; до этого код на месте читается и проверяется быстрее.

## Как выбрать быстро

| Признак | Вероятный шаблон |
|---|---|
| `__construct` контроллера в основе принимает объект вроде клиента API | A |
| В плагине есть статический аксессор `Plugin::get_*_client()` | A |
| Плагин обращается к внешнему SaaS или внешнему HTTP-сервису | A |
| `__construct` контроллера в основе без аргументов или только со скалярами | B |
| В основе — обёртка над типом записи, опциями или метаданными | B |
| Поверхность REST плагина оборачивает типы записей, таксономии, опции или метаданные ядра WP | B |
