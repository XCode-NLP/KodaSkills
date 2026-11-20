# PPTX

Документация: <https://python-pptx.readthedocs.io/>, <https://gitbrent.github.io/PptxGenJS/>.

PPTX — это ZIP-архив с XML-файлами Office Open XML.
Презентация состоит из слайдов, макетов, темы и связей.

## Что внутри

| Путь                    | Назначение               |
|-------------------------|--------------------------|
| `ppt/presentation.xml`  | Список слайдов и размеры |
| `ppt/slides/slide*.xml` | Содержимое слайдов       |
| `ppt/slideLayouts/`     | Макеты                   |
| `ppt/slideMasters/`     | Мастера                  |
| `ppt/theme/`            | Тема, шрифты и цвета     |
| `ppt/media/`            | Изображения и видео      |
| `ppt/notesSlides/`      | Заметки докладчика       |

## python-pptx

```bash
pip install python-pptx
```

Создание презентации:

```python
from pptx import Presentation
from pptx.util import Inches, Pt

presentation = Presentation()
presentation.slide_width = Inches(13.333)
presentation.slide_height = Inches(7.5)

title_slide = presentation.slides.add_slide(presentation.slide_layouts[0])
title_slide.shapes.title.text = "Итоги квартала"
title_slide.placeholders[1].text = "Отдел продаж · ноябрь 2026"

content_slide = presentation.slides.add_slide(presentation.slide_layouts[1])
content_slide.shapes.title.text = "Ключевые результаты"
frame = content_slide.placeholders[1].text_frame
frame.text = "Выручка выросла на 18%"
paragraph = frame.add_paragraph()
paragraph.text = "Новых клиентов: 24"
paragraph.level = 1
paragraph.font.size = Pt(20)

presentation.save("report.pptx")
```

Открытие и правка:

```python
from pptx import Presentation

presentation = Presentation("report.pptx")
for index, slide in enumerate(presentation.slides, start=1):
    print(f"Слайд {index}")
    for shape in slide.shapes:
        if shape.has_text_frame:
            print(shape.text_frame.text)
```

## Макеты и местозаполнители

- `slide_layouts[0]` — титульный слайд.
- `slide_layouts[1]` — заголовок и содержимое.
- `slide_layouts[5]` — только заголовок.
- `slide_layouts[6]` — пустой слайд.
- Конкретный набор зависит от шаблона. Не полагайся на индексы, если используешь корпоративный шаблон: перечисли макеты и выбери по имени.

```python
for index, layout in enumerate(presentation.slide_layouts):
    print(index, layout.name)
```

Местозаполнители задают позиции и стили. Используй их вместо абсолютного позиционирования.
Если нужен свободный макет, добавляй текстовые блоки через `add_textbox`, но тогда сам отвечаешь за шрифты и отступы.

## Текст

- `text_frame.text` заменяет весь текст.
- `add_paragraph()` добавляет абзац.
- `paragraph.level` задаёт уровень списка.
- `run.font` управляет шрифтом, размером, цветом и начертанием.
- Для переноса строк используй отдельные абзацы, а не `\n` внутри run.
- `text_frame.word_wrap = True` включает перенос.
- `text_frame.auto_size` помогает подогнать текст, но результат зависит от редактора.

```python
from pptx.dml.color import RGBColor
from pptx.util import Pt

paragraph = frame.add_paragraph()
run = paragraph.add_run()
run.text = "Важно"
run.font.bold = True
run.font.size = Pt(24)
run.font.color.rgb = RGBColor(0xC0, 0x00, 0x00)
```

## Таблицы

```python
rows, cols = 4, 3
table_shape = slide.shapes.add_table(rows, cols, Inches(1), Inches(2), Inches(11), Inches(2))
table = table_shape.table

headers = ["Показатель", "План", "Факт"]
for column, value in enumerate(headers):
    table.cell(0, column).text = value

data = [
    ("Выручка", "10 млн", "11,8 млн"),
    ("Клиенты", "20", "24"),
    ("Маржа", "30%", "32%"),
]
for row, values in enumerate(data, start=1):
    for column, value in enumerate(values):
        table.cell(row, column).text = value
```

- Ширину столбцов задавай через `table.columns[i].width`.
- Высоту строк — через `table.rows[i].height`.
- Объединение ячеек: `table.cell(0, 0).merge(table.cell(0, 1))`.
- Стиль таблицы задаётся темой; не рассчитывай на точные цвета без проверки.

