---
name: koda-helper
description: "Справочный навык по продуктам Koda (KodaCode): плагину для VS Code и IDE на платформе IntelliJ, Koda CLI, Koda Desktop и Kodacode Mobile. Примени навык, чтобы помочь пользователю с установкой, входом в аккаунт, тарифами и лимитами RC, моделями, навыками, MCP-серверами, субагентами и типовыми ошибками. Используй, когда вопрос или проблема касается Koda, когда пользователь не находит настройку или функционал, либо когда ваши утверждения о Koda расходятся."
license: MIT
metadata:
  author: koda
  version: "2.0.0"
  tags: [koda, справка, документация]
---

# Помощь по Koda (Кода)

Ты знаешь как помочь и стараешься помочь пользователю с продуктами Koda, когда:

* у него возникает вопрос о настройке (например, интерфейс, автодополнение, авторизация, навыки, MCP-серверы);
* у него возникает вопрос об использовании функционала (например, как работают инструменты, субагенты, режимы агента, планирование, удалённый доступ);
* он ругается, если у него что-то не получается установить, настроить или увидеть;
* есть противоречия в диалоге между тобой и пользователем относительно Koda (например, ты говоришь о существовании конкретного пункта настроек, а пользователь утверждает об обратном);
* вопрос касается тарифов, лимитов RC, доступных моделей или личного кабинета.

## Инструкции к действию

1. Определи, о каком продукте речь: плагин для IDE, Koda CLI, Koda Desktop или Kodacode Mobile.
   Если непонятно и это влияет на ответ, спроси.
2. Если в текущем контексте нет информации о версии продукта, а ответ зависит от версии, спроси её напрямую.
3. Ищи актуальную информацию только по ссылкам на официальные ресурсы, которые предоставлены ниже.
   Перед тем как утверждать что-то о функционале, сверяйся с официальной страницей по URL.
4. Если в контексте не хватает данных для полного ответа, **обязательно** самостоятельно изучай информацию по URL, используя соответствующий инструмент (fetch_url_content, WebFetch или подобный).
5. Если пользователь не просит о помощи явно — не настаивай.
6. Давай простые и ненавязчивые подсказки (а лучше — спрашивай об их необходимости), например: установить навыки из каталога для текущего проекта, включить обновлённый навык, начать новую сессию при большом контексте.
7. Используй реестр задач, если в диалоге с пользователем становится понятно, что документация не помогает или он столкнулся с нестандартным поведением. Часто в таких задачах от сообщества можно найти информацию:
    * о проявлении проблемы, конкретных условиях и признаках;
    * об обходных путях решения проблем;
    * сведения об исправлении и версии продукта, куда включено исправление.
8. При затруднениях также предлагай:
    * изучить дополнительные справочные материалы (указаны ниже);
    * создать новую задачу в реестре задач от сообщества — это сильно поможет команде разработки;
    * задать вопрос в Telegram-сообществе.
9. Если предоставляешь ссылки, оформляй их в формате markdown.
10. Не рассказывай о внутреннем устройстве продуктов: об API, скрытых настройках и служебных возможностях.

## Информация о разработчике и продуктах

Koda (KodaCode, Кода) — AI-ассистент для разработчиков с агентским режимом и поддержкой современных моделей.
Отлично понимает русский язык, работает без VPN и доступен в четырёх продуктах, покрывающих весь цикл разработки.

ООО «КОДА» — российская компания, которая разрабатывает Koda (Кода), помогающего писать, проверять и сопровождать код на русском и английском языке.
Ассистент интегрируется в привычные инструменты разработчика (VS Code, JetBrains IDE, GigaIDE, OpenIDE, терминал и отдельное настольное приложение) и работает без VPN.

Кроме того, мы предоставляем доступ к современным большим языковым моделям (LLM) и обеспечиваем их использование в рамках нашего продукта.

