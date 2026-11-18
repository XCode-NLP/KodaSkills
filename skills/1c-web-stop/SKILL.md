---
name: 1c-web-stop
description: Остановка Apache HTTP Server. Используй когда пользователь просит остановить веб-сервер, Apache, прекратить веб-публикацию
allowed-tools: "run_terminal_command read_file"
license: MIT
metadata:
  author: nikolay-shirokov
  source: https://github.com/nikolay-shirokov/cc-1c-skills
---

# /1c-web-stop — Остановка Apache

Останавливает Apache HTTP Server. Публикации сохраняются — при следующем `/1c-web-publish` сервер запустится снова.

## Usage

```
/1c-web-stop
```

## Параметры подключения

Прочитай `.v8-project.json` из корня проекта. Если задан `webPath` — используй как `-ApachePath`.
По умолчанию `tools/apache24` от корня проекта.

## Команда

```powershell
powershell.exe -NoProfile -File "${CLAUDE_SKILL_DIR}/scripts/web-stop.ps1" <параметры>
```

### Параметры скрипта

| Параметр | Обязательный | Описание |
|----------|:------------:|----------|
| `-ApachePath <путь>` | нет | Корень Apache (по умолчанию `tools/apache24`) |

## После выполнения

Предложи пользователю:
- **Перезапуск** — `/1c-web-publish <база>` (повторный вызов поднимет Apache с существующими публикациями)
- **Удаление публикаций** — `/1c-web-unpublish <имя>` или `/1c-web-unpublish --all`

## Примеры

```powershell
# Остановить Apache
powershell.exe -NoProfile -File "${CLAUDE_SKILL_DIR}/scripts/web-stop.ps1"

# С указанием пути
powershell.exe -NoProfile -File "${CLAUDE_SKILL_DIR}/scripts/web-stop.ps1" -ApachePath "C:\tools\apache24"
```
