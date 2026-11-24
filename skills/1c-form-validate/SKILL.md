---
name: 1c-form-validate
description: Валидация управляемой формы 1С. Используй после создания или модификации формы для проверки корректности
allowed-tools: "run_terminal_command read_file"
license: MIT
metadata:
  author: nikolay-shirokov
  source: https://github.com/nikolay-shirokov/cc-1c-skills
  tags: [1c, форма, валидация]
---

# /1c-form-validate — валидация управляемой формы 1С

## Параметры

| Параметр  | Обяз. | Умолч. | Описание                                |
|-----------|:-----:|---------|-----------------------------------------|
| FormPath  | да    | —       | Путь к файлу Form.xml                   |
| Detailed  | нет   | —       | Подробный вывод (все проверки, включая успешные) |
| MaxErrors | нет   | 30      | Остановиться после N ошибок              |

## Команда

```powershell
powershell.exe -NoProfile -File "${CLAUDE_SKILL_DIR}/scripts/form-validate.ps1" -FormPath "Catalogs/Номенклатура/Forms/ФормаЭлемента"
powershell.exe -NoProfile -File "${CLAUDE_SKILL_DIR}/scripts/form-validate.ps1" -FormPath "src/МояОбработка/Forms/Форма/Ext/Form.xml"
```

