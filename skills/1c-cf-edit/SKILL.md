---
name: 1c-cf-edit
description: Точечное редактирование конфигурации 1С. Используй когда нужно изменить свойства конфигурации, добавить или удалить объект из состава, настроить роли по умолчанию, поменять раскладку панелей, настроить начальную страницу
allowed-tools: "run_terminal_command read_file create_new_file"
license: MIT
metadata:
  author: nikolay-shirokov
  source: https://github.com/nikolay-shirokov/cc-1c-skills
  tags: [1c, конфигурация, метаданные, редактирование]
---

# /1c-cf-edit — редактирование конфигурации 1С

Точечное редактирование Configuration.xml: свойства, состав ChildObjects, роли по умолчанию.

## Параметры и команда

| Параметр | Описание |
|----------|----------|
| `ConfigPath` | Путь к Configuration.xml или каталогу выгрузки |
| `Operation` | Операция (см. таблицу) |
| `Value` | Значение для операции (batch через `;;`) |
| `DefinitionFile` | JSON-файл с массивом операций |
| `NoValidate` | Пропустить авто-валидацию |

```powershell
powershell.exe -NoProfile -File "${CLAUDE_SKILL_DIR}/scripts/cf-edit.ps1" -ConfigPath '<path>' -Operation modify-property -Value 'Version=1.0.0.1'
```

## Операции

| Операция | Формат Value | Описание |
|----------|-------------|----------|
| `modify-property` | `Ключ=Значение` (batch `;;`) | Изменить свойство |
| `add-childObject` | `Type.Name` (batch `;;`) | Зарегистрировать уже существующий файл объекта в ChildObjects. Для создания нового объекта используй `/1c-meta-compile`, `/1c-role-compile`, `/1c-subsystem-compile` — они регистрируют автоматически |
| `remove-childObject` | `Type.Name` (batch `;;`) | Удалить объект из ChildObjects |
| `sort-childObjects` | вид, напр. `Catalog` (batch `;;`), либо пусто | Упорядочить ChildObjects по имени внутри вида. Без значения — все виды, кроме четырёх (см. reference) |
| `add-defaultRole` | `Role.Name` или `Name` | Добавить роль по умолчанию |
| `remove-defaultRole` | `Role.Name` или `Name` | Удалить роль по умолчанию |
| `set-defaultRoles` | Имена через `;;` | Заменить список ролей по умолчанию |
| `set-panels` | JSON-объект (см. [reference.md](reference.md)) | Перезаписать `Ext/ClientApplicationInterface.xml` (раскладка панелей) |
| `set-home-page` | JSON-объект (см. [reference.md](reference.md)) | Перезаписать `Ext/HomePageWorkArea.xml` (начальная страница) |

Допустимые значения свойств, формат DefinitionFile (JSON), каноничный порядок: [reference.md](reference.md)

## Примеры

```powershell
# Изменить версию и поставщика
... -ConfigPath src -Operation modify-property -Value "Version=1.0.0.1 ;; Vendor=Фирма 1С"

# Добавить объекты
... -ConfigPath src -Operation add-childObject -Value "Catalog.Товары ;; Document.Заказ"

# Удалить объект
... -ConfigPath src -Operation remove-childObject -Value "Catalog.Устаревший"

# Роли по умолчанию
... -ConfigPath src -Operation add-defaultRole -Value "ПолныеПрава"
... -ConfigPath src -Operation set-defaultRoles -Value "ПолныеПрава ;; Администратор"
```
