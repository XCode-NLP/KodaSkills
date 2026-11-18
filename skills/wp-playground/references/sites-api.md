## Sites API и клиент активного сайта

Используй этот справочник для браузерных операций JavaScript на сайте Playground, когда
его выбрал [маршрутизатор взаимодействия](website.md#выбор-способа-взаимодействия).

- `window.playgroundSites` управляет сохранёнными сайтами в браузере и выбором активного
  сайта.
- `window.playground` — это `PlaygroundClient` для активной среды выполнения WordPress;
  `playgroundSites.getClient()` возвращает этого клиента после готовности сайта.

## Управление сайтами в браузере через `window.playgroundSites`

Используй `window.playgroundSites` на странице верхнего уровня
`https://playground.wordpress.net/`. Он появляется не сразу при загрузке страницы,
поэтому дождись глобального объекта, а затем вызови `isReady()` перед работой с
менеджером сайтов.

```js
while (!window.playgroundSites) {
	await new Promise((resolve) => setTimeout(resolve, 50));
}
await window.playgroundSites.isReady();
```

Доступные операции менеджера сайтов:

- `list()`: посмотреть известные сайты, активный сайт, имена, слаги и типы хранилища.
- `createNewTemporarySite(slug?, settings?)`: создать и переключиться на новый сайт в
  памяти. Настройки используют `phpVersion`, `wpVersion`, `networking`, `language` и
  `multisite`.
- `setActiveSite(slug)`: переключиться на существующий сайт и дождаться его загрузки.
- `isReady()`: дождаться готовности активного сайта и его клиента.
- `getClient()`: получить `PlaygroundClient` активного сайта.
- `saveInBrowser(name?)`: сохранить активный сайт в браузерное хранилище OPFS.
- `saveToLocalFileSystem(name?, handle?)`: сохранить активный сайт в выбранную
  пользователем локальную директорию, если браузер это поддерживает.
- `rename(newName)`: переименовать активный сохранённый сайт.
- `setPhpVersion(version)`: сменить версию PHP и перезагрузить активный сохранённый сайт.
- `setNetworking(enabled)`: включить или отключить исходящую сеть и перезагрузить
  активный сохранённый сайт.
- `delete(slug)`: удалить сохранённый сайт, когда пользователь явно попросил удаление.

Поведение хранилища:

- `temporary`: только в памяти; сбрасывается при перезагрузке.
- `opfs`: сохраняется в хранилище браузера для `playground.wordpress.net`; переживает
  перезагрузки.
- `local-fs`: сохраняется в выбранную пользователем локальную директорию; только
  Chromium и File System Access API.

Важные ограничения:

- `createNewTemporarySite()` принимает только настройки запуска сайта: `phpVersion`,
  `wpVersion`, `networking`, `language` и `multisite`. Имена в JS — `phpVersion` и
  `wpVersion`, а не `php` и `wp`.
- Он не устанавливает плагины и темы и не выполняет Blueprint: для этого используй
  работу с URL или Blueprint.
- `saveInBrowser()` и `saveToLocalFileSystem()` безопасны для уже сохранённых сайтов.
- `rename()`, `setPhpVersion()` и `setNetworking()` работают с активным сохранённым
  сайтом. Если нужен конкретный сайт, сначала переключись через `setActiveSite(slug)`.
  Временный сайт сначала сохрани.
- `delete(slug)` удаляет сохранённые данные сайта; не вызывай его, если пользователь не
  просил удаления.

## Взаимодействие с активным сайтом WordPress

Используй активный `PlaygroundClient` после загрузки сайта. Если пользователь пишет
`window.palyground`, считай это опечаткой вместо `window.playground`.

```js
await window.playgroundSites?.isReady();
const client = window.playgroundSites?.getClient() || window.playground;
await client.isReady();
```

Доступные операции с активным сайтом:

- Просмотр файлов: `listFiles`, `readFileAsText`, `readFileAsBuffer`, `fileExists`,
  `isFile`, `isDir`, `isSymlink`, `readlink` и `realpath` в виртуальной файловой системе
  `/wordpress`.
- Изменение файлов: `mkdir`, `mkdirTree`, `writeFile`, `mv`, `cp`, `chmod`, `symlink`,
  `unlink`, `rmdir` и `unzip`. `mv` перемещает или переименовывает файлы. `unlink`
  удаляет файлы, а `playgroundSites.delete(slug)` удаляет сохранённый сайт. `rmdir` — для
  пустых директорий.
- Выполнение PHP: запускай фрагменты PHP через `run({ code })`; смотри возвращённые поля
  вывода, статуса и ошибки. Подключи `/wordpress/wp-load.php` перед использованием API
  WordPress, таких как `wp_insert_post`, `get_option`, `get_stylesheet` или
  `wp_get_theme`.
- Веб-запросы: обращайся к маршрутам WordPress через
  `request({ path, method, headers, body })` и смотри статус и тело. Используй это для
  страниц админки, например `/wp-admin/`, и маршрутов REST, например
  `/wp-json/wp/v2/posts`; помни, что поведение админки и nonce зависит от состояния
  входа.
- Навигация в браузере: отправь видимый фрейм Playground на путь WordPress через
  `goTo(path)`.
- Проверка состояния: проверяй установленные и активные плагины и темы через PHP-API
  WordPress или по файловой системе, прежде чем сообщать об успешной настройке.
- MU-плагины: записывай файлы в `/wordpress/wp-content/mu-plugins/`, затем запроси или
  открой маршрут WordPress, чтобы заставить их загрузиться.

Держи различие ясным:

- `playgroundSites` управляет записями сайтов и сохранением.
- `window.playground` и `getClient()` работают с активной средой выполнения WordPress.
- Query API и `blueprint-url` настраивают сайт при загрузке страницы.

## Проверка

- Перед изменениями посмотри `window.playgroundSites.list()`, чтобы подтвердить нужный
  активный сайт.
- После операций менеджера сайтов проверь, что `window.playgroundSites.list()` показывает
  ожидаемый активный сайт и тип хранилища.
- Для операций клиента сначала выполни безвредное чтение, например
  `await client.listFiles('/wordpress')`, а уже потом записывай файлы или меняй
  состояние. После операции проверь запрошенное состояние.
- После смены сайта или перезагрузки дождись готовности и заново получи активный клиент
  перед дальнейшими операциями.
