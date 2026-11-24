---
name: 1c-cfe-validate
description: Валидация расширения конфигурации 1С (CFE). Используй после создания или модификации расширения для проверки корректности
allowed-tools: "run_terminal_command read_file"
license: MIT
metadata:
  author: nikolay-shirokov
  source: https://github.com/nikolay-shirokov/cc-1c-skills
  tags: [1c, расширение, валидация]
---

# /1c-cfe-validate — валидация расширения конфигурации (CFE)

Проверяет структурную корректность расширения: XML-формат, свойства, состав, заимствованные объекты, права ролей. Аналог `/1c-cf-validate`, но для расширений.

Проверяются исходники. Применимость — уже после загрузки в базу: `/1c-db-cfe-admin check`.

## Параметры

| Параметр      | Обяз. | Умолч. | Описание                                        |
|---------------|:-----:|---------|-------------------------------------------------|
| ExtensionPath | да    | —       | Путь к каталогу или Configuration.xml расширения |
| ConfigPath    | нет   | —       | Каталог конфигурации, из которой заимствованы объекты |
| Detailed      | нет   | —       | Подробный вывод (все проверки, включая успешные)  |
| MaxErrors     | нет   | 30      | Остановиться после N ошибок                      |
| OutFile       | нет   | —       | Записать результат в файл                        |

### ConfigPath

Указывай всегда, когда конфигурация-источник доступна: по ней сверяется связь заимствованных объектов с объектами конфигурации и основной язык. Без неё такие расхождения не ловятся, и расширение может пройти валидацию, а потом быть отвергнутым платформой.

Если пользователь не указал путь — определи сам:
1. Прочитай `.v8-project.json` из корня проекта
2. Разреши целевую базу (по имени, ветке или `default`)
3. Возьми её поле `configSrc`

## Команда

```powershell
powershell.exe -NoProfile -File "${CLAUDE_SKILL_DIR}/scripts/cfe-validate.ps1" -ExtensionPath "src\cfe\extname"
powershell.exe -NoProfile -File "${CLAUDE_SKILL_DIR}/scripts/cfe-validate.ps1" -ExtensionPath "src\cfe\extname\Configuration.xml"
powershell.exe -NoProfile -File "${CLAUDE_SKILL_DIR}/scripts/cfe-validate.ps1" -ExtensionPath "src\cfe\extname" -ConfigPath "src\cf"
```
