# DOCX

Документация: <https://python-docx.readthedocs.io/>, <https://docxtpl.readthedocs.io/>.

DOCX — это ZIP-архив с XML-файлами Office Open XML.
Не редактируй его как обычный текст: используй библиотеку.

## Что внутри

| Путь                                   | Назначение               |
|----------------------------------------|--------------------------|
| `[Content_Types].xml`                  | Типы частей пакета       |
| `_rels/.rels`                          | Связи верхнего уровня    |
| `word/document.xml`                    | Основной текст документа |
| `word/styles.xml`                      | Стили                    |
| `word/numbering.xml`                   | Нумерация списков        |
| `word/settings.xml`                    | Настройки документа      |
| `word/header*.xml`, `word/footer*.xml` | Колонтитулы              |
| `word/media/`                          | Изображения              |
| `word/theme/`                          | Тема и шрифты            |

Можно распаковать файл и посмотреть структуру, но собирать его обратно вручную не стоит.

## python-docx

```bash
pip install python-docx
```

Создание документа:

```python
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH

document = Document()
style = document.styles["Normal"]
style.font.name = "Times New Roman"
style.font.size = Pt(12)

heading = document.add_heading("Отчёт", level=1)
heading.alignment = WD_ALIGN_PARAGRAPH.CENTER

paragraph = document.add_paragraph("Первый абзац. ")
run = paragraph.add_run("Важная часть")
run.bold = True
run.italic = True

document.add_page_break()
document.add_paragraph("Вторая страница")

table = document.add_table(rows=1, cols=3)
table.style = "Table Grid"
header = table.rows[0].cells
header[0].text = "Наименование"
header[1].text = "Количество"
header[2].text = "Цена"

row = table.add_row().cells
row[0].text = "Болты"
row[1].text = "100"
row[2].text = "12,50"

document.save("report.docx")
```

Чтение:

```python
from docx import Document

document = Document("input.docx")
for paragraph in document.paragraphs:
    print(paragraph.style.name, paragraph.text)

for table in document.tables:
    for row in table.rows:
        print([cell.text for cell in row.cells])
```

## Стили

- Используй стили из шаблона, а не ручное форматирование каждого абзаца.
- Лучший способ получить корпоративный вид — открыть готовый `.docx` как шаблон и добавлять контент в него.
- `document.styles` позволяет менять существующие стили и создавать новые.
- Для шрифтов с кириллицей задавай `w:eastAsia` и `w:cs`, если документ должен одинаково выглядеть в разных редакторах.
- Не рассчитывай, что шрифт установлен на машине получателя. Для печати встраивай шрифты или используй стандартные.

## Таблицы

- `table.style = "Table Grid"` включает видимые границы.
- Ширину столбцов задавай через `cell.width` и `table.autofit = False`.
- Объединение ячеек: `cell_a.merge(cell_b)`.
- Для повторяющейся шапки используй `table.rows[0]._tr.get_or_add_trPr()` и `tblHeader`.
- Вложенные таблицы лучше не строить: они плохо переносятся между редакторами.

## Изображения

```python
from docx.shared import Cm

document.add_picture("chart.png", width=Cm(16))
```

- Указывай ширину или высоту, чтобы не получить гигантскую картинку.
- Для печати используй изображения с разрешением не ниже 150–300 DPI.
- Не вставляй SVG без проверки: поддержка зависит от версии Word и библиотеки.
- Подпись к рисунку делай отдельным абзацем со стилем `Caption`.

## Колонтитулы и нумерация страниц

```python
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

section = document.sections[0]
footer = section.footer
paragraph = footer.paragraphs[0]
paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

run = paragraph.add_run()
field_begin = OxmlElement("w:fldChar")
field_begin.set(qn("w:fldCharType"), "begin")
field_instr = OxmlElement("w:instrText")
field_instr.set(qn("xml:space"), "preserve")
field_instr.text = "PAGE"
field_end = OxmlElement("w:fldChar")
field_end.set(qn("w:fldCharType"), "end")
run._r.append(field_begin)
run._r.append(field_instr)
run._r.append(field_end)
```

`python-docx` не имеет высокоуровневого API для полей, поэтому номер страницы добавляется через XML.
После вставки поля открой документ в Word или LibreOffice: некоторые редакторы обновляют поле только при открытии или печати.

