---
name: 1c-help-add
description: Добавить встроенную справку к объекту 1С (обработка, отчёт, справочник, документ и др.). Используй когда пользователь просит добавить справку, help, встроенную помощь к объекту
allowed-tools: "run_terminal_command read_file create_new_file edit_file file_glob_search"
license: MIT
metadata:
  author: nikolay-shirokov
  source: https://github.com/nikolay-shirokov/cc-1c-skills
---

# /1c-help-add — Добавление справки

Добавляет встроенную справку к объекту: файл метаданных `Help.xml`, HTML-страницу и при необходимости обновляет метаданные форм.

## Usage

```
/1c-help-add <ObjectName> [Lang] [SrcDir]
```

| Параметр   | Обязательный | По умолчанию | Описание                            |
|------------|:------------:|--------------|-------------------------------------|
| ObjectName | да           | —            | Путь объекта относительно SrcDir (например `Catalogs/МойСправочник`, `DataProcessors/МояОбработка`) |
| Lang       | нет          | `ru`         | Код языка справки                   |
| SrcDir     | нет          | `src`        | Каталог исходников                  |

## Команда

```powershell
powershell.exe -NoProfile -File "${CLAUDE_SKILL_DIR}/scripts/add-help.ps1" -ObjectName "<ObjectName>" [-Lang "<Lang>"] [-SrcDir "<SrcDir>"]
```

## Что делает скрипт

- Создаёт `Ext/Help.xml` и `Ext/Help/ru.html` — шаблон справки
- Если у объекта есть формы — добавляет `<IncludeHelpInContents>` в метаданные форм (если отсутствует)
- Справка **не регистрируется** в `ChildObjects` — достаточно наличия файлов

## После запуска

Отредактируй `Ext/Help/ru.html` — наполни содержимым справки (стандартный HTML: `<h1>`..`<h4>`, `<p>`, `<ul>`, `<table>` и т.д.). Кнопка справки появится автоматически через `Autofill` в AutoCommandBar формы.
