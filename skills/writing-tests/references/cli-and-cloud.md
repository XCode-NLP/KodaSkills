# Тестирование команд `@mcp-use/cli`

Тесты CLI запускают **собранный** CLI (`dist/bin.js`) как дочерний процесс, направляют его на
локальную подделку Manufact Cloud и проверяют то, что выходит. Стенд живёт в
`libraries/typescript/packages/cli/tests/helpers/`:

| Файл | Что он даёт |
| --------------- | ------ |
| `cli-test.ts` | `test` — тест Vitest с фикстурами `cloud` и `cli` |
| `fake-cloud.ts` | `startFakeCloud()` — подделка на `node:http` за фикстурой `cloud` |
| `run-cli.ts` | `runCli()` — запуск дочернего процесса за фикстурой `cli` |

Эталонный пример — `tests/cloud/deployments.test.ts`.

## Сначала сборка

Запускатор выполняет `dist/bin.js`, поэтому пересобирай после каждого изменения исходников:

```bash
cd libraries/typescript
pnpm --filter @mcp-use/cli build   # около секунды
pnpm --filter @mcp-use/cli exec vitest run tests/cloud/deployments.test.ts
```

Запускатор отказывается стартовать, когда `dist/bin.js` отсутствует или старше любого файла в
`src/`, поэтому устаревшая сборка не может выдать сломанное изменение за зелёное. CI собирает
перед тем, как тестировать.

## Тест от начала до конца

```ts
import { describe, expect } from "vitest";
import { test } from "../helpers/cli-test.js";
import { SIGNED_IN, signIn } from "../helpers/cloud-auth.js";
import { deployment } from "../helpers/cloud-fixtures.js";

test("restart redeploys the same server and branch", async ({ cloud, cli }) => {
  signIn(cloud); // the organization lookup every signed-in command makes
  cloud.on("GET", "/api/v1/deployments/dep_1", {
    body: deployment({ id: "dep_1", serverId: "srv_1", gitBranch: "main" }),
  });
  // Answers 201, the route's documented success status.
  cloud.on("POST", "/api/v1/deployments", { body: { id: "dep_2" } });

  const result = await cli.run(["deployments", "restart", "dep_1", "--json"], {
    env: SIGNED_IN,
  });

  expect(result.exitCode).toBe(0);
  expect(result.json).toEqual({ id: "dep_2" });
  expect(cloud.requestsTo("POST", "/api/v1/deployments")).toMatchObject([
    { body: { serverId: "srv_1", branch: "main", trigger: "redeploy" } },
  ]);
});
```

Используй `test` из `cli-test.ts`, а `describe` и `expect` — из `vitest`.

Для табличных тестов используй `test.for(cases)(name, ([a, b], { cli, cloud }) => …)`.
`test.each` не передаёт фикстуры. Обе формы показаны в `tests/help-contract.test.ts` и
`tests/bin.test.ts`.

## Фикстура `cloud`

Свежая подделка Cloud на каждый тест, слушающая `127.0.0.1` на свободном порту. Её маршруты
типизированы по сгенерированному клиенту Cloud (`tests/helpers/cloud-routes.gen.ts`).

- `cloud.on(method, path, reply)` отвечает на каждый совпавший вызов значением `reply`.
- `cloud.sequence(method, path, [reply1, reply2])` отвечает по одному вызову на ответ, по порядку.
  Вызов после последнего ответа считается необработанным — так тест доказывает, что цикл опроса
  остановился или запрос не повторялся.
- `path` — **полный конкретный путь**, который запрашивает CLI, например
  `/api/v1/deployments/dep_1`, без строки запроса. Он должен принадлежать маршруту из спецификации,
  иначе вызов не скомпилируется. Параметры запроса проверяй через `request.query`.
- Ответ — это `{ status?, body?, headers? }` или функция от запроса, возвращающая его. `body`
  отправляется как JSON и типизируется как ответ маршрута для этого `status`. `status` по умолчанию
  равен документированному успешному статусу маршрута (201 для `POST /api/v1/deployments`).
  Функция ответа также получает `request.params` — параметры пути (`{ id: "dep_1" }`).
- **Тела ответов проверяются по типам ответов Cloud** — и для фиксированных ответов, и для функций
  ответа, — поэтому фикстура, не соответствующая Cloud, валит `typecheck`. Статусы ошибок, которых
  нет в спецификации, например 500 или 503, могут нести любое тело.
- У объектов Cloud много обязательных полей. Строй их через `tests/helpers/cloud-fixtures.ts`
  (например, `deployment({ id, status })`) и передавай каждое поле, от которого зависят твои
  утверждения, чтобы значения были видны в тесте. Добавляй там конструктор, когда нужен новый
  объект.
- `cloud.onUndocumented(method, path, reply)` регистрирует маршрут, которого нет в спецификации, —
  без типов и проверок, а `cloud.sequenceUndocumented(method, path, replies)` — его `sequence`. Оба
  выбрасывают ошибку для маршрута, который в спецификации есть. Сегодня они нужны только маршрутам
  входа по устройству (`POST /api/auth/device/code` и `/token`); когда их используешь, объясни
  причину в комментарии.
- `cloud.requests` перечисляет все запросы в порядке поступления; `cloud.requestsTo(method, path)`
  фильтрует их. У каждого есть `method`, `path`, `query`, `headers` (в нижнем регистре), `body`
  (разобранный JSON, строка или `undefined`) и `rawBody` (`Buffer` для multipart-загрузок).
