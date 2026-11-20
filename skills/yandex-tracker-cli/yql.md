# Язык запросов

`ytcli issue find --yql '<запрос>'` принимает собственный язык фильтров Трекера. Фильтры-флаги (`-q`, `-a`, `-s`, `--tags`) покрывают частую половину; этот — остальное, и он только для чтения: через запрос нельзя ничего записать, как бы он ни был составлен.

Каждый запрос на этой странице был отправлен в настоящий Трекер и принят. Незнакомые Трекеру имена отклоняются с `422` и сообщением `Фильтр <name> не существует`, поэтому неверная догадка стоит одного запроса и прямо говорит, какое слово не так.

## Форма

```bash
ytcli issue find --yql 'Queue: TRACKER AND Status: Open'
ytcli issue find --yql 'Queue: TRACKER AND Assignee: me()'
ytcli issue find --yql 'Queue: TRACKER AND (Status: Open OR Status: "In Progress")'
```

`<параметр>: <значение>`, соединённые `AND` и `OR`. Скобки группируют; без них `AND` связывает крепче `OR`. Пробел между двумя условиями означает `AND`.

Значение с пробелом заключай в кавычки: `Status: "In Progress"`.

## Сравнение

```bash
ytcli issue find --yql 'Queue: TRACKER AND Status: !Closed'
ytcli issue find --yql 'Queue: TRACKER AND Votes: >0'
ytcli issue find --yql 'Queue: TRACKER AND "Story Points": 1..5'
ytcli issue find --yql 'Queue: TRACKER AND Priority: critical, blocker'
```

`!` отрицает. `>`, `<`, `>=`, `<=` сравнивают. `1..5` — числовой диапазон. Несколько значений одного параметра через запятую означают любое из них.

## Функции

```bash
ytcli issue find --yql 'Queue: TRACKER AND Assignee: empty()'
ytcli issue find --yql 'Queue: TRACKER AND Deadline: notEmpty()'
ytcli issue find --yql 'Queue: TRACKER AND Resolution: unresolved()'
ytcli issue find --yql 'Queue: TRACKER AND Updated: week()'
ytcli issue find --yql 'Queue: TRACKER AND Created: today()'
```

`empty()` и `notEmpty()` — заполнено ли поле вообще. `me()` — пользователь самого токена. `unresolved()` — задачи без решения. `today()`, `week()`, `month()`, `quarter()`, `year()` — это интервалы, а не моменты: они совпадают со всем внутри периода.

## Даты

```bash
ytcli issue find --yql 'Queue: TRACKER AND Updated: >now()-7d'
ytcli issue find --yql 'Queue: TRACKER AND Created: >= today() - "1w"'
```

Промежуток записывается как `"XXM XXw XXd XXh XXm XXs"` — `"2M 3d 5h"` это два месяца, три дня, пять часов. Оба написания выше работают; документированное — в кавычках.

## Сортировка

```bash
ytcli issue find --yql 'Queue: TRACKER "Sort By": Updated DESC'
ytcli issue find --yql 'Queue: TRACKER AND Assignee: notEmpty() "Sort By": Created ASC, Updated DESC'
```

`"Sort By"` — такой же параметр, как остальные, в кавычках из-за пробела. Несколько полей через запятую применяются по порядку.

## Имена

Проверены на живой организации:

| что | имена |
|---|---|
| люди | `Assignee`, `Author`, `Followers`, `Modifier`, `"Pending Reply From"` |
| состояние | `Status`, `Resolution`, `Priority`, `Type`, `Key` |
| даты | `Created`, `Updated`, `Resolved`, `Deadline` |
| группировка | `Queue`, `Project`, `Epic`, `Sprint`, `Components`, `Tags` |
| текст | `Summary`, `Description`, `Comment` |
| трудозатраты | `"Story Points"`, `"Original Estimate"`, `"Time Spent"`, `Votes` |

**Имя фильтра — не ключ поля.** `--set storyPoints=3` пишет поле; `"Story Points": 1..5` фильтрует по нему. `StoryPoints` как фильтр — это 422. Эти два словаря раздельные, и `queue fields PROJ` перечисляет только сторону записи.

Не каждое имя есть в каждой организации — фильтр по полю, которое никто не включал, отклоняется так же, как опечатка.

## Цена

`--yql` намеренно конфликтует с фильтрами-флагами: их сочетание либо выбросило бы половину запрошенного, либо придумало бы `AND`, которого никто не писал.

Когда размер ответа важен, спрашивай `issue count --yql '…'` до `issue find --yql '…'`. Это тот же запрос и одно число в ответ.

Результат — страница, и она заканчивается `shown N of M` плюс `next: --page K`, если есть ещё. Короткая страница не доказывает короткий ответ.
