# Круговая проверка прав

Проверь, что зарегистрированный `permission_callback` каждой возможности действительно
опирается на реальное право — статически (осмотром исходника) и, в режиме выполнения, прогоном
барьера в контекстах неаутентифицированного пользователя, подписчика и администратора.

## Предыстория — что `permission_callback` реально получает

Когда возможность вызывают, зарегистрированный `permission_callback` вызывается через
`WP_Ability::check_permissions( $input )`, который передаёт управление
`WP_Ability::invoke_callback( $callback, $input )` (оба определены в `class-wp-ability.php`
ядра WordPress).

Контракт `invoke_callback`:

- Если возможность объявляет непустую `input_schema`, колбэк вызывается с одним позиционным
  аргументом: проверенным значением `$input` (тем, что дал корневой тип схемы — массив,
  строка, целое, логическое значение и т.д.).
- Если `input_schema` пуста или отсутствует, колбэк вызывается **без аргументов**.

В частности, колбэк **никогда не получает `WP_REST_Request`**, даже когда возможность
достигается через мост REST. Мост разворачивает запрос, выполняет проверку схемы и передаёт
вниз проверенное значение. Колбэки прав, построенные вокруг шаблонов `WP_REST_Request`
(например, `$request->get_method()`), не могут работать как есть, если скопированы из
контроллера REST: помечай любое такое использование как статический FAIL.

## Статическая проверка — отнеси каждый колбэк к форме

Прочитай тело `permission_callback` каждой возможности и отнеси его к форме:

| Форма | Тело | Результат | Замечания |
|---|---|---|---|
| A | `return current_user_can( 'cap' );` | OK | Предпочтительно. Запиши разрешённое право. |
| B | Ветвление по `$input` — разные права для разных форм | OK с замечанием | Два разных действия пользователя обычно требуют двух возможностей, каждая со своей формой A. См. `../../wp-abilities-api/references/domain-vs-projection.md`. |
| B-плохо | Ветвление по `$request->get_method()` или другим вызовам `WP_REST_Request` | FAIL | Аргумент — проверенное значение ввода, а не объект запроса. Почти всегда это копия из контроллера REST без перевода. |
| C | `'__return_true'` | WARN | Намеренно публичная возможность. Опиши причину в коде или в массиве `risks` документа аудита. |
| D | Делегирует вспомогательной функции, которая разрешается в `current_user_can(...)` | OK | Проследи функцию. Если она безусловно возвращает `true`, считай это формой C. |
| E | `return true;` (литерал) | FAIL | Функционально форма C, но её труднее найти grep-ом. Замени на `'__return_true'` или добавь реальную проверку права. |
| F | `return is_user_logged_in();` | WARN | Разрешает вызов любому аутентифицированному пользователю, включая подписчиков. Редко бывает намеренно. Опиши или ужесточи. |

Запиши для каждой возможности: `(shape, resolved_cap)`. Любая форма B-плохо или E →
статический FAIL. Формы C и F → WARN. Формы A, B, D → OK.

## Проверка во время выполнения

Прогони барьер в трёх контекстах пользователя через `WP_Ability::check_permissions( $input )`.

`check_permissions()` принимает необязательное значение ввода и передаёт его в
зарегистрированный `permission_callback`. Колбэки формы A (`return current_user_can('cap')`)
его не читают. Колбэкам формы B, ветвящимся по `$input` (то самое замечание, которое отмечает
статическая проверка), нужно представительное значение, чтобы прогнать настоящий барьер; иначе
они получат `null`, и результат круговой проверки будет вводить в заблуждение. Фрагмент ниже
передаёт `array()` — минимальный безопасный ввод для схем с типом «объект». Для возможностей с
корневой схемой другого типа подставь представительное значение объявленного корневого типа.

