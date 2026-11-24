---
name: 1c-meta-validate
description: Валидация объекта метаданных 1С. Используй после создания или модификации объекта конфигурации для проверки корректности
allowed-tools: "run_terminal_command read_file"
license: MIT
metadata:
  author: nikolay-shirokov
  source: https://github.com/nikolay-shirokov/cc-1c-skills
  tags: [1c, метаданные, валидация]
---

# /1c-meta-validate — валидация объекта метаданных 1С

Проверяет XML объекта метаданных из выгрузки конфигурации на структурные ошибки.

## Параметры

| Параметр   | Обяз. | Умолч. | Описание                                      |
|------------|:-----:|---------|-------------------------------------------------|
| ObjectPath | да    | —       | Путь к XML-файлу или каталогу. Через `\|` для batch |
| Detailed   | нет   | —       | Подробный вывод (все проверки, включая успешные) |
| MaxErrors  | нет   | 30      | Остановиться после N ошибок (per object)        |
| OutFile    | нет   | —       | Записать результат в файл (UTF-8 BOM)           |

## Команда

```powershell
powershell.exe -NoProfile -File "${CLAUDE_SKILL_DIR}/scripts/meta-validate.ps1" -ObjectPath "Catalogs/Номенклатура/Номенклатура.xml"
powershell.exe -NoProfile -File "${CLAUDE_SKILL_DIR}/scripts/meta-validate.ps1" -ObjectPath "Catalogs/Банки|Documents/Заказ"
```
