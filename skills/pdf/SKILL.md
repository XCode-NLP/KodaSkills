---
name: pdf
description: "Работа с PDF-файлами: чтение, извлечение текста и таблиц, объединение и разделение, поворот страниц, водяные знаки, создание новых PDF, заполнение форм, шифрование и расшифровка, извлечение изображений, OCR сканов для поиска по тексту. Используй, если упомянут файл `.pdf` или нужно его получить. Триггеры: PDF, пдф, извлечь текст из PDF, склеить PDF, разбить PDF, форма PDF, скан, распознать текст в PDF."
license: Apache-2.0
metadata:
  author: anthropic
  source: https://github.com/anthropics/skills
---

# Работа с PDF

## Обзор

Здесь собраны основные операции с PDF на Python и в командной строке. Продвинутые возможности, JavaScript-библиотеки и подробные примеры — в `REFERENCE.md`. Если нужно заполнить форму PDF, прочитай `FORMS.md` и следуй его инструкциям.

## Быстрый старт

```python
from pypdf import PdfReader, PdfWriter

# Чтение PDF
reader = PdfReader("document.pdf")
print(f"Страниц: {len(reader.pages)}")

# Извлечение текста
text = ""
for page in reader.pages:
    text += page.extract_text()
```

## Библиотеки Python

### pypdf — базовые операции

#### Объединение PDF

```python
from pypdf import PdfWriter, PdfReader

writer = PdfWriter()
for pdf_file in ["doc1.pdf", "doc2.pdf", "doc3.pdf"]:
    reader = PdfReader(pdf_file)
    for page in reader.pages:
        writer.add_page(page)

with open("merged.pdf", "wb") as output:
    writer.write(output)
```

#### Разделение PDF

```python
reader = PdfReader("input.pdf")
for i, page in enumerate(reader.pages):
    writer = PdfWriter()
    writer.add_page(page)
    with open(f"page_{i+1}.pdf", "wb") as output:
        writer.write(output)
```

#### Метаданные

```python
reader = PdfReader("document.pdf")
meta = reader.metadata
print(f"Заголовок: {meta.title}")
print(f"Автор: {meta.author}")
print(f"Тема: {meta.subject}")
print(f"Создатель: {meta.creator}")
```

#### Поворот страниц

```python
reader = PdfReader("input.pdf")
writer = PdfWriter()

page = reader.pages[0]
page.rotate(90)  # поворот на 90 градусов по часовой стрелке
writer.add_page(page)

with open("rotated.pdf", "wb") as output:
    writer.write(output)
```

### pdfplumber — извлечение текста и таблиц

#### Текст с сохранением расположения

```python
import pdfplumber

with pdfplumber.open("document.pdf") as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        print(text)
```

#### Таблицы

```python
with pdfplumber.open("document.pdf") as pdf:
    for i, page in enumerate(pdf.pages):
        tables = page.extract_tables()
        for j, table in enumerate(tables):
            print(f"Таблица {j+1} на странице {i+1}:")
            for row in table:
                print(row)
```

#### Продвинутое извлечение таблиц

```python
import pandas as pd

with pdfplumber.open("document.pdf") as pdf:
    all_tables = []
    for page in pdf.pages:
        tables = page.extract_tables()
        for table in tables:
            if table:  # проверяем, что таблица не пустая
                df = pd.DataFrame(table[1:], columns=table[0])
                all_tables.append(df)

# Объединяем все таблицы
if all_tables:
    combined_df = pd.concat(all_tables, ignore_index=True)
    combined_df.to_excel("extracted_tables.xlsx", index=False)
```

### reportlab — создание PDF

#### Простой PDF

```python
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

c = canvas.Canvas("hello.pdf", pagesize=letter)
width, height = letter

# Текст
c.drawString(100, height - 100, "Hello World!")
c.drawString(100, height - 120, "This is a PDF created with reportlab")

# Линия
c.line(100, height - 140, 400, height - 140)

# Сохранение
c.save()
```

#### PDF из нескольких страниц

```python
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet

doc = SimpleDocTemplate("report.pdf", pagesize=letter)
styles = getSampleStyleSheet()
story = []

# Содержимое
title = Paragraph("Report Title", styles['Title'])
story.append(title)
story.append(Spacer(1, 12))

body = Paragraph("This is the body of the report. " * 20, styles['Normal'])
story.append(body)
story.append(PageBreak())

# Вторая страница
story.append(Paragraph("Page 2", styles['Heading1']))
story.append(Paragraph("Content for page 2", styles['Normal']))

# Сборка PDF
doc.build(story)
```

#### Нижние и верхние индексы

