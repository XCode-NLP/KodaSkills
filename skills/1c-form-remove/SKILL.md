---
name: 1c-form-remove
description: Удалить форму из объекта 1С (обработка, отчёт, справочник, документ и др.)
disable-model-invocation: true
allowed-tools: "run_terminal_command read_file create_new_file edit_file file_glob_search"
license: MIT
metadata:
  author: nikolay-shirokov
  source: https://github.com/nikolay-shirokov/cc-1c-skills
  tags: [1c, форма, удаление]
---

# /1c-form-remove — Удаление формы

Удаляет форму и убирает её регистрацию из корневого XML объекта.

## Usage

```
/1c-form-remove <ObjectName> <FormName>
```

| Параметр   | Обязательный | По умолчанию | Описание                            |
|------------|:------------:|--------------|-------------------------------------|
| ObjectName | да           | —            | Имя объекта                         |
| FormName   | да           | —            | Имя формы для удаления              |
| SrcDir     | нет          | `src`        | Каталог исходников                  |
| Force      | нет          | —            | Удалить, даже если на форму ссылаются, и очистить ссылки |

## Команда

```powershell
powershell.exe -NoProfile -File "${CLAUDE_SKILL_DIR}/scripts/remove-form.ps1" -ObjectName "<ObjectName>" -FormName "<FormName>" [-SrcDir "<SrcDir>"] [-Force]
```

## Что удаляется

```
<SrcDir>/<ObjectName>/Forms/<FormName>.xml     # Метаданные формы
<SrcDir>/<ObjectName>/Forms/<FormName>/         # Каталог формы (рекурсивно)
```

## Что модифицируется

- `<SrcDir>/<ObjectName>.xml` — убирается `<Form>` из `ChildObjects`
- Свойства объекта, указывавшие на удалённую форму — очищаются
