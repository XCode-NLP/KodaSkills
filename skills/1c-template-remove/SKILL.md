---
name: 1c-template-remove
description: Удалить макет из объекта 1С (обработка, отчёт, справочник, документ и др.)
disable-model-invocation: true
allowed-tools: "run_terminal_command read_file create_new_file edit_file file_glob_search"
license: MIT
metadata:
  author: nikolay-shirokov
  source: https://github.com/nikolay-shirokov/cc-1c-skills
  tags: [1c, макет, удаление]
---

# /1c-template-remove — Удаление макета

Удаляет макет и убирает его регистрацию из корневого XML объекта.

## Usage

```
/1c-template-remove <ObjectName> <TemplateName>
```

| Параметр     | Обязательный | По умолчанию | Описание                            |
|--------------|:------------:|--------------|-------------------------------------|
| ObjectName   | да           | —            | Имя объекта                         |
| TemplateName | да           | —            | Имя макета для удаления             |
| SrcDir       | нет          | `src`        | Каталог исходников                  |

## Команда

```powershell
powershell.exe -NoProfile -File "${CLAUDE_SKILL_DIR}/scripts/remove-template.ps1" -ObjectName "<ObjectName>" -TemplateName "<TemplateName>" [-SrcDir "<SrcDir>"]
```

## Что удаляется

```
<SrcDir>/<ObjectName>/Templates/<TemplateName>.xml     # Метаданные макета
<SrcDir>/<ObjectName>/Templates/<TemplateName>/         # Каталог макета (рекурсивно)
```

## Что модифицируется

- `<SrcDir>/<ObjectName>.xml` — убирается `<Template>` из `ChildObjects`
- Для ExternalReport/Report: если удалённый макет был указан в `MainDataCompositionSchema` — значение очищается