## Изображения и диаграммы

```python
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE
from pptx.util import Inches

slide.shapes.add_picture("chart.png", Inches(1), Inches(2), width=Inches(6))

chart_data = CategoryChartData()
chart_data.categories = ["Q1", "Q2", "Q3", "Q4"]
chart_data.add_series("Выручка", (10, 12, 11, 14))
slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(1), Inches(2), Inches(8), Inches(4), chart_data)
```

- Для диаграмм используй `CategoryChartData` и типы `XL_CHART_TYPE`.
- Диаграмма в PPTX — это объект с данными, а не картинка. Редактировать её можно в PowerPoint.
- Для сложных диаграмм проще подготовить изображение, но тогда потеряется редактируемость.
- Проверяй, что изображение не растянуто и не обрезано.

## Заметки докладчика

```python
notes = slide.notes_slide.notes_text_frame
notes.text = "Рассказать про рост выручки и новых клиентов."
```

Заметки не видны на слайде, но полезны для экспорта в PDF с заметками.

## PptxGenJS (Node.js)

```js
import pptxgen from 'pptxgenjs';

const presentation = new pptxgen();
presentation.layout = 'LAYOUT_WIDE';

const slide = presentation.addSlide();
slide.addText('Итоги квартала', { x: 0.5, y: 0.5, w: 12, h: 1, fontSize: 32, bold: true });
slide.addText('Выручка выросла на 18%', { x: 0.5, y: 1.8, w: 12, h: 1, fontSize: 20 });
slide.addTable(
  [
    ['Показатель', 'План', 'Факт'],
    ['Выручка', '10 млн', '11,8 млн'],
  ],
  { x: 0.5, y: 3, w: 12, border: { pt: 1, color: '999999' } },
);

await presentation.writeFile({ fileName: 'report.pptx' });
```

`PptxGenJS` удобен для генерации с нуля. Для правки существующего шаблона он подходит хуже, чем `python-pptx`.

## Ограничения

- `python-pptx` не поддерживает анимации и переходы.
- SmartArt, некоторые эффекты и трёхмерные объекты могут не читаться.
- Правка существующих слайдов ограничена: библиотека не всегда сохраняет сложные элементы.
- Точная вёрстка зависит от шрифтов и версии PowerPoint.
- Автоподбор текста работает по-разному в PowerPoint, LibreOffice и Keynote.

## Шаблоны

Лучший способ получить корпоративный стиль — использовать готовый `.pptx` как шаблон.

1. Открой шаблон через `Presentation("template.pptx")`.
2. Выбери макет по имени.
3. Заполняй местозаполнители, не добавляй новые текстовые блоки без необходимости.
4. Удаляй лишние слайды, если шаблон содержит примеры.
5. Проверь тему, шрифты и цвета.

```python
presentation = Presentation("template.pptx")
layout = next(layout for layout in presentation.slide_layouts if layout.name == "Title and Content")
slide = presentation.slides.add_slide(layout)
```

## Проверка результата

1. Открой презентацию в PowerPoint, LibreOffice или Keynote.
2. Проверь, что текст не выходит за границы и не накладывается.
3. Проверь шрифты и кириллицу.
4. Проверь таблицы, изображения и диаграммы.
5. Проверь заметки и порядок слайдов.
6. Экспортируй в PDF и просмотри страницы.

## Частые ошибки

| Симптом                    | Причина                                 | Решение                                      |
|----------------------------|-----------------------------------------|----------------------------------------------|
| Текст вылезает за слайд    | Слишком большой шрифт или длинный текст | Уменьши шрифт, включи перенос, сократи текст |
| Пропали стили              | Слайд создан с пустого макета           | Используй макет и местозаполнители           |
| Шрифт подменился           | Шрифта нет на машине                    | Используй стандартный шрифт или встрой его   |
| Диаграмма не редактируется | Вставлена как картинка                  | Используй объект диаграммы                   |
| Не сохранились анимации    | Библиотека их не поддерживает           | Правь в PowerPoint вручную                   |
| Слайды идут не по порядку  | Неверный порядок XML                    | Используй API для перемещения слайдов        |
| Пустые местозаполнители    | Макет содержит лишние поля              | Удали пустые местозаполнители                |
