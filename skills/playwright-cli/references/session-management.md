# Управление сессиями браузера

Запускай несколько изолированных сессий браузера одновременно с сохранением состояния.

## Именованные сессии браузера

Используй флаг `-s`, чтобы изолировать контексты браузера:

```bash
# Браузер 1: сценарий авторизации
playwright-cli -s=auth open https://app.example.com/login

# Браузер 2: обычный просмотр (отдельные cookie и хранилище)
playwright-cli -s=public open https://example.com

# Команды изолированы по сессии браузера
playwright-cli -s=auth fill e1 "user@example.com"
playwright-cli -s=public snapshot
```

## Свойства изоляции сессий браузера

У каждой сессии браузера независимые:
- cookie;
- LocalStorage / SessionStorage;
- IndexedDB;
- кэш;
- история просмотров;
- открытые вкладки.

## Команды сессий браузера

```bash
# перечислить все сессии браузера
playwright-cli list

# остановить сессию браузера (закрыть браузер)
playwright-cli close                # остановить браузер по умолчанию
playwright-cli -s=mysession close   # остановить именованный браузер

# остановить все сессии браузера
playwright-cli close-all

# принудительно убить все процессы демона (для зависших или зомби-процессов)
playwright-cli kill-all

# удалить пользовательские данные сессии браузера (директорию профиля)
playwright-cli delete-data                # удалить данные браузера по умолчанию
playwright-cli -s=mysession delete-data   # удалить данные именованного браузера
```

Сессия без интерфейса завершается сама через час без команд; следующая команда тогда сообщит, что браузер не открыт, поэтому запусти `open` снова. Браузеры с интерфейсом остаются открытыми. Используй `open --idle-timeout=<ms>`, чтобы изменить таймаут, или `0`, чтобы отключить его.

## Переменная окружения

Задай имя сессии браузера по умолчанию через переменную окружения:

```bash
export PLAYWRIGHT_CLI_SESSION="mysession"
playwright-cli open example.com  # автоматически использует "mysession"
```

## Частые приёмы

### Одновременный сбор данных

```bash
#!/bin/bash
# собрать данные с нескольких сайтов одновременно

# запустить все браузеры
playwright-cli -s=site1 open https://site1.com &
playwright-cli -s=site2 open https://site2.com &
playwright-cli -s=site3 open https://site3.com &
wait

# снять снимки с каждого
playwright-cli -s=site1 snapshot
playwright-cli -s=site2 snapshot
playwright-cli -s=site3 snapshot

# убрать за собой
playwright-cli close-all
```

### Сессии для A/B-тестирования

```bash
# проверить разные варианты интерфейса
playwright-cli -s=variant-a open "https://app.com?variant=a"
playwright-cli -s=variant-b open "https://app.com?variant=b"

# сравнить
playwright-cli -s=variant-a screenshot
playwright-cli -s=variant-b screenshot
```

### Постоянный профиль

По умолчанию профиль браузера хранится только в памяти. Используй флаг `--persistent` при `open`, чтобы сохранять профиль браузера на диск:

```bash
# постоянный профиль (расположение создаётся автоматически)
playwright-cli open https://example.com --persistent

# постоянный профиль с заданной директорией
playwright-cli open https://example.com --profile=/path/to/profile
```

## Подключение к работающему браузеру

Используй `attach`, чтобы подключиться к уже работающему браузеру вместо запуска нового.

### Подключение по имени канала

Подключайся к работающему экземпляру Chrome или Edge по имени канала. В браузере должна быть включена удалённая отладка — перейди в нём на `chrome://inspect/#remote-debugging` и отметь «Allow remote debugging for this browser instance».

```bash
# подключиться к Chrome
playwright-cli attach --cdp=chrome

# подключиться к Chrome Canary
playwright-cli attach --cdp=chrome-canary

# подключиться к Microsoft Edge
playwright-cli attach --cdp=msedge

# подключиться к Edge Dev
playwright-cli attach --cdp=msedge-dev
```

Поддерживаемые каналы: `chrome`, `chrome-beta`, `chrome-dev`, `chrome-canary`, `msedge`, `msedge-beta`, `msedge-dev`, `msedge-canary`.

Когда `--session` не указан, сессия называется по каналу (например, `--cdp=msedge` создаёт сессию `msedge`), поэтому одновременные подключения к Chrome и Edge не конфликтуют на `default`. Передай `--session=<name>`, чтобы задать имя явно.

### Подключение через эндпоинт CDP

Подключайся к браузеру, который открывает эндпоинт Chrome DevTools Protocol:

```bash
playwright-cli attach --cdp=http://localhost:9222
```

### Подключение через расширение браузера

Подключайся к браузеру с установленным расширением Playwright:

```bash
playwright-cli attach --extension
```

### Отключение

Заверши подключённую сессию, не затрагивая внешний браузер:

```bash
# отключить подключённую сессию по умолчанию
playwright-cli detach

# отключить конкретную подключённую сессию
playwright-cli -s=msedge detach
```

`detach` работает только для сессий, созданных через `attach`. Для сессий, созданных через `open`, используй `close`.

## Сессия браузера по умолчанию

Когда `-s` опущен, команды используют сессию браузера по умолчанию:

```bash
# эти команды используют одну и ту же сессию по умолчанию
playwright-cli open https://example.com
playwright-cli snapshot
playwright-cli close  # останавливает браузер по умолчанию
```

## Настройка сессии браузера

Задавай конкретные настройки сессии при открытии:

```bash
# открыть с файлом конфигурации
playwright-cli open https://example.com --config=.playwright/my-cli.json

# открыть в конкретном браузере
playwright-cli open https://example.com --browser=firefox

# открыть с интерфейсом
playwright-cli open https://example.com --headed

# открыть с постоянным профилем
playwright-cli open https://example.com --persistent
```

## Рекомендации

### 1. Называй сессии по смыслу

```bash
# ХОРОШО: понятное назначение
playwright-cli -s=github-auth open https://github.com
playwright-cli -s=docs-scrape open https://docs.example.com

# ИЗБЕГАЙ: обезличенные имена
playwright-cli -s=s1 open https://github.com
```

### 2. Всегда убирай за собой

```bash
# останови браузеры, когда закончил
playwright-cli -s=auth close
playwright-cli -s=scrape close

# или останови все сразу
playwright-cli close-all

# если браузеры перестали отвечать или остались зомби-процессы
playwright-cli kill-all
```

### 3. Удаляй устаревшие данные браузера

```bash
# удали старые данные браузера, чтобы освободить место на диске
playwright-cli -s=oldsession delete-data
```
