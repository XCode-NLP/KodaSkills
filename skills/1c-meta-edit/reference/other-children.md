# Значения перечисления и команды

## add-enumValue / add-command

Просто имена (batch через `;;`):
```powershell
-Operation add-enumValue -Value "Значение1 ;; Значение2 ;; Значение3"
-Operation add-command -Value "ОткрытьДосье"
```

Команда создаётся вместе с заготовкой модуля `Commands/<Имя>/Ext/CommandModule.bsl`.

## Формы и макеты — другими навыками

Кроме записи в `ChildObjects` у формы и макета есть собственные файлы, поэтому `1c-meta-edit` их
не добавляет и не удаляет:

| Что | Добавить | Удалить |
|-----|----------|---------|
| Форма | навык `1c-form-add` | навык `1c-form-remove` |
| Макет | навык `1c-template-add` | навык `1c-template-remove` |

Содержимое формы собирает навык `1c-form-compile`.
