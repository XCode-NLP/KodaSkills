---
name: yougile-move
description: "Перемещение задачи в другую колонку Yougile. Используй, когда пользователь хочет изменить статус задачи или перенести её между колонками."
license: MIT
metadata:
  author: Isk4R1oT
  source: https://github.com/Isk4R1oT/YouGlieMCP
---

Перемести задачу в другую колонку Yougile.

Аргументы: `$ARGUMENTS` — код задачи и название целевой колонки.

Примеры:
- `/yougile-move ID-582 In Progress`
- `/yougile-move ID-1061 Testing`

Шаги:
1. Выдели код задачи и целевую колонку из `$ARGUMENTS`
2. Если аргументов нет или они неоднозначны, попроси указать код задачи и колонку
3. Вызови `move_task` с параметрами `task` и `column`
4. Подтверди перемещение: «Задача {code} перемещена в «{column}»»
