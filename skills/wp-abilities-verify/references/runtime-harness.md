# Стенд режима выполнения

Процедура режима выполнения. Всё, что делает статический режим, плюс шесть канонических
проверок, которым нужен живой вызов `wp_get_abilities()`.

Статический режим ловит структурные проблемы (ложь в аннотациях, провал линтов схем,
несовпадения с аудитом). Режим выполнения ловит тот класс ошибок, который проявляется только
против загруженного WordPress: отсутствующие аргументы конструктора, проблемы порядка
инициализации, пути валидатора схемы, отказы круговой проверки прав и нарушения
идемпотентности на уровне байтов ответа.

## Правило стенда: остановись на первой фатальной ошибке

Если любой шаг ниже даёт фатальную ошибку PHP, ОСТАНОВИСЬ. Дальнейшие шаги не дадут осмысленного
вывода. Зафиксируй сбой, эскалируй исполнителю плагина для исправления, затем повтори прогон с
шага 1.

Возврат `WP_Error` допустим: любая ошибка с префиксом `<plugin>_*` или префиксом поставщика
означает, что колбэк выполнения аккуратно обработал путь ошибки. Блокируют только фатальные
ошибки PHP.

## Шаг 0 — определи команду запуска окружения

Прочитай `AGENTS.md` плагина, чтобы найти каноническую команду запуска окружения. НЕ считай,
что `npm run wp-env start` работает в любом плагине. Частые варианты, встречающиеся в реальных
деревьях плагинов:

- `npm run wp-env start` — проекты на `@wordpress/env` с добавленным в репозиторий
  `.wp-env.json`;
- `npx wp-env start` — проекты на `@wordpress/env` без собственной обёртки npm-скрипта;
- `composer install && composer test-php --setup-only` — локальная для пакета инициализация
  тестов, которая не ставит полный WordPress;
- `docker compose up -d` — собственные стеки разработки на Docker для плагина.

У семейств плагинов со своими инструментами разработки будет своя команда запуска в
`AGENTS.md`; следуй ей, как описано.

Если `AGENTS.md` её не описывает, спроси пользователя, а не угадывай. Запиши команду запуска
окружения и соответствующее обращение к wp-cli (например, `npx wp-env run cli wp`) и используй
их единообразно до конца стенда.

В этом файле `<env-cli>` — сокращение для того обращения к wp-cli, которое использует плагин.

## Шаг 1 — подними окружение и проверь basics

```bash
<env-up-command>
<env-cli> wp core version
<env-cli> wp plugin list --status=active
<env-cli> wp eval 'var_export( function_exists( "wp_get_abilities" ) );'
```

Подтверди:

- версия WordPress >= 6.9 (Abilities API доступен в ядре);
- проверяемый плагин активен;
- `wp_get_abilities` существует (истина при WP >= 6.9, иначе должен быть активен плагин или
  пакет с Abilities API).

Любой ответ «нет» останавливает стенд.

## Проверка 1 — имена возможностей совпадают с ожидаемым по исходникам списком

Перечисли возможности во время выполнения и сравни со статической описью из
`static-enumeration.md`:

```bash
<env-cli> wp --user=admin eval '
$names = array_filter(
    array_keys( (array) wp_get_abilities() ),
    function ( $n ) {
        return strpos( $n, "<plugin-slug>/" ) === 0;
    }
);
sort( $names );
echo "count=" . count( $names ) . PHP_EOL;
echo implode( PHP_EOL, $names ) . PHP_EOL;
'
```

Сравни со статической описью:

- в исходниках возможность есть, во время выполнения нет → FAIL. Хук регистрации не
  срабатывает; проверь момент вызова хука инициализации и активацию плагина.
- во время выполнения возможность есть, в исходниках нет → WARN. Динамический путь регистрации,
  который перечислитель не смог проследить. Опиши, но не блокируй.
- количества совпадают → OK.

## Проверка 2 — аннотации читаются такими, какими объявлены

```bash
<env-cli> wp --user=admin eval '
$names = array_filter(
    array_keys( (array) wp_get_abilities() ),
    function ( $n ) {
        return strpos( $n, "<plugin-slug>/" ) === 0;
    }
);
sort( $names );
foreach ( $names as $name ) {
    $a = wp_get_ability( $name );
    $m = $a->get_meta();
    printf(
        "%s | readonly=%s | destructive=%s | idempotent=%s | category=%s" . PHP_EOL,
        $name,
        var_export( $m["annotations"]["readonly"], true ),
        var_export( $m["annotations"]["destructive"], true ),
        var_export( $m["annotations"]["idempotent"], true ),
        $a->get_category()
    );
}
'
```

Сверь каждую аннотацию с объявленным значением в аудите (если аудит передан) И с объявленным
значением в статической описи. Несовпадение по любой оси → FAIL.