## Гиперссылки

В `python-docx` нет прямого метода для гиперссылки. Добавляй её через XML-связь:

```python
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT


def add_hyperlink(paragraph, url: str, text: str) -> None:
    part = paragraph.part
    relationship_id = part.relate_to(url, RT.HYPERLINK, is_external=True)

    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), relationship_id)

    run = OxmlElement("w:r")
    run_properties = OxmlElement("w:rPr")
    color = OxmlElement("w:color")
    color.set(qn("w:val"), "0563C1")
    underline = OxmlElement("w:u")
    underline.set(qn("w:val"), "single")
    run_properties.append(color)
    run_properties.append(underline)

    text_element = OxmlElement("w:t")
    text_element.text = text
    run.append(run_properties)
    run.append(text_element)
    hyperlink.append(run)
    paragraph._p.append(hyperlink)
```

## Шаблоны с docxtpl

`docxtpl` использует Jinja2 и позволяет заполнять готовый DOCX.

```python
from docxtpl import DocxTemplate

template = DocxTemplate("template.docx")
template.render(
    {
        "title": "Договор поставки",
        "number": "42/2026",
        "items": [
            {"name": "Болты", "quantity": 100, "price": "12,50"},
            {"name": "Гайки", "quantity": 200, "price": "8,00"},
        ],
    }
)
template.save("contract.docx")
```

В шаблоне:

```text
{{ title }} № {{ number }}

{% for item in items %}
{{ item.name }} — {{ item.quantity }} шт. по {{ item.price }} руб.
{% endfor %}
```

- Синтаксис Jinja2 чувствителен к пробелам и переносам строк.
- Для циклов в таблицах используй `{%tr for %}` и `{%tr endfor %}`, чтобы повторять строку таблицы.
- Для изображений используй `InlineImage`.
- Не передавай в шаблон недоверенные строки без экранирования, если они попадают в XML-разметку.

## Чтение и конвертация

| Инструмент    | Что делает                                       |
|---------------|--------------------------------------------------|
| `python-docx` | Читает параграфы, таблицы, стили, изображения    |
| `docx2txt`    | Извлекает простой текст                          |
| `mammoth`     | Конвертирует DOCX в HTML с сохранением структуры |
| Pandoc        | Конвертирует DOCX в Markdown, HTML и обратно     |
| LibreOffice   | Конвертирует DOCX в PDF и другие форматы         |

`mammoth` не гарантирует точную вёрстку: он ориентирован на семантический HTML, а не на копию страницы.

## Ограничения python-docx

- Не работает со старым бинарным форматом `.doc`: сначала конвертируй его в `.docx` через LibreOffice.
- Нет полноценной поддержки комментариев и отслеживаемых изменений.
- Нет высокоуровневого API для полей, оглавления и гиперссылок.
- Ограниченная поддержка сложных стилей, диаграмм и SmartArt.
- Не пересчитывает оглавление и поля.
- Не гарантирует идеальную совместимость с Word во всех сценариях.

Если нужна сложная вёрстка, используй шаблон DOCX, docx4j, Apache POI или LibreOffice.

## Проверка результата

1. Открой файл в LibreOffice и Word, если доступен.
2. Проверь текст, таблицы, изображения, колонтитулы и нумерацию страниц.
3. Проверь разрывы страниц и переносы.
4. Проверь, что шрифты не подменились.
5. Для шаблонов проверь пустые значения и циклы с нулём элементов.

## Частые ошибки

| Симптом                        | Причина                    | Решение                                  |
|--------------------------------|----------------------------|------------------------------------------|
| Файл не открывается            | Повреждён XML или ZIP      | Не редактируй DOCX как текст             |
| Пропали стили                  | Документ пересоздан с нуля | Открывай существующий шаблон             |
| Нет номера страницы            | Поле не обновлено          | Открой в Word или обнови поля            |
| Гиперссылка не работает        | Добавлен только текст      | Добавь XML-связь                         |
| Таблица разъехалась            | Не задана ширина и autofit | Задай ширины и отключи autofit           |
| Кириллица в квадратах          | Нет шрифта в системе       | Установи шрифт или используй стандартный |
| Шаблон падает на пустом списке | Нет проверки в Jinja2      | Используй `{% if items %}`               |
