---
name: yougile-update
description: "Изменение задачи в Yougile: название, описание, срок, цвет, признак выполнения или исполнитель. Используй, когда пользователь хочет изменить задачу."
license: MIT
metadata:
  author: Isk4R1oT
  source: https://github.com/Isk4R1oT/YouGlieMCP
---

Измени задачу в Yougile.

Аргументы: `$ARGUMENTS` — код задачи и то, что нужно изменить.

Примеры:
- `/yougile-update ID-582 title: Новое название задачи`
- `/yougile-update ID-582 deadline: 2026-03-25`
- `/yougile-update ID-582 done`
- `/yougile-update ID-582 color: task-red`
- `/yougile-update ID-582 description: Нужно реализовать X`

Шаги:
1. Выдели код задачи и поля для изменения из аргументов
2. Если аргументов нет, спроси пользователя, что менять
3. Определи, что именно нужно изменить:
   - Название — вызови `update_task` с `title`
   - Описание — вызови `update_task` с `description`
   - Срок — вызови `update_task` с `deadline` в формате ISO
   - Цвет — вызови `update_task` с `color`
   - Отметить выполненной («done», «complete») — вызови `complete_task` с `completed: true`
   - Открыть заново («reopen») — вызови `complete_task` с `completed: false`
   - Назначить исполнителя — вызови `assign_task` с `assign`
   - Снять исполнителя — вызови `assign_task` с `unassign`
4. Подтверди: «Задача {code} изменена: {что именно}»
