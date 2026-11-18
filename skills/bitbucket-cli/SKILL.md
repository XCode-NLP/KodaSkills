---
name: bitbucket-cli
description: "Работа с Bitbucket через REST API и curl: репозитории, pull request, конвейеры и задачи. Используй этот навык и тогда, когда просят проверить pull request Bitbucket: если дан URL или идентификатор PR, бери дифф и проверяй его, а не через навык code-review."
license: Apache-2.0
metadata:
  author: abdullahkhawer
  source: https://github.com/abdullahkhawer/devops-skills
---

# Навык работы с Bitbucket

У Bitbucket Cloud нет официального CLI, сравнимого с `gh` и `glab`, — для всех операций используй REST API через `curl`.

## Настройка

Обнови рабочую область ниже, прежде чем пользоваться этим навыком:

| Настройка | Значение |
|---|---|
| Рабочая область Bitbucket | `<your-workspace>` |
| Файл учётных данных | `~/.bitbucket/token` |

Если целевая рабочая область неясна, спроси пользователя, прежде чем запускать любую команду.

### Предусловия (разовая настройка силами пользователя)

Создай [App Password](https://bitbucket.org/account/settings/app-passwords/) с правами `Repositories: Read` (и `Write` либо `Pull requests: Write`, если нужны изменения), затем сохрани `<username>:<app-password>` в файл учётных данных. Никогда не печатай и не показывай значение учётных данных. Не выполняй эти шаги сам.

```bash
mkdir -p ~/.bitbucket && echo "<username>:<app-password>" > ~/.bitbucket/token && chmod 600 ~/.bitbucket/token
```

## Формат команд

Все вызовы API идут через `curl` с basic-аутентификацией, читаемой из файла учётных данных:

```bash
curl -s -u "$(cat ~/.bitbucket/token)" \
  "https://api.bitbucket.org/2.0/<endpoint>" | jq .
```

## Проверка кода в PR

Когда просят проверить pull request Bitbucket (дан URL или идентификатор PR), извлеки `<workspace/repo>` и `<PR_ID>` из URL (если репозитория нет, спроси пользователя), затем получи метаданные PR (`GET /2.0/repositories/<workspace>/<repo>/pullrequests/<PR_ID>`) и его дифф (`GET /2.0/repositories/<workspace>/<repo>/pullrequests/<PR_ID>/diff`). Чтобы полностью понять контекст и влияние всех изменений кода, прочитай всю кодовую базу исходной ветки — один дифф не передаёт окружающую логику, зависимости и общий дизайн, с которыми взаимодействуют изменения. Сообщи заголовок PR, автора и ветки, затем проверь все изменённые файлы на: секреты, инъекции и XSS (безопасность); неэффективные алгоритмы и утечки памяти (производительность); запахи кода и мёртвый код (качество); отсутствующую обработку ошибок; избыточное журналирование или журналирование чувствительных данных; отсутствующую или устаревшую документацию. Для каждой находки укажи путь к файлу, номера строк, проблемный фрагмент и предлагаемое исправление. Если всё в порядке, перечисли, что проверено, и скажи, что выглядит хорошо.

## Доступные эндпоинты API

### Только чтение (безопасно, подтверждение не нужно)

| Эндпоинт | Метод | Описание |
|---|---|---|
| `/2.0/repositories/<workspace>` | GET | Перечислить репозитории рабочей области |
| `/2.0/repositories/<workspace>/<repo>` | GET | Получить сведения о репозитории |
| `/2.0/repositories/<workspace>/<repo>/pullrequests` | GET | Перечислить pull request |
| `/2.0/repositories/<workspace>/<repo>/pullrequests/<id>` | GET | Получить pull request |
| `/2.0/repositories/<workspace>/<repo>/pullrequests/<id>/diff` | GET | Получить дифф PR |
| `/2.0/repositories/<workspace>/<repo>/pullrequests/<id>/commits` | GET | Перечислить коммиты PR |
| `/2.0/repositories/<workspace>/<repo>/pipelines/` | GET | Перечислить запуски конвейеров |
| `/2.0/repositories/<workspace>/<repo>/issues` | GET | Перечислить задачи |

### Изменяющие операции (подтверди у пользователя перед запуском)

| Эндпоинт | Метод | Описание |
|---|---|---|
| `/2.0/repositories/<workspace>/<repo>/pullrequests` | POST | Создать pull request |
| `/2.0/repositories/<workspace>/<repo>/pullrequests/<id>` | PUT | Обновить pull request |
| `/2.0/repositories/<workspace>/<repo>/pullrequests/<id>/comments` | POST | Прокомментировать pull request |
| `/2.0/repositories/<workspace>/<repo>/pullrequests/<id>/merge` | POST | Слить pull request |
| `/2.0/repositories/<workspace>/<repo>/pipelines/` | POST | Запустить конвейер |

### Никогда не запускать — нужно явное согласие человека

| Эндпоинт | Метод | Причина |
|---|---|---|
| `/2.0/repositories/<workspace>/<repo>/pullrequests/<id>/decline` | POST | Закрывает PR без слияния |
| `/2.0/repositories/<workspace>/<repo>` | DELETE | Необратимо удаляет репозиторий |
| `/2.0/repositories/<workspace>/<repo>/pullrequests/<id>` | DELETE | Необратимое удаление PR |
| `/2.0/repositories/<workspace>/<repo>/branch-restrictions/<id>` | DELETE | Снимает правила защиты ветки |

## Правила

- НИКОГДА не обращайся к рабочей области Bitbucket, отличной от настроенной выше. Если URL ссылается на другую рабочую область, остановись и попроси пользователя подтвердить.
- НИКОГДА не печатай, не показывай, не записывай в журнал и не сохраняй содержимое `~/.bitbucket/token` или любое значение учётных данных.
- Всегда читай учётные данные на месте через `$(cat ~/.bitbucket/token)` — никогда не вшивай их в команду.
- Все списочные эндпоинты постраничны (поле `next` в ответе) — иди по URL из `next`, пока оно не исчезнет, чтобы получить все страницы.
- НИКОГДА не сливай, не отклоняй и не удаляй pull request или репозиторий без явного указания пользователя.
- Если слаг репозитория или идентификатор PR незнакомы, сначала найди их запросом только на чтение.