Эта проверка дополняет статическую враждебную проверку из `annotation-correctness.md`:
статическая проверяет фактическое поведение колбэка, а проверка во время выполнения — то, во
что разрешился хук регистрации при загрузке. Обе должны совпадать, чтобы аннотациям можно было
доверять.

## Проверка 3 — `execute()` каждой возможности чтения ведёт себя так, как обещает контракт

Два уровня проверки. Дымовой уровень ловит регрессии инициализации и грубые ошибки; уровень
высокой достоверности действительно прогоняет возможность против той формы данных, которую она
увидит в работе. Запускай оба, когда документ аудита содержит `seed_data_needs`; когда не
содержит, запускай только дымовой уровень.

### Уровень 1 — дымовое выполнение (синтетический ввод)

Подтверди, что каждое чтение возвращает `OK` или `WP_Error` из словаря. Ловит фатальные ошибки
PHP, незапущенные сервисы, отказы регистрации.

```bash
<env-cli> wp --user=admin eval '
$reads = array(
    "<plugin-slug>/<read-ability-1>",
    "<plugin-slug>/<read-ability-2>",
    // ...
);
foreach ( $reads as $name ) {
    $r = wp_get_ability( $name )->execute();
    echo $name . ": " . ( is_wp_error( $r ) ? "WP_Error(" . $r->get_error_code() . ")" : "OK" ) . PHP_EOL;
}
'
```

Допустимые исходы:

- `OK` — возможность вернулась без ошибки;
- `WP_Error(<plugin>_not_initialized)` — сработала защита инициализации (например, сервис не
  запущен). Нормальный путь ошибки;
- `WP_Error(<plugin>_<resource>_data_unavailable)` — временная ошибка бэкенда. Допустимо;
- `WP_Error(<upstream_code>)` — прошла ошибка стороннего поставщика. Опиши, не блокируй.

Недопустимые:

- фатальная ошибка PHP → останови стенд;
- `WP_Error` с кодом вне словаря → WARN. Сверься с
  `../../wp-abilities-api/references/error-code-vocabulary.md`.

Возможности с обязательным вводом вызываются отдельно с синтетическим, но правдоподобным
значением:

```bash
<env-cli> wp --user=admin eval '
$r = wp_get_ability( "<plugin>/<ability-with-required-input>" )
    ->execute( array( "<field>" => "<synthetic-id>" ) );
echo "<ability>: " . ( is_wp_error( $r ) ? "WP_Error(" . $r->get_error_code() . ")" : "OK" ) . PHP_EOL;
'
```

Синтетический идентификатор на свежей установке обычно вызывает
`<plugin>_<resource>_data_unavailable` или эквивалентный код поставщика. Для уровня 1 допустимо
и то и другое: это значит «возможность отработала чисто, источник сообщил об отсутствии данных»,
что и есть дымовой сигнал.

### Уровень 2 — проверка высокой достоверности (представительные засеянные данные)

Синтетический ввод ловит фатальные и грубые ошибки. Он НЕ ловит случаи, когда неверный
идентификатор возвращает не ту запись, кэшированные сторожевые значения выдаются вместо свежих
данных, барьер прав выглядит верным на синтетическом идентификаторе, но не на реальном,
отфильтрованные подписи расходятся с заявлением без фильтра, отсутствующие права проявляются
только когда в области видимости реальная запись, или появляется расхождение в подготовленном
выводе (новое поле, добавленное в контроллер, которое возможность наследует и теперь
утекает). Это те режимы отказа, которые важны, и они проявляются только когда возможность
работает с той формой данных, которую увидит в работе.

Для каждой возможности, чья запись в аудите объявляет непустой `seed_data_needs`, засей
окружение согласно этому полю, затем вызови возможность с представительным вводом (реальный
идентификатор, реальный слаг, а не синтетическая заглушка) и проверь форму вывода И контракт
приватности:

```bash
<env-cli> wp --user=admin eval '
// Seed once at the top of the harness run, per the audit doc:
// e.g. wp post create, wp user create, wp option update, factory helpers.

$ability = wp_get_ability( "<plugin>/<read-ability>" );
$result  = $ability->execute( array( "<field>" => "<real-id-from-the-seeded-data>" ) );

if ( is_wp_error( $result ) ) {
    echo "FAIL: " . $result->get_error_code() . PHP_EOL;
    exit;
}

// Assert the documented output shape — keys present, types correct.
$expected_keys = array( "id", "label", "status" );  // from the ability schema or audit return_type
foreach ( $expected_keys as $k ) {
    if ( ! array_key_exists( $k, (array) $result ) ) {
        echo "FAIL: missing output key " . $k . PHP_EOL;
        exit;
    }
}

// Assert the privacy contract: sensitive fields the contract does NOT
// promise must not appear (e.g. full PAN, full bank account, raw token,
// internal-only debug fields).
$forbidden_keys = array( "full_pan", "card_number", "bank_account_number", "iban" );
foreach ( $forbidden_keys as $k ) {
    if ( array_key_exists( $k, (array) $result ) ) {
        echo "FAIL: privacy leak — " . $k . " present in output." . PHP_EOL;
        exit;
    }
}

echo "PASS: shape OK, privacy OK." . PHP_EOL;
'
```