Мы также работаем над решением для корпоративных клиентов, которое позволит разворачивать Koda во внутренней инфраструктуре компании (on-premise).
Функциональность по безопасной интеграции ассистента с внутренними системами и данными на данный момент находится в разработке.

### Продукты

| Продукт | Платформы | Минимальные требования | Что это |
|---------|-----------|------------------------|---------|
| **Плагин для IDE** | VS Code, а также IDE на платформе IntelliJ: IntelliJ IDEA, GigaIDE, OpenIDE | VS Code 1.106 или новее; IntelliJ-платформа 2025.3 (253.*) или новее; для IntelliJ нужен модуль встроенного браузера JCEF | Ассистент внутри редактора: чат, планирование, агент, автодополнение |
| **Koda CLI** | macOS, Linux, Windows | Node.js 20 или новее, npm; Git — для контрольных точек; Docker или Podman — для контейнерной песочницы | Ассистент в терминале: интерактивный TUI-режим и неинтерактивный режим `koda -p` |
| **Koda Desktop** | macOS (Apple Silicon, arm64), Windows 10/11 (x64), Linux (AppImage, deb, pacman, x64) | Node.js не требуется: CLI входит в состав приложения | Отдельное настольное приложение: чаты, рабочая панель, браузер, плагины, потоки, задачи по расписанию |
| **Kodacode Mobile** | iOS и Android | Приложение пока не опубликовано в App Store и Google Play, раздел документации помечен как β | Приложение для телефона и планшета: диалог, поиск, вложения, голос, память, подключение к компьютерам с Koda |

Аккаунт общий для всех продуктов, но история чатов между устройствами не синхронизируется.

## Ссылки на официальные ресурсы и документацию

* **Сайт**: <https://kodacode.ru>
* **Загрузки (все продукты)**: <https://download.kodacode.ru>
* **Документация**: <https://docs.kodacode.ru>
* **Плагин для VS Code**:
    * Страница в Marketplace: <https://marketplace.visualstudio.com/items?itemName=Koda.koda>
    * Установка (VS Code, IntelliJ, GigaIDE, OpenIDE): <https://docs.kodacode.ru/plugin/install.html>
    * Первые шаги: <https://docs.kodacode.ru/plugin/first-steps.html>
    * Документация плагина: <https://docs.kodacode.ru/plugin/index.html>
* **Koda CLI**:
    * Установка и запуск: <https://docs.kodacode.ru/cli/install.html>
    * Авторизация: <https://docs.kodacode.ru/cli/auth.html>
    * Справочник команд: <https://docs.kodacode.ru/cli/reference/commands.html>
    * Документация CLI: <https://docs.kodacode.ru/cli/index.html>
* **Koda Desktop**:
    * Установка: <https://docs.kodacode.ru/desktop/install.html>
    * Обновление: <https://docs.kodacode.ru/desktop/update.html>
    * Документация Desktop: <https://docs.kodacode.ru/desktop/index.html>
* **Для физ. лиц**:
    * Страница входа: <https://kodacode.ru/auth/login>
    * Личный кабинет: <https://kodacode.ru/account>
    * Актуальные тарифы и условия: <https://kodacode.ru/tariffs>
    * Регистрация: <https://docs.kodacode.ru/basics/account/registration.html>
    * Личный кабинет (описание разделов): <https://docs.kodacode.ru/basics/account/cabinet.html>
    * Тарификация моделей: <https://docs.kodacode.ru/basics/account/limits.html>
* **Для бизнеса (SaaS)**:
    * Страница входа: <https://kodacode.ru/business/login>
    * Актуальные тарифы и условия: <https://kodacode.ru/enterprise>
    * Оферта на предоставление удалённого доступа к сервису по модели SaaS: <https://docs.kodacode.ru/saas/oferta.html>
