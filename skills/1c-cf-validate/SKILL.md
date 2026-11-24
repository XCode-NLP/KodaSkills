---
name: 1c-cf-validate
description: Валидация конфигурации 1С. Используй после создания или модификации конфигурации для проверки корректности
allowed-tools: "run_terminal_command read_file"
license: MIT
metadata:
  author: nikolay-shirokov
  source: https://github.com/nikolay-shirokov/cc-1c-skills
  tags: [1c, конфигурация, валидация]
---

# /1c-cf-validate — валидация конфигурации 1С

Проверяет Configuration.xml на структурные ошибки: XML well-formedness, InternalInfo, свойства, enum-значения, ChildObjects, DefaultLanguage, файлы языков, каталоги объектов.

## Параметры

| Параметр   | Обяз. | Умолч. | Описание                                      |
|------------|:-----:|---------|-------------------------------------------------|
| ConfigPath | да    | —       | Путь к Configuration.xml или каталогу выгрузки  |
| Detailed   | нет   | —       | Подробный вывод (все проверки, включая успешные) |
| MaxErrors  | нет   | 30      | Остановиться после N ошибок                     |
| OutFile    | нет   | —       | Записать результат в файл (UTF-8 BOM)           |

## Команда

```powershell
powershell.exe -NoProfile -File "${CLAUDE_SKILL_DIR}/scripts/cf-validate.ps1" -ConfigPath "upload/cfempty"
powershell.exe -NoProfile -File "${CLAUDE_SKILL_DIR}/scripts/cf-validate.ps1" -ConfigPath "upload/cfempty/Configuration.xml"
```