Подгоняй `$expected_keys` и `$forbidden_keys` под каждую возможность. Поле `return_type` в
документе аудита подсказывает форму; ключи приватности зависят от предметной области плагина.
Для плагинов семейства платежей канонический запрещённый набор — полные номера карт, номера
банковских счетов и сырые токены; другие семейства подставляют своё. Контрактные тесты в дереве
плагина (`test-the-public-contract.md` из наложения для расширений WooCommerce) — долговременный
дом для этих утверждений в каждом прогоне CI; эта проверка уровня 2 — разовый прогон стенда,
дающий артефакт для PR.

Когда документ аудита объявляет `seed_data_needs: null`, уровень 2 пока не запускаем: аудитор
не определил форму засева. Стенд сообщает
`LEVEL 2: pending (seed_data_needs is null — ask the implementer)` и продолжает. Когда
`seed_data_needs` — строка, оператор стенда засевает данные согласно её описанию перед запуском
блока с представительным вводом выше.

## Проверка 4 — каждая возможность записи при отсутствии ввода возвращает `ability_invalid_input` или `<plugin>_missing_<field>`

```bash
<env-cli> wp --user=admin eval '
$a = wp_get_ability( "<plugin>/<write-ability>" );

$r1 = $a->execute( array() );
echo "missing: " . ( is_wp_error( $r1 ) ? "WP_Error(" . $r1->get_error_code() . ")" : "UNEXPECTED_OK" ) . PHP_EOL;

$r2 = $a->execute( array( "<required_field>" => 123 ) );
echo "non-string: " . ( is_wp_error( $r2 ) ? "WP_Error(" . $r2->get_error_code() . ")" : "UNEXPECTED_OK" ) . PHP_EOL;
'
```

Допустимые коды согласно `../../wp-abilities-api/references/error-code-vocabulary.md`:

- `ability_invalid_input` — первым сработал валидатор схемы Abilities API (обычный путь через
  мост REST; выдаётся `WP_Ability::validate_input()` в ядре);
- `<plugin>_missing_<field>` — сработала собственная защита колбэка выполнения (путь прямого
  вызова);
- `<plugin>_invalid_<field>` — то же для случая неверного типа.

`UNEXPECTED_OK` → FAIL. Проверка отсутствует: возможность приняла пустой ввод и сделала то,
чего делать не должна была.

## Проверка 5 — барьер прав отказывает подписчику и разрешает администратору

```bash
<env-cli> wp --user=admin eval '
$ability = wp_get_ability( "<plugin>/<any-ability>" );
$input   = array(); // representative input; substitute for non-object root schemas.

// Admin path.
wp_set_current_user( 1 );
$admin_result = $ability->check_permissions( $input );

// Subscriber path.
$sub_login = "verify_sub_" . time();
$sub_id    = wp_create_user( $sub_login, "x", $sub_login . "@example.com" );
if ( ! is_wp_error( $sub_id ) ) {
    $user = get_user_by( "id", $sub_id );
    $user->set_role( "subscriber" );
    wp_set_current_user( $sub_id );
    $sub_result = $ability->check_permissions( $input );
} else {
    $sub_result = $sub_id; // surface the create_user error in the report
}

foreach ( array( "admin" => $admin_result, "subscriber" => $sub_result ) as $context => $r ) {
    if ( true === $r ) {
        $printable = "true";
    } elseif ( is_wp_error( $r ) ) {
        $printable = "WP_Error(" . $r->get_error_code() . ")";
    } else {
        $printable = var_export( $r, true );
    }
    echo $context . ": " . $printable . PHP_EOL;
}

// Cleanup the test subscriber so repeated harness runs don't accumulate users
// on shared dev environments. Switch back to admin first since we last ran as
// the subscriber and that role doesn't hold delete_users. On multisite,
// wp_delete_user() only removes the user from the current site membership —
// wpmu_delete_user() in wp-admin/includes/ms.php is the network-wide delete.
if ( isset( $sub_id ) && ! is_wp_error( $sub_id ) ) {
    wp_set_current_user( 1 );
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

Ожидаемое:

```
admin: true
subscriber: false
```

Любая инверсия — ошибка в зарегистрированном `permission_callback`. Более глубокие сверки
(объявленное в аудите право → зарегистрированный колбэк → разрешённый `current_user_can(...)`)
см. в `permission-roundtrip.md`.

Публичные возможности (намеренно без барьера) ожидают `subscriber: true` И `admin: true`. Перед
принятием такого исхода убедись, что `permission_callback` возможности в исходниках равен
`'__return_true'`.

`check_permissions()` возвращает `bool|WP_Error` согласно `WP_Ability::check_permissions()` в
ядре WordPress. `WP_Error` с кодом `ability_invalid_permission_callback` означает, что
регистрация не дала допустимую вызываемую функцию, — жёсткий FAIL. `WP_Error` с кодом
`ability_callback_exception` означает, что колбэк выбросил исключение, — тоже жёсткий FAIL.

## Проверка 6 — эвристика двойного вызова для идемпотентных возможностей

Применяй только к возможностям с аннотацией `idempotent: true`, чей `execute()` вернулся без
ошибки в проверке 3. Согласно шагу «Дополнение в режиме выполнения» в
`annotation-correctness.md`, это *эвристика*: идемпотентность в ядре означает «нет
дополнительного эффекта на окружение» (согласно docblock аннотации `idempotent` в
`class-wp-ability.php`), а не «побайтово одинаковые возвращаемые значения».

```bash
<env-cli> wp --user=admin eval '
$a  = wp_get_ability( "<plugin>/<idempotent-ability>" );
$r1 = $a->execute();
$r2 = $a->execute();

