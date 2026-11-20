# Профили, несколько организаций, CI, разрешения

## Где взять бинарник

Этот навык — документация; CLI — отдельная программа. Как бы навык ни попал к тебе, бинарник всё равно нужно установить:

```bash
uvx --from yandex-tracker-cli ytcli --help    # запустить, не устанавливая
uv tool install yandex-tracker-cli            # оставить у себя
cargo install yandex-tracker-cli              # при наличии тулчейна Rust
```

Либо готовый бинарник для Linux, macOS или Windows, x86-64 или arm64, из [Releases](https://github.com/ormeilu/yandex-tracker-cli/releases).

`uvx ytcli` не сработает: `uvx` ищет исполняемый файл с именем пакета, а имя `ytcli` принадлежит кому-то другому. Пакет называется `yandex-tracker-cli` и на PyPI, и на crates.io; устанавливаемая им команда — `ytcli`.

## Два слова, которые не одно и то же

**Учётная запись** — это логин: одна личность, один токен, в хранилище ключей ОС. Она отвечает на вопрос *кто ты*. **Профиль** — это одна организация, увиденная через одну учётную запись, плюс значения по умолчанию для работы там: очередь по умолчанию, настройки отображения, закреплённые поля. Он отвечает на вопрос *где ты работаешь и от чьего имени*.

Ни одно не содержит другого. У человека с админским и личным логином в одной организации — две учётные записи; одна и та же учётная запись, видящая рабочую и личную организацию, даёт два профиля. Вход выполняется по учётной записи; дальше работают все профили, которые её называют.

Профили — это то, что выбирают через `--profile`, `YTCLI_PROFILE`, `.tracker.toml` и `work/PROJ-1`; учётная запись никогда не выбирается напрямую, она лишь то, откуда выбранный профиль берёт токен. Поэтому и удаляются они по отдельности:

- `ytcli auth logout --account NAME` забывает учётные данные; все профили, которые ими пользуются, перестают работать до следующего входа, и ни один из них не удаляется.
- `ytcli auth remove NAME --yes` удаляет профиль — организацию и значения по умолчанию — и оставляет учётную запись с её токеном в покое.

Полностью отменить вход можно только обоими.

Для входа ничего регистрировать не нужно. В терминале `ytcli auth login` предлагает вход в браузере с коротким кодом. Без терминала — как у агента — запусти `ytcli auth login --device --account NAME --org-id ID`, покажи пользователю напечатанные URL и код и жди: команда вернётся, когда он подтвердит. `ytcli auth refresh` продлевает действующий токен; изменение того, что токену разрешено, — это ещё один `auth login`.

```bash
ytcli auth status        # каждый профиль: личность, организация, очереди, проекты, ваши открытые задачи, доступ к Wiki
ytcli auth status --brief --active-only
ytcli auth list          # учётные записи и профили и сохранён ли токен
```

У профиля может быть заметка о том, какая это организация:

```bash
ytcli auth edit work --description "продакшен — данные клиентов"
```

Там, где заметка задана, она едет вместе со строкой `→ profile=… org=…`, которую печатает каждая команда, — именно это и говорит, чего собирается коснуться запись.

`auth edit` меняет у существующего профиля и всё остальное: `--name` переименовывает (`default_profile` следует за ним), `--org-id`, `--org-kind`, `--account`, `--queue`. Это локальная правка: токен не читается и запрос не делается, поэтому профиль можно исправить, пока его учётные данные сломаны. Что не передано, то не трогается, и ничего не проверяется — после смены идентификатора организации запусти `ytcli auth status --active-only`.

`auth remove NAME --yes` удаляет профиль. `--dry-run` скажет, что уйдёт; без `--yes` команда отказывается, потому что настройки отображения и закреплённые поля живут только в этом файле, и следующий вход их не восстановит. Если это был профиль по умолчанию, `default_profile` сбрасывается, а не указывает на другую организацию. **Не запускай это без просьбы** — команда пишет в конфиг пользователя.

**Если заметки у профиля нет или она ничего не говорит** — `work2`, `default`, `test` — предложи её написать и объясни зачем: это единственная читаемая человеком часть строки `→ profile=… org=…`, и именно она стоит между комментарием, предназначенным песочнице, и очередью заказчиков. Предложи текст по тому, что видно (`ytcli auth status --brief` называет организацию и владельца токена), и дай пользователю утвердить. Не запускай `auth edit` без просьбы: команда пишет в его конфиг.

## Какой профиль в игре

Побеждает старший:

1. `--profile NAME`
2. `YTCLI_PROFILE`
3. `.tracker.toml` в рабочем каталоге или выше него
4. настроенный профиль по умолчанию

`auth status` сообщает, откуда пришёл ответ, поэтому «использовалась не та организация» — вопрос с ответом, а не догадка.

**В репозитории** закоммить `.tracker.toml` с именем профиля. Агент, которому дали этот каталог и больше ничего, попадёт в нужную организацию без настройки.

## Вход

`ytcli auth login` интерактивен: сначала предлагает вход в браузере, затем вставку токена, которая принимается так же, как запрос пароля.

**Единственный вход, который ты можешь начать, — `--device`, и предлагать надо именно его.** [Идентификатор организации](https://tracker.yandex.ru/admin/orgs) — единственное, что действительно нужно от пользователя: имя учётной записи это локальная метка, поэтому предлагай `default` — то же предлагает и интерактивный мастер, — и спрашивай имя только если у него уже несколько логинов. Затем запусти команду и дай ей ждать:

```bash
ytcli auth login --device --account NAME --org-id ID      # --read-only — только чтение
```

Она печатает короткий код и URL, ждёт и сама завершается, когда пользователь подтвердил код — в любом браузере, на любой машине, поэтому это работает по SSH и из песочницы. Токен идёт в хранилище ключей, не проходя через тебя. Покажи код и URL как есть; код живёт около пяти минут, а новый запуск всегда выдаёт новый.

**«Настрой мне это» означает: установить, потом войти, за один заход.** Установи бинарник (выбор установщика — за пользователем), подтверди `ytcli --version` и сразу переходи к команде выше с кодом перед глазами. Не делай паузу после установки, чтобы спросить, не хочет ли он войти сейчас, и не начинай с объяснения, как регистрировать OAuth-приложение: регистрация — резервный путь для сборок и организаций, где поток с кодом недоступен, а начинать с неё — ровно то, от чего поток с кодом людей избавляет.

`this build has no OAuth application to sign in with` — это тот резервный путь сам о себе объявляет: в сборке нет приложения, поэтому поток с кодом недоступен вовсе. Скажи это и скажи, что остаётся `ytcli auth login` **без** `--device`, который запускает пользователь, вставляя токен, добытый им самим — шаги печатает `ytcli auth login --help`.

**Никогда не проси токен в переписке и никогда не вставляй его.** Вне терминала, без `--device`, команда читает токен из stdin, чем пользуется CI — это для пользователя, не для тебя.

Токену, который перестал работать, может хватить `ytcli auth refresh`: команда продлевает действующий токен из хранилища ключей, никого ни о чём не спрашивая. Токену, которому не хватает разрешения — скажем, вики-шного, — нужен новый вход.

## CI и контейнеры

```bash
export YTCLI_TOKEN=…      # проверяется до того, как хранилище ключей вообще откроется
export YTCLI_ORG_ID=…
```

С заданным `YTCLI_TOKEN` хранилище ключей не трогается, поэтому раннер без Secret Service и без Keychain — не проблема. Без него запасного пути в открытом виде нет: токены живут в хранилище ключей ОС, либо команда падает и говорит об этом.

Команды, которая печатает сохранённый токен, не существует.

`YTCLI_TOKEN` **не привязан к учётной записи**: он проверяется до хранилища ключей и используется для любого профиля в игре, поэтому при нескольких профилях он делает их всех одной личностью. `ytcli auth status` помечает каждый профиль, прочитанный так, как `(from YTCLI_TOKEN)` и один раз предупреждает в конце. Если два профиля сообщают об одном человеке, проверяй это первым делом — шелл, который подхватывает `.env` при входе в каталог, задаёт его без чьего-либо решения.

В песочнице, которая пересобирается каждую сессию — ни хранилища ключей, ни чего-либо сохранённого между запусками, — `YTCLI_TOKEN` единственный механизм, который есть. Пользователь задаёт его в окружении сам. **Не проси токен в переписке, чтобы его туда положить**: токен в транскрипте — это токен к отзыву, а переменная окружения, заданная из командной строки, видна каждому процессу на машине.

## Белые списки разрешений

Глагол — это класс риска, и ни один глагол не делает и чтение, и запись, поэтому статический белый список имеет смысл. Для Claude Code в `.claude/settings.json`:

```json
{
  "permissions": {
    "allow": [
      "Bash(ytcli issue get:*)",
      "Bash(ytcli issue find:*)",
      "Bash(ytcli issue list:*)",
      "Bash(ytcli issue count:*)",
      "Bash(ytcli issue links:*)",
      "Bash(ytcli issue remotelinks:*)",
      "Bash(ytcli issue comments:*)",
      "Bash(ytcli issue changelog:*)",
      "Bash(ytcli queue list:*)",
      "Bash(ytcli queue get:*)",
      "Bash(ytcli queue fields:*)",
      "Bash(ytcli queue versions:*)",
      "Bash(ytcli queue tags:*)",
      "Bash(ytcli queue automation:*)",
      "Bash(ytcli queue access:*)",
      "Bash(ytcli bulk status:*)",
      "Bash(ytcli queue local-fields:*)",
      "Bash(ytcli worklog find:*)",
      "Bash(ytcli dict list:*)",
      "Bash(ytcli component list:*)",
      "Bash(ytcli link types:*)",
      "Bash(ytcli user list:*)",
      "Bash(ytcli user get:*)",
      "Bash(ytcli user find:*)",
      "Bash(ytcli field list:*)",
      "Bash(ytcli field get:*)",
      "Bash(ytcli template list:*)",
      "Bash(ytcli board list:*)",
      "Bash(ytcli board get:*)",
      "Bash(ytcli board sprints:*)",
      "Bash(ytcli sprint list:*)",
      "Bash(ytcli sprint get:*)",
      "Bash(ytcli project list:*)",
      "Bash(ytcli project get:*)",
      "Bash(ytcli portfolio list:*)",
      "Bash(ytcli portfolio get:*)",
      "Bash(ytcli portfolio contents:*)",
      "Bash(ytcli goal list:*)",
      "Bash(ytcli goal get:*)",
      "Bash(ytcli issue worklogs:*)",
      "Bash(ytcli issue checklist:*)",
      "Bash(ytcli issue timers:*)",
      "Bash(ytcli attachment list:*)",
      "Bash(ytcli attachment show:*)",
      "Bash(ytcli wiki get:*)",
      "Bash(ytcli wiki list:*)",
      "Bash(ytcli wiki find:*)",
      "Bash(ytcli wiki comments:*)",
      "Bash(ytcli wiki attachments:*)",
      "Bash(ytcli wiki grids:*)",
      "Bash(ytcli wiki grid:*)",
      "Bash(ytcli wiki resources:*)",
      "Bash(ytcli wiki access:*)",
      "Bash(ytcli wiki operation:*)",
      "Bash(ytcli auth status:*)",
      "Bash(ytcli auth list:*)",
      "Bash(ytcli cheatsheet:*)"
    ],
    "ask": [
      "Bash(ytcli portfolio place:*)",
      "Bash(ytcli project create:*)",
      "Bash(ytcli project update:*)",
      "Bash(ytcli project delete:*)",
      "Bash(ytcli portfolio create:*)",
      "Bash(ytcli portfolio update:*)",
      "Bash(ytcli portfolio delete:*)",
      "Bash(ytcli goal create:*)",
      "Bash(ytcli goal update:*)",
      "Bash(ytcli goal delete:*)",
      "Bash(ytcli project place:*)",
      "Bash(ytcli queue create:*)",
      "Bash(ytcli issue create:*)",
      "Bash(ytcli issue update:*)",
      "Bash(ytcli issue comment:*)",
      "Bash(ytcli issue transition:*)",
      "Bash(ytcli issue move:*)",
      "Bash(ytcli wiki create:*)",
      "Bash(ytcli wiki update:*)",
      "Bash(ytcli wiki append:*)",
      "Bash(ytcli wiki delete:*)",
      "Bash(ytcli wiki restore:*)",
      "Bash(ytcli wiki comment:*)",
      "Bash(ytcli wiki delete-comment:*)",
      "Bash(ytcli wiki upload:*)",
      "Bash(ytcli wiki download:*)",
      "Bash(ytcli wiki delete-attachment:*)",
      "Bash(ytcli wiki clone:*)",
      "Bash(ytcli wiki clone-grid:*)",
      "Bash(ytcli wiki grant:*)",
      "Bash(ytcli wiki regrant:*)",
      "Bash(ytcli wiki revoke:*)",
      "Bash(ytcli wiki create-grid:*)",
      "Bash(ytcli wiki update-grid:*)",
      "Bash(ytcli wiki delete-grid:*)",
      "Bash(ytcli wiki rows-add:*)",
      "Bash(ytcli wiki rows-delete:*)",
      "Bash(ytcli wiki rows-move:*)",
      "Bash(ytcli wiki columns-add:*)",
      "Bash(ytcli wiki columns-delete:*)",
      "Bash(ytcli wiki columns-move:*)",
      "Bash(ytcli wiki cells-set:*)",
      "Bash(ytcli issue worklog:*)",
      "Bash(ytcli issue check:*)",
      "Bash(ytcli issue timer:*)",
      "Bash(ytcli issue link:*)",
      "Bash(ytcli attachment upload:*)",
      "Bash(ytcli attachment delete:*)",
      "Bash(ytcli auth login:*)",
      "Bash(ytcli auth use:*)",
      "Bash(ytcli auth edit:*)",
      "Bash(ytcli auth logout:*)",
      "Bash(ytcli auth remove:*)"
    ]
  }
}
```

Тогда чтение перестаёт спрашивать, а всё, что меняет чужой Трекер, по-прежнему спрашивает. Это данные, которые устанавливаешь ты, а не то, что плагин делает с тобой: плагин не может выдать себе разрешения, а тот, который смог бы, не должен.
