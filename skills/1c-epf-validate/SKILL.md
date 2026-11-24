---
name: 1c-epf-validate
description: Валидация внешней обработки 1С (EPF). Используй после создания или модификации обработки для проверки корректности
allowed-tools: "run_terminal_command read_file"
license: MIT
metadata:
  author: nikolay-shirokov
  source: https://github.com/nikolay-shirokov/cc-1c-skills
  tags: [1c, обработка, валидация]
---

# /1c-epf-validate — валидация внешней обработки (EPF)

Проверяет структурную корректность XML-исходников внешней обработки: корневую структуру, InternalInfo, свойства, ChildObjects, реквизиты, табличные части, уникальность имён, наличие файлов форм и макетов. Также работает для внешних отчётов (ERF).

Проверяется XML. Синтаксис модулей проверяет сборка: `/1c-epf-build`, `/1c-erf-build`.

## Параметры

| Параметр   | Обяз. | Умолч. | Описание                                      |
|------------|:-----:|---------|-------------------------------------------------|
| ObjectPath | да    | —       | Путь к корневому XML или каталогу обработки     |
| Detailed   | нет   | —       | Подробный вывод (все проверки, включая успешные) |
| MaxErrors  | нет   | 30      | Остановиться после N ошибок                     |
| OutFile    | нет   | —       | Записать результат в файл (UTF-8 BOM)           |

## Команда

```powershell
powershell.exe -NoProfile -File "${CLAUDE_SKILL_DIR}/scripts/epf-validate.ps1" -ObjectPath "src/МояОбработка"
powershell.exe -NoProfile -File "${CLAUDE_SKILL_DIR}/scripts/epf-validate.ps1" -ObjectPath "src/МояОбработка/МояОбработка.xml"
```