if ( is_wp_error( $r1 ) || is_wp_error( $r2 ) ) {
    echo "skipped: one or both invocations returned WP_Error" . PHP_EOL;
    if ( is_wp_error( $r1 ) ) { echo "r1=" . $r1->get_error_code() . PHP_EOL; }
    if ( is_wp_error( $r2 ) ) { echo "r2=" . $r2->get_error_code() . PHP_EOL; }
} else {
    $h1 = md5( serialize( $r1 ) );
    $h2 = md5( serialize( $r2 ) );
    echo "match=" . var_export( $h1 === $h2, true ) . PHP_EOL;
    echo "h1=" . $h1 . PHP_EOL;
    echo "h2=" . $h2 . PHP_EOL;
}
'
```

Толкование:

- `match=true` → дешёвый PASS. Тот же ввод дал тот же ответ, и любые записи в окружение
  (возможности записи) были одинаковыми в обоих вызовах.
- `match=false` → прежде чем решать, изучи, что изменилось:
  - ответ включает отметку времени, nonce или случайный ID на каждый вызов → окружение не
    изменилось. По определению ядра это всё ещё идемпотентно. При желании убери поле, если оно не
    нужно агенту; аннотация остаётся `idempotent: true`;
  - ответ отражает счётчик или последовательность, выросшие между вызовами → реальное изменение
    окружения. FAIL: убери аннотацию `idempotent: true` или исправь лежащую в основе запись,
    чтобы она определялась вводом.

Для неоднозначных случаев (ответ меняется, но очевидного счётчика нет) дополни сравнением
состояния: сними снимок представительной таблицы или опции до вызова 1, снимок после вызова 2,
сравни. Если состояние изменилось сильнее, чем объясняют записи из ввода, возможность
неидемпотентна.

## Формат вывода

Стенд режима выполнения пишет отдельный раздел в отчёт прогона:

```markdown
## Runtime harness

**Env:** wp-env (Docker), WordPress 7.0, <plugin> <version>
**Captured:** <YYYY-MM-DD HH:MM>

### Check 1 — enumeration

count=7 (expected 7 from static inventory)
<sorted list>

### Check 2 — annotations

| Ability | readonly | destructive | idempotent | Matches source? |
|---|---|---|---|---|

### Check 3 — read execution

| Ability | Result |
|---|---|

### Check 4 — write input validation

| Ability | Missing-input code | Wrong-type code |
|---|---|---|

### Check 5 — permission gate

| Ability | admin | subscriber | Expected |
|---|---|---|---|

### Check 6 — idempotency

| Ability | match | h1 | h2 |
|---|---|---|---|

### Notes / surprises

<Anything unexpected that didn't block.>
```

## Когда стенд ловит ошибку

Наблюдаемый шаблон:

1. Стенд выявляет фатальную ошибку PHP (например,
   `ArgumentCountError: Too few arguments to function <controller>::__construct`).
2. Исполнитель исправляет ошибку отдельным коммитом.
3. Стенд запускается снова; вывод после исправления пишется как итоговый статус.
4. Сохрани трассировку до исправления в отчёте в разделе «Статус до исправления», чтобы
   ревьюеры видели, что поймала проверка.

Это самый ценный сигнал, который даёт стенд режима выполнения: ошибки порядка инициализации и
отсутствующих зависимостей проходят статическое ревью, потому что исходник объявляет верную
форму, и проявляются только когда регистрация работает против загруженного WordPress.