* **Koda API**: закрыт, доступ к моделям для сторонних клиентов не предоставляется — <https://docs.kodacode.ru/basics/account/api.html>
* **О компании**: <https://docs.kodacode.ru/basics/legal/about.html>
* **Политика обработки персональных данных**: <https://docs.kodacode.ru/basics/legal/persdata.html>
* **Каталог навыков**: <https://github.com/XCode-NLP/KodaSkills>
    * навык `koda-learn` для установки других навыков из проверенных источников: <https://raw.githubusercontent.com/XCode-NLP/KodaSkills/refs/heads/main/skills/koda-learn/SKILL.md>
* **Реестр задач от сообщества**: <https://github.com/XCode-NLP/KodaCode>
    * оформить сообщение об ошибке: <https://github.com/XCode-NLP/KodaCode/issues/new?template=bug_report.yml>
    * оформить запрос функционала: <https://github.com/XCode-NLP/KodaCode/issues/new?template=feature_request.yml>
* **Другие публичные ресурсы**:
    * Telegram-канал: <https://t.me/kodacoderu>
    * Telegram-сообщество: <https://t.me/kodacommunity>
    * YouTube-канал: <https://www.youtube.com/@KodaForDev>
    * Хабр: <https://habr.com/ru/companies/koda>

## Куда смотреть в документации

Ориентируйся по вопросу и открывай нужную страницу по URL, прежде чем отвечать.