- Запрос без маршрута получает ответ 501 и попадает в `cloud.unhandled`. Фикстура **валит тест**
  после его завершения, если `unhandled` не пуст, поэтому регистрируй только маршруты, нужные
  поведению.

Когда Cloud меняется, перегенерируй клиент
(`pnpm --filter @mcp-use/cli generate:cloud-client <openapi.json>`); подделка, которая больше не
соответствует API, тогда валит `typecheck`.

## Фикстура `cli`

Песочница, подключённая к поддельному Cloud теста.

- `cli.run(args, { env, cwd, input, timeoutMs })` запускает `node dist/bin.js ...args` и разрешается
  в `{ exitCode, stdout, stderr, json, errorJson }`.
- `json` — это stdout, разобранный как **ровно один** документ JSON, или `undefined`. Две строки
  JSON дают `undefined`, поэтому `expect(result.json).toEqual({...})` заодно проверяет «только один
  документ». `errorJson` делает то же для stderr, куда попадают ошибки `--json`.
- Дочерний процесс работает с чистым окружением: наследуются только `PATH`, переменные временных
  директорий и базовые переменные Windows. Он получает:
  - `HOME` и `USERPROFILE`, указывающие на `cli.home`;
  - `XDG_CONFIG_HOME`, указывающий на `cli.configHome`;
  - `MCP_USE_CLOUD_API_URL`, указывающий на подделку;
  - `NO_COLOR=1`;
  - и всё, что ты передашь в `env`.

  Твои собственные `MANUFACT_TOKEN`, `MCP_USE_API_KEY`, `~/.manufact` и `~/.mcp-use` в тест не
  попадают.

- Рабочая директория — `cli.cwd`, пустая временная директория. Пиши туда файлы проекта или передай
  `cwd`.
- Stdin — это канал, никогда не TTY. В него пишется `input`, затем он закрывается. Команды, которые
  задавали бы вопрос, должны падать с «pass --yes», и это поведение стоит проверять.
- После теста всё удаляется.

## Рецепты

**Пользователь вошёл.** Передай `env: SIGNED_IN` (ключ API в `MANUFACT_TOKEN`) и вызови
`signIn(cloud)` из `tests/helpers/cloud-auth.ts` — он отвечает на поиск организации одной
организацией `org_1`. Чтобы проверить сохранённые учётные данные, запиши `~/.manufact/auth.json` в
`cli.home`; как это делается, показано в `tests/cloud/auth.test.ts`.

**Ошибки в JSON.** Команды по соглашениям из `src/core/command.ts` печатают документ ошибки в
**stdout** (`result.json`); команды, ещё не переведённые на эти соглашения, печатают его в stderr
(`result.errorJson`). Проверяй код выхода и `code` ошибки, а не сообщение:

```ts
expect(result.exitCode).toBe(1);
expect(result.json).toMatchObject({
  error: { code: "deployment_not_found" },
});
```

**Коды выхода.** 0 — успех или справка, 2 — ошибки использования и отсутствие подтверждения, 1 —
сбои API и операционные сбои.

**Файлы, которые пишет CLI.** Прочитай их обратно из `cli.home` или `cli.cwd` после запуска и
сравни с литеральным содержимым.

**Агенты — основные пользователи.** Большинство тестов должно использовать `--json`, проверять весь
документ через `toEqual` и убеждаться, что `stderr` при успехе пуст. Оставь несколько тестов
человеческого режима для форматов, которые читают люди или скрипты, например таблиц.

**Команды с опросом.** CLI спит по-настоящему между опросами (одна секунда для журналов сборки).
Дай подделке два ответа, а не десять, чтобы тест оставался быстрым и всё равно доказывал, что цикл
продвигается и останавливается. Опросы, учитывающие `MCP_USE_POLL_INTERVAL_MS` (вход по устройству
учитывает), не спят вовсе, если передать `env: { MCP_USE_POLL_INTERVAL_MS: "0" }`.

**Проекты, которые импортируют `mcp-use`, React или zod.** `cli.cwd` лежит во временной директории
ОС, где эти пакеты не разрешаются. Для `build`, `dev` или `typecheck` на настоящем проекте скопируй
фикстуру через `copyFixture()` из `tests/build/helpers.ts`. Она лежит внутри пакета и связывается с
`mcp-use`. Затем передай `cwd` (или `--path`) в `cli.run`.

**Сохранённое состояние.** Засей файлы в `cli.home` до запуска и прочитай их после;
`tests/client/client-saved.test.ts` делает это для `~/.mcp-use/client/servers.json`. Чтобы доказать,
что команда не сделала сетевого вызова, направь её на `cloud.origin`. Тогда любой запрос появится в
`cloud.requests`, и тот же файл теста может сочетать случай «запроса нет» со случаем, где запрос
действительно отправляется.

**Проекты не на mcp-use.** Manufact Cloud должен работать с любым проектом. Когда команда читает
проект, покрой хотя бы один случай, где `cli.cwd` не является проектом mcp-use (нет зависимости
`mcp-use` или это вообще не Node).

## Ловушки

- **Никогда не используй `spawnSync` и `execFileSync` для CLI.** Подделка работает в цикле событий
  теста. Синхронный запуск его блокирует, и CLI зависает.
- **Пересобирай после правки `src/`.** Защита от устаревшей сборки ловит забытую пересборку.
- **Не подменяй наши собственные модули** в тестах стенда. Если поведение нельзя достичь через
  argv, окружение, файлы и подделку, спроси себя, является ли оно поведением.
- Тесты в одном файле выполняются друг за другом, и у каждого свой сервер и свои директории,
  поэтому они никогда не делят состояние.
