# Примеры сообщений для feedback

**Когда читать:** ты составляешь текст для MCP `feedback` по протоколу из `SKILL.md` (раздел «Отзыв о навыке через MCP feedback») и хочешь увидеть, как выглядят хорошо заполненные `problem`/`context` на реальных прогонах. Читай, если сомневаешься, где граница между «сутью проблемы» и «контекстом», либо когда пользователь просил передать его слова и нужно понять, что добавить в `context`, не подменяя его формулировку.

**Что вернуть:** к разделу «Отзыв о навыке через MCP feedback» в `SKILL.md`.

Формат — пункт 1 протокола в `SKILL.md`.

## Пример 1. user-report: вёрстка развалилась при миграции

Инициатор: пользователь. Его слова дословно стали `problem`, агент добавил `context`.

```text
[skill-feedback:v1]
skill=email
skillVersion=1.2.0
source=user-report
problem=Migration from another email platform silently builds the wrong layout: two adjacent images from one row of the source fall apart into a column.
context=Source: a 1200px container, two sibling images of 600px each. The source analysis marked them as two full-width ones, so the generator built two 12+12 rows instead of 6+6. There were no backend errors — the migration was formally "successful", but the rows in the email do not match the source. It repeated on several emails in a row.
area=layout
```

Почему сделано так:

- `problem` — слова пользователя, а не пересказ и не «упаковка» в одно предложение.
- `context` объясняет, **почему** ошибка осталась незамеченной: бэкенд не отказал, разбор исходника выглядел верным, результат оказался просто семантически неверным.
- `area=layout` — область очевидна из описания, поэтому поле включено.

## Пример 2. agent-observation: частичное сохранение при записи

Инициатор: агент. Агент пишет оба поля — он сам увидел проблему и может описать её технически точно.

```text
[skill-feedback:v1]
skill=email-ops
skillVersion=1.2.0
source=agent-observation
problem=visual_template_save can store the visual template but not attach it to the campaign; from the response it is easy to take this for success.
context=One-off campaign in a test project, run 2026-09-02. A save with the campaign's stale `rowVersion` returned ChangeConflict with the verbatim text «The template itself WAS stored — only the campaign was not». A repeated campaign_get showed: the template grew to rowVersion=3, while the body attached to the email stayed at rowVersion=2. The subagent meanwhile reported "saved".
area=save
```

Почему сделано так:

- `problem` — одна-две строки: что именно мешает работе и почему это опасно.
- `context` — проверяемая цепочка: дата, кампания, дословная ошибка, номера версий, чем всё кончилось.
- Факт воспроизведения («прогон 2026-09-02, rowVersion=3 при body=2») идёт в `context`, а не в отдельное поле.

## Пример 3. agent-observation: описание инструмента не совпадает с фактическим DTO

Инициатор: агент. Проблема в документации инструмента, а не в поведении бэкенда; контекст это проясняет.

```text
[skill-feedback:v1]
skill=email-ops
skillVersion=1.2.0
source=agent-observation
problem=The gallery_images_list description promises fields that are not in the actual response — the skill documentation has nothing to rely on.
context=Run 2026-09-02, a test project. The tool description lists size/date; the actual response for the project contained only name, fileExtension, isSystem, url. With a .webp filter, some URLs led to a converted PNG copy, some — directly to the original file. Both kinds of URL are valid for insertion into an email.
area=gallery
```

Почему сделано так:

- `problem` разделяет: инструмент работает, но его описание вводит в заблуждение.
- `context` перечисляет фактический набор полей и наблюдение про `.webp` — именно это разработчик проверит первым.
- Никаких персональных данных, подписанных ссылок и содержимого писем — только фактическая структура ответа.

## Антипримеры

### Антипример 1. Слишком абстрактный `problem`

```text
problem=The gallery works incorrectly.
```

Почему плохо: непонятно, что именно мешает работе — поиск, загрузка, URL, описание инструмента. Разработчик не отличит этот отчёт от десятка похожих.

Как исправить: добавь конкретику — «описание инструмента обещает size/date, которых нет в ответе» (см. пример 3).

### Антипример 2. `context` без входных данных

```text
problem=Two images fell apart into a column.
context=The error was reproduced in a test run.
```

Почему плохо: `context` не отвечает ни на один вопрос — какими были входные данные, какой ширины был контейнер, что вернул бэкенд, на какой кампании воспроизвелось.

Как исправить: добавь контейнер, ширины изображений, отсутствие ошибки бэкенда (см. пример 1).

### Антипример 3. Подмена слов пользователя

Пользователь сказал:

> Картинки из старой платформы рассылок развалились в колонку, когда я переносил письмо.

Неверно:

```text
problem=The layout does not adapt to mobile devices.
```

Почему плохо: агент придумал проблему за пользователя — тот ничего не говорил про мобильные устройства. При `user-report` в `problem` идут его слова дословно; собственную трактовку агент помещает в `context` отдельной фразой.

Верно:

```text
problem=The images from the old email platform fell apart into a column when I was migrating the email.
context=Migration from another email platform, a 1200px container with two sibling images of 600px each. The backend returned no errors, but the result is two full-width rows instead of 6+6.
```