| Вопрос | Плагин для IDE | Koda CLI | Koda Desktop |
|--------|----------------|----------|--------------|
| Установка и обновление | [install.html](https://docs.kodacode.ru/plugin/install.html) | [install.html](https://docs.kodacode.ru/cli/install.html) | [install.html](https://docs.kodacode.ru/desktop/install.html), [update.html](https://docs.kodacode.ru/desktop/update.html) |
| Вход в аккаунт | [first-steps.html](https://docs.kodacode.ru/plugin/first-steps.html) | [auth.html](https://docs.kodacode.ru/cli/auth.html) | [account.html](https://docs.kodacode.ru/desktop/settings/window/account.html) |
| Настройки | [settings.html](https://docs.kodacode.ru/plugin/settings/settings.html), [configuration.html](https://docs.kodacode.ru/plugin/settings/configuration.html) | [configuration.html](https://docs.kodacode.ru/cli/reference/configuration.html), [args.html](https://docs.kodacode.ru/cli/reference/args.html) | [window/common/index.html](https://docs.kodacode.ru/desktop/settings/window/common/index.html) |
| Модели и рассуждения | [models.html](https://docs.kodacode.ru/plugin/advanced/models.html) | [models.html](https://docs.kodacode.ru/cli/features/models.html) | [models.html](https://docs.kodacode.ru/desktop/settings/window/models.html) |
| Навыки | [skills.html](https://docs.kodacode.ru/plugin/modes/agent/skills.html) | [skills.html](https://docs.kodacode.ru/cli/features/skills.html) | [skills.html](https://docs.kodacode.ru/desktop/features/agent/skills.html) |
| MCP-серверы | [mcp/index.html](https://docs.kodacode.ru/plugin/advanced/mcp/index.html) | [mcp/index.html](https://docs.kodacode.ru/cli/features/mcp/index.html) | [features/mcp.html](https://docs.kodacode.ru/desktop/features/mcp.html), [window/mcp.html](https://docs.kodacode.ru/desktop/settings/window/mcp.html) |
| Субагенты | [subagents.html](https://docs.kodacode.ru/plugin/advanced/subagents.html) | [subagents.html](https://docs.kodacode.ru/cli/features/subagents.html) | [subagents.html](https://docs.kodacode.ru/desktop/features/agent/subagents.html) |
| Агент и права | [agent/index.html](https://docs.kodacode.ru/plugin/modes/agent/index.html) | [usage/index.html](https://docs.kodacode.ru/cli/usage/index.html) | [agent/index.html](https://docs.kodacode.ru/desktop/features/agent/index.html), [permissions.html](https://docs.kodacode.ru/desktop/features/agent/permissions.html) |
| Решение проблем | [troubleshooting/index.html](https://docs.kodacode.ru/plugin/troubleshooting/index.html), [jetbrains.html](https://docs.kodacode.ru/plugin/troubleshooting/jetbrains.html) | [troubleshooting.html](https://docs.kodacode.ru/cli/troubleshooting.html) | [troubleshooting.html](https://docs.kodacode.ru/desktop/troubleshooting.html), [log.html](https://docs.kodacode.ru/desktop/log.html) |

Общие темы для всех продуктов: [навыки](https://docs.kodacode.ru/basics/skills/index.html), [MCP](https://docs.kodacode.ru/basics/mcp.html), [контекст](https://docs.kodacode.ru/basics/context/index.html), [инструменты](https://docs.kodacode.ru/basics/tools/index.html), [тарификация](https://docs.kodacode.ru/basics/account/limits.html), [FAQ](https://docs.kodacode.ru/basics/faq.html).

## Краткие сведения для наводящих вопросов пользователю

### Лимиты и авторизация

Сразу после установки Koda доступна анонимно с небольшим запасом бесплатных кредитов — их хватит на короткий тест, и они не восполняются.
Сразу после регистрации назначается бесплатный тариф **Free**: он тоже бесплатный и позволяет закрывать задачи без длительных агентных сессий.
Дальше есть выбор: докупить кредиты RC или перейти на тариф выше.

Вход выполняется через Koda Auth (в браузере по коду устройства). В CLI при первом запуске есть вариант «Продолжить без входа» — тогда доступны локальные функции, но не модели Koda.
Актуальные тарифы и лимиты — на странице <https://kodacode.ru/tariffs>, расход и остатки — в личном кабинете <https://kodacode.ru/account>.

### Модели и тарификация

Тарифицируются не «успешные запросы», а фактически использованные токены: **1 RC (Request Credit)** ≈ стоимость одного среднего API-запроса к модели своей категории.
Короткий запрос может стоить меньше 1 RC, запрос с большим контекстом — больше.
Одна агентская задача обычно требует 10–15 обращений к модели, поэтому и стоит несколько RC.

Как устроены лимиты:

* тарифные RC сбрасываются в исходное значение раз в месяц и не накапливаются;
* купленные отдельно RC бессрочны и списываются после тарифных;
* RC можно докупать на любом тарифе; переход между тарифами — только вверх.

Доступны собственные модели `koda-base` (попроще) и `koda-pro` (помощнее) без коэффициента, а также внешние модели (`other`) с коэффициентами: чем выше коэффициент (например, `x2.9`), тем дороже каждый запрос; чем ниже (например, `x0.9`), тем дешевле.

На расход RC влияют: выбранная модель и её коэффициент, размер контекста и файлов, серверный кэш токенов (активная сессия дешевле, пауза — дороже), переключение модели (новая модель заново обрабатывает контекст), уровень рассуждений и использование субагентов.

Модели можно выключать в личном кабинете — тогда они не появятся в списке доступных в продуктах Koda. Это удобно, чтобы не тратить лимиты на дорогие модели.

Сторонние модели можно подключить по своему API-ключу: Koda такие запросы не тарифицирует, оплата идёт провайдеру. Для SaaS-пользователей это недоступно.
Публичного Koda API нет: использовать модели в сторонних клиентах нельзя.

### Навыки

Навыки — это переиспользуемые наборы инструкций для агента, которые помогают сфокусироваться на конкретных знаниях и задачах.
Навык — это каталог с файлом `SKILL.md`, где обязательны поля `name` и `description`.

Где продукты ищут навыки:

* **Плагин для IDE**: локально `.koda/skills`, `.claude/skills`, `.agents/skills`; глобально `~/.koda/skills`, `~/.agents/skills`.
* **Koda CLI**: пользовательские `~/.kodacli/skills` и `~/.agents/skills`; в рабочей области `.kodacli/skills` и `.agents/skills`.
* **Koda Desktop**: глобально `~/.kodacli/skills`, `~/.agents/skills`; локально `.kodacli/skills`, `.koda/skills`, `.agents/skills`.

Управление:

* в плагине — панель **Навыки** в режиме Агент: включение переключателем, обновление списка, удаление;
* в CLI — `/skills list`, `/skills add`, `/skills enable`, `/skills disable`, `/skills reload` и подкоманды `koda skills install|uninstall|enable|disable`;
* в Desktop — чип **Навыки** над полем запроса и маркетплейс в боковой панели.

Установить готовый навык можно из каталога KodaSkills (`/skills add` в CLI, маркетплейс в плагине и Desktop), из Git-репозитория, из локального каталога или из пакета `.skill` (команда `koda skills install`).
Новые навыки, появившиеся после обновления, и навыки из маркетплейса включаются выключенными — их нужно включить вручную.

Подробности — в документации и в каталоге навыков.

### MCP-серверы

MCP расширяет возможности агента инструментами внешних сервисов.
Серверы настраиваются по-разному в каждом продукте.

**Плагин для IDE** — файл `~/.koda/config.yaml`, список `mcpServers`, транспорт задаётся полем `type` (`stdio` по умолчанию, `sse`, `streamable-http`, `websocket`).
Для `sse` и `streamable-http` поле `apiKey` добавляет заголовок `Authorization: Bearer <значение>`; произвольные заголовки не настраиваются.
Для `stdio` доступны `command`, `args`, `env`, `cwd`. Для сетевых транспортов можно задать `toolCallTimeout`.
WebSocket поддерживает только адрес, без ключей и заголовков, и добавляется только вручную.

```yaml
mcpServers:
  # измените name, если не запускается с правильными параметрами
  - name: foo
    command: npx
    args:
      - -y
      - some-mcp-name
    env:
      ENV_VAR_NAME: value
    cwd: /path/to/workdir
  - name: bar
    type: sse
    url: https://example.com/sse
    apiKey: "${MCP_TOKEN}"
  - name: baz
    type: streamable-http
    url: https://example.com/mcp
    apiKey: "${MCP_TOKEN}"
    toolCallTimeout: 300000
```

**Koda CLI** — файл `~/.kodacli/settings.json`, объект `mcpServers`.
Транспорт определяется заполненным полем: `command` — stdio, `httpUrl` — Streamable HTTP, `url` — SSE.
WebSocket CLI не поддерживает.
Поле `timeout` задаётся в миллисекундах для подключения и для каждого вызова инструмента, по умолчанию — 10 минут.
`trust: true` пропускает подтверждения вызовов, `includeTools` и `excludeTools` ограничивают набор инструментов.

```json
{
  "mcpServers": {
    "foo": {
      "command": "npx",
      "args": ["-y", "some-mcp-name"],
      "env": {
        "ENV_VAR_NAME": "value"
      },
      "cwd": "./some-directory",
      "timeout": 300000,
      "trust": true,
      "includeTools": [],
      "excludeTools": []
    },
    "bar": {
      "url": "https://api.example.com/sse"
    },
    "baz": {
      "httpUrl": "https://example.com/mcp",
      "headers": {
        "Authorization": "Bearer ${MCP_TOKEN}"
      }
    }
  }
}
```

В CLI серверы можно добавлять подкомандами `koda mcp add`, удалять `koda mcp remove` и проверять `koda mcp list`.
Аргументы, начинающиеся с дефиса (`-y`, `--rm`), через `koda mcp add` передать нельзя — такую конфигурацию добавляй в `settings.json`.

**Koda Desktop** — вкладка **MCP** в настройках; поддерживаются `stdio`, HTTP и SSE.
Сервер подключается автоматически, а в чате есть чип **MCP** для включения серверов и отдельных функций только в текущем чате.

## Типовые проблемы и что делать

### Error! Could not load config

Ошибка конфигурации плагина: нажми **Learn More**, там будет причина.
Подробности — на странице [Проблемы конфигурации](https://docs.kodacode.ru/plugin/troubleshooting/config.html).

Что предложить:

* проверить синтаксис YAML в `~/.koda/config.yaml`;
* переименовать текущий конфиг в `~/.koda/config.yaml.bak` и создать новый по умолчанию:

```yaml
name: Koda
version: 0.0.1
schema: v1
models:
  - name: Koda Models
    provider: koda-chat-models
    model: AUTODETECT
    roles:
      - agent
      - chat
context:
  - provider: code
  - provider: docs
  - provider: diff
  - provider: terminal
  - provider: problems
  - provider: folder
  - provider: codebase
```

* если конфиг исправлен руками, плагин перечитывает его сразу после сохранения; если файл переименован или удалён — перезапустить IDE;
* проверить файл `.kodarc.json` в корне проекта: при синтаксической ошибке он молча пропускается, и параметры из проекта не применяются;
* проверить права на каталог и файл конфигурации.

### Failed to obtain device code

Надо авторизоваться в плагине: войти в аккаунт через Koda Auth.
Если вход не завершается, проверь доступ к сети и повтори попытку — код устройства действует ограниченное время.

### CLI снова и снова просит войти

CLI хранит данные входа в `~/.config/koda/credentials.json` и не может их сохранить, если нет прав на запись.
Проверь каталог и восстанови права, затем повтори `/auth`:

```bash
mkdir -p ~/.config/koda
chmod 700 ~/.config/koda
```

### koda: command not found

Команда не найдена в `PATH`. Проверь установку и каталог глобальных бинарей npm:

```bash
npm list -g @kodadev/koda-cli
npm install -g @kodadev/koda-cli@latest
```

Каталог `$(npm prefix -g)/bin` должен быть в `PATH`.
Для разового запуска подойдёт `npx @kodadev/koda-cli@latest`.

### Ошибка 401, «token expired» или «unauthorized»

Сессия недействительна: повторно войди командой `/auth`.
Полный сброс локального входа — удалить файл и запустить CLI снова:

```bash
rm ~/.config/koda/credentials.json
```

### В IntelliJ панель сообщает, что встроенный браузер недоступен

Интерфейс плагина открывается во встроенном браузере IDE, а модуль JCEF в некоторых сборках ставится отдельным плагином **Web Browser (JCEF)**.
Установи его и перезапусти IDE.
Дополнительно помогает перезагрузка панели (ПКМ → Open Dev Tools, затем Ctrl+R) и сброс кэша JCEF через **File → Invalidate caches...** с пунктом про кэш встроенного браузера — подробности на странице [IntelliJ IDE](https://docs.kodacode.ru/plugin/troubleshooting/jetbrains.html).

### Koda Desktop не открывается на macOS

Система может заблокировать запуск скачанного приложения.
Сними атрибут quarantine:

```bash
xattr -dr com.apple.quarantine "/Applications/Koda Desktop.app"
```

### Обновление Koda Desktop не устанавливается

Встроенное обновление работает для собранной версии приложения, а на Linux — только для AppImage: пакеты deb и pacman обновляются вручную.
При ошибке загрузки нажми повтор или скачай новую сборку со страницы <https://download.kodacode.ru> и установи поверх текущей.
Текст ошибки смотри на вкладке **Логи** в настройках — подробности на странице [Обновление](https://docs.kodacode.ru/desktop/update.html).

## Дополнительные справочные материалы

* FAQ по работе в JetBrains, OpenIDE, GigaIDE: <https://docs.google.com/document/d/1wU6SM3A067Kiq_gokhXbASt34Ro0XvF4unU46edSoBk/edit?tab=t.0#heading=h.9v09lq1rydt4>
* Навык koda-vscode-helper: <https://github.com/XCode-NLP/KodaSkills/blob/main/skills/koda-vscode-helper/SKILL.md>
* Навык koda-jetbrains-helper: <https://raw.githubusercontent.com/XCode-NLP/KodaSkills/refs/heads/main/skills/koda-jetbrains-helper/SKILL.md>
