---
name: jira-and-confluence-cli
description: "Работа с Jira и Confluence через Atlassian CLI (acli): задачи, спринты, доски, страницы, пространства и управление проектами."
license: Apache-2.0
metadata:
  author: abdullahkhawer
  source: https://github.com/abdullahkhawer/devops-skills
  tags: [jira, confluence, cli, задачи]
---

# Навык работы с Jira и Confluence

Используй инстанс и правила ниже при построении всех команд `acli`.

## Настройка

Задай URL своего сайта Atlassian, прежде чем пользоваться этим навыком:

| Настройка | Значение |
|---|---|
| Сайт Atlassian | `<your-site>.atlassian.net` |

Замени `<your-site>.atlassian.net` на настоящий домен своего сайта Atlassian по всему навыку.

### Предусловия (разовая настройка силами пользователя)

Если настройка ещё не выполнена, сообщи пользователю, что она требуется, и попроси выполнить шаги ниже вручную. Не выполняй эти шаги сам.

1. Установи Atlassian CLI, если он ещё не установлен:

```bash
brew tap atlassian/homebrew-acli
brew install acli
```

2. Аутентифицируйся на своём инстансе Atlassian:

```bash
acli auth login
```

Откроется окно браузера на `https://api.atlassian.com/oauth2/authorize/...`. Нажми **Accept**, чтобы выдать Atlassian CLI нужные области OAuth. После авторизации вернись в терминал и выбери свой сайт из списка, когда появится запрос.

## Структура команд

```
acli jira workitem   # создание, получение, список, обновление, смена статуса
acli jira board      # список, получение
acli jira sprint     # список, получение
acli confluence page # создание, получение, список, обновление
```

## Частые команды

### Создать задачу
```bash
acli jira workitem create \
  --project "PROJECT_KEY" \
  --type "Story" \
  --summary "Summary here" \
  --description-file /path/to/description.txt
```

Для многострочных описаний всегда используй `--description-file` с временным файлом — встроенный `--description` с переносами строк ненадёжен.

### Перечислить задачи (JQL)
```bash
acli jira workitem list --jql "project = ABC AND status != Done" --limit 100
```

### Получить задачу
```bash
acli jira workitem get --id ABC-1234
```

### Сменить статус задачи
```bash
acli jira workitem transition --id ABC-1234 --status "In Progress"
```

### Создать страницу Confluence
```bash
acli confluence page create \
  --space "SPACE_KEY" \
  --title "Page Title" \
  --content-file /path/to/content.txt
```

## Правила

- Для команд со списками всегда передавай `--limit 100`, чтобы получить полные результаты (`--paginate` в `acli` не поддерживается).
- НИКОГДА не запускай команды удаления без явного указания пользователя — удаление в Jira и Confluence необратимо.
- При построении запросов JQL и CQL предпочитай явные фильтры по полям свободному поиску, чтобы избежать случайных широких совпадений.
- Если ключ проекта, ключ пространства, идентификатор доски или ключ задачи выглядят незнакомо, остановись и попроси пользователя подтвердить, прежде чем продолжать.
- НИКОГДА не читай, не показывай и не сохраняй API-токен Atlassian — это учётные данные, они должны оставаться секретными.