**ВАЖНО**: никогда не используй символы Unicode для индексов (₀₁₂₃₄₅₆₇₈₉, ⁰¹²³⁴⁵⁶⁷⁸⁹) в PDF на ReportLab. Встроенные шрифты не содержат этих глифов, и они отрисуются сплошными чёрными прямоугольниками.

Вместо этого используй XML-теги ReportLab в объектах `Paragraph`:

```python
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet

styles = getSampleStyleSheet()

# Нижний индекс: тег <sub>
chemical = Paragraph("H<sub>2</sub>O", styles['Normal'])

# Верхний индекс: тег <super>
squared = Paragraph("x<super>2</super> + y<super>2</super>", styles['Normal'])
```

Для текста, нарисованного через canvas (не через `Paragraph`), вручную подбирай размер шрифта и позицию вместо символов Unicode.

## Инструменты командной строки

### pdftotext (poppler-utils)

```bash
# Извлечение текста
pdftotext input.pdf output.txt

# Извлечение текста с сохранением расположения
pdftotext -layout input.pdf output.txt

# Только нужные страницы
pdftotext -f 1 -l 5 input.pdf output.txt  # страницы 1-5
```

### qpdf

```bash
# Объединение PDF
qpdf --empty --pages file1.pdf file2.pdf -- merged.pdf

# Разделение страниц
qpdf input.pdf --pages . 1-5 -- pages1-5.pdf
qpdf input.pdf --pages . 6-10 -- pages6-10.pdf

# Поворот страниц
qpdf input.pdf output.pdf --rotate=+90:1  # поворот страницы 1 на 90 градусов

# Удаление пароля
qpdf --password=mypassword --decrypt encrypted.pdf decrypted.pdf
```

### pdftk (если установлен)

```bash
# Объединение
pdftk file1.pdf file2.pdf cat output merged.pdf

# Разделение
pdftk input.pdf burst

# Поворот
pdftk input.pdf rotate 1east output rotated.pdf
```

## Частые задачи

### Текст из сканированных PDF

```python
# Требуется: pip install pytesseract pdf2image
import pytesseract
from pdf2image import convert_from_path

# Преобразование PDF в изображения
images = convert_from_path('scanned.pdf')

# OCR каждой страницы
text = ""
for i, image in enumerate(images):
    text += f"Page {i+1}:\n"
    text += pytesseract.image_to_string(image)
    text += "\n\n"

print(text)
```

### Водяной знак

```python
from pypdf import PdfReader, PdfWriter

# Создание водяного знака (или загрузка готового)
watermark = PdfReader("watermark.pdf").pages[0]

# Применение ко всем страницам
reader = PdfReader("document.pdf")
writer = PdfWriter()

for page in reader.pages:
    page.merge_page(watermark)
    writer.add_page(page)

with open("watermarked.pdf", "wb") as output:
    writer.write(output)
```

### Извлечение изображений

```bash
# Через pdfimages (poppler-utils)
pdfimages -j input.pdf output_prefix

# Все изображения сохранятся как output_prefix-000.jpg, output_prefix-001.jpg и так далее
```

### Защита паролем

```python
from pypdf import PdfReader, PdfWriter

reader = PdfReader("input.pdf")
writer = PdfWriter()

for page in reader.pages:
    writer.add_page(page)

# Добавление пароля
writer.encrypt("userpassword", "ownerpassword")

with open("encrypted.pdf", "wb") as output:
    writer.write(output)
```

## Краткая справка

| Задача                        | Лучший инструмент                  | Команда или код                     |
|-------------------------------|------------------------------------|-------------------------------------|
| Объединить PDF                | pypdf                              | `writer.add_page(page)`             |
| Разделить PDF                 | pypdf                              | одна страница на файл               |
| Извлечь текст                 | pdfplumber                         | `page.extract_text()`               |
| Извлечь таблицы               | pdfplumber                         | `page.extract_tables()`             |
| Создать PDF                   | reportlab                          | Canvas или Platypus                 |
| Объединить в командной строке | qpdf                               | `qpdf --empty --pages ...`          |
| OCR сканов                    | pytesseract                        | сначала преобразовать в изображение |
| Заполнить форму PDF           | pdf-lib или pypdf (см. `FORMS.md`) | см. `FORMS.md`                      |

## Дополнительные материалы

- Продвинутое использование `pypdfium2` — в `REFERENCE.md`.
- JavaScript-библиотеки (`pdf-lib`) — в `REFERENCE.md`.
- Если нужно заполнить форму PDF, следуй инструкциям в `FORMS.md`.
- Руководство по диагностике проблем — в `REFERENCE.md`.