```bash
<env-cli> wp --user=admin eval '
$ability = wp_get_ability( "<plugin>/<ability-name>" );
if ( ! $ability ) {
    echo "ability not registered" . PHP_EOL;
    exit( 1 );
}

$input   = array(); // representative input; substitute for non-object root schemas.
$results = array();

// Unauthenticated.
wp_set_current_user( 0 );
$results["anon"] = $ability->check_permissions( $input );

// Subscriber (create a fresh user).
$sub_login = "verify_sub_" . time();
$sub_id    = wp_create_user( $sub_login, "x", $sub_login . "@example.com" );
if ( ! is_wp_error( $sub_id ) ) {
    $sub_user = get_user_by( "id", $sub_id );
    $sub_user->set_role( "subscriber" );
    wp_set_current_user( $sub_id );
    $results["subscriber"] = $ability->check_permissions( $input );
}

// Admin.
wp_set_current_user( 1 );
$results["admin"] = $ability->check_permissions( $input );

foreach ( $results as $context => $result ) {
    if ( true === $result ) {
        $printable = "true";
    } elseif ( is_wp_error( $result ) ) {
        $printable = "WP_Error(" . $result->get_error_code() . ")";
    } else {
        $printable = var_export( $result, true );
    }
    echo $context . "=" . $printable . PHP_EOL;
}

// Cleanup the test subscriber so repeated harness runs don't accumulate users
// on shared dev environments. Already running as admin (line above), so the
// caller has the delete_users capability. On multisite, wp_delete_user() only
// removes the user from the current site membership — wpmu_delete_user() in
// wp-admin/includes/ms.php is the network-wide delete.
if ( isset( $sub_id ) && ! is_wp_error( $sub_id ) ) {
    if ( is_multisite() ) {
        require_once ABSPATH . "wp-admin/includes/ms.php";
        wpmu_delete_user( $sub_id );
    } else {
        require_once ABSPATH . "wp-admin/includes/user.php";
        wp_delete_user( $sub_id );
    }
}
'
```

Как толковать результат:

- `check_permissions()` возвращает `bool|WP_Error`. Считай `true` *разрешением*; `false` и
  любой `WP_Error` — *отказом*.
- `WP_Error` с кодом `ability_invalid_permission_callback` означает, что регистрация не дала
  допустимую вызываемую функцию, — жёсткий FAIL.
- `WP_Error` с кодом `ability_callback_exception` означает, что колбэк выбросил исключение, —
  жёсткий FAIL; сохрани исходное сообщение.

Ожидаемое для обычной (непубличной) возможности:

```
anon=false
subscriber=false
admin=true
```

Ожидаемое для намеренно публичной возможности (форма C):

```
anon=true
subscriber=true
admin=true
```

Любое отклонение → FAIL. Частые причины: ссылка на право, которого у администратора нет,
ошибка в колбэке или слишком мягкие права (форма E или F там, где должна была быть форма A).

## Сверка с аудитом

Если передан документ аудита, его `capability_gate` (или `permission.resolves_to` каждой
возможности) объявляет, каким должен быть барьер. Сравни:

- аудит и регистрация разрешаются в одно право → OK;
- аудит и регистрация расходятся → FAIL. Либо аудит неверен, либо регистрация разошлась;
- аудит объявляет составной барьер `{read, write}`, а регистрация использует форму B с обоими
  правами → OK;
- аудит объявляет составной барьер, а регистрация использует форму A (одно право) → FAIL.
  Пути записи унаследуют барьер чтения (или наоборот), что даёт недостаточную или избыточную
  авторизацию.

Механику прослеживания см. в
`../../wp-abilities-audit/references/capability-gate-tracing.md`; этот навык повторяет то же
прослеживание и сравнивает результаты.

## Формат вывода

```markdown
## Permission gates

| Ability | Shape | Resolved cap(s) | anon | subscriber | admin | Audit match |
|---|---|---|---|---|---|---|
| <ability> | A | manage_options | false | false | true | OK |
| <ability> | B | edit_posts (read), delete_posts (destructive) | false | false | true | OK |
| <ability> | C | __return_true (public) | true | true | true | WARN |
| <ability> | E | (literal true) | true | true | true | FAIL |
```

## Оговорки режима только статической проверки

Без режима выполнения заполняются только столбцы осмотра исходника:

| Ability | Shape | Resolved cap(s) | Audit match |
|---|---|---|---|

Столбцы круговой проверки опускаются, а не угадываются. Отметь в заголовке раздела:
`Permission gates (static inspection only)`.
