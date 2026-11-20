# Продвинутая работа с PDF

Здесь собраны продвинутые возможности обработки PDF, подробные примеры и дополнительные библиотеки, которых нет в основной инструкции навыка.

## Библиотека pypdfium2 (лицензия Apache/BSD)

### Обзор

`pypdfium2` — привязка Python к PDFium (библиотеке PDF из Chromium). Хорошо подходит для быстрого рендеринга PDF и создания изображений, а также служит заменой PyMuPDF.

### Рендеринг PDF в изображения

```python
import pypdfium2 as pdfium
from PIL import Image

# Загрузка PDF
pdf = pdfium.PdfDocument("document.pdf")

# Рендеринг страницы в изображение
page = pdf[0]  # первая страница
bitmap = page.render(
    scale=2.0,  # выше разрешение
    rotation=0  # без поворота
)

# Преобразование в PIL Image
img = bitmap.to_pil()
img.save("page_1.png", "PNG")

# Обработка нескольких страниц
for i, page in enumerate(pdf):
    bitmap = page.render(scale=1.5)
    img = bitmap.to_pil()
    img.save(f"page_{i+1}.jpg", "JPEG", quality=90)
```

### Извлечение текста через pypdfium2

```python
import pypdfium2 as pdfium

pdf = pdfium.PdfDocument("document.pdf")
for i, page in enumerate(pdf):
    textpage = page.get_textpage()
    text = textpage.get_text_range()
    print(f"Page {i+1} text length: {len(text)} chars")
```

## Библиотеки JavaScript

### pdf-lib (лицензия MIT)

`pdf-lib` — мощная библиотека JavaScript для создания и изменения PDF в любой среде JavaScript.

#### Загрузка и изменение готового PDF

```javascript
import { PDFDocument } from 'pdf-lib';
import fs from 'fs';

async function manipulatePDF() {
    // Загрузка готового PDF
    const existingPdfBytes = fs.readFileSync('input.pdf');
    const pdfDoc = await PDFDocument.load(existingPdfBytes);

    // Число страниц
    const pageCount = pdfDoc.getPageCount();
    console.log(`Document has ${pageCount} pages`);

    // Новая страница
    const newPage = pdfDoc.addPage([600, 400]);
    newPage.drawText('Added by pdf-lib', {
        x: 100,
        y: 300,
        size: 16
    });

    // Сохранение изменённого PDF
    const pdfBytes = await pdfDoc.save();
    fs.writeFileSync('modified.pdf', pdfBytes);
}
```

#### Создание сложных PDF с нуля

```javascript
import { PDFDocument, rgb, StandardFonts } from 'pdf-lib';
import fs from 'fs';

async function createPDF() {
    const pdfDoc = await PDFDocument.create();

    // Шрифты
    const helveticaFont = await pdfDoc.embedFont(StandardFonts.Helvetica);
    const helveticaBold = await pdfDoc.embedFont(StandardFonts.HelveticaBold);

    // Страница
    const page = pdfDoc.addPage([595, 842]); // размер A4
    const { width, height } = page.getSize();

    // Текст со стилем
    page.drawText('Invoice #12345', {
        x: 50,
        y: height - 50,
        size: 18,
        font: helveticaBold,
        color: rgb(0.2, 0.2, 0.8)
    });

    // Прямоугольник (фон заголовка)
    page.drawRectangle({
        x: 40,
        y: height - 100,
        width: width - 80,
        height: 30,
        color: rgb(0.9, 0.9, 0.9)
    });

    // Содержимое в виде таблицы
    const items = [
        ['Item', 'Qty', 'Price', 'Total'],
        ['Widget', '2', '$50', '$100'],
        ['Gadget', '1', '$75', '$75']
    ];

    let yPos = height - 150;
    items.forEach(row => {
        let xPos = 50;
        row.forEach(cell => {
            page.drawText(cell, {
                x: xPos,
                y: yPos,
                size: 12,
                font: helveticaFont
            });
            xPos += 120;
        });
        yPos -= 25;
    });

    const pdfBytes = await pdfDoc.save();
    fs.writeFileSync('created.pdf', pdfBytes);
}
```

#### Продвинутое объединение и разделение

```javascript
import { PDFDocument } from 'pdf-lib';
import fs from 'fs';

async function mergePDFs() {
    // Новый документ
    const mergedPdf = await PDFDocument.create();

    // Загрузка исходных PDF
    const pdf1Bytes = fs.readFileSync('doc1.pdf');
    const pdf2Bytes = fs.readFileSync('doc2.pdf');

    const pdf1 = await PDFDocument.load(pdf1Bytes);
    const pdf2 = await PDFDocument.load(pdf2Bytes);

    // Копирование страниц из первого PDF
    const pdf1Pages = await mergedPdf.copyPages(pdf1, pdf1.getPageIndices());
    pdf1Pages.forEach(page => mergedPdf.addPage(page));

    // Копирование отдельных страниц из второго PDF (страницы 0, 2, 4)
    const pdf2Pages = await mergedPdf.copyPages(pdf2, [0, 2, 4]);
    pdf2Pages.forEach(page => mergedPdf.addPage(page));

    const mergedPdfBytes = await mergedPdf.save();
    fs.writeFileSync('merged.pdf', mergedPdfBytes);
}
```

### pdfjs-dist (лицензия Apache)

PDF.js — библиотека Mozilla для рендеринга PDF в браузере.

#### Загрузка и рендеринг

```javascript
import * as pdfjsLib from 'pdfjs-dist';

// Настройка воркера (важно для производительности)
pdfjsLib.GlobalWorkerOptions.workerSrc = './pdf.worker.js';

async function renderPDF() {
    // Загрузка PDF
    const loadingTask = pdfjsLib.getDocument('document.pdf');
    const pdf = await loadingTask.promise;

    console.log(`Loaded PDF with ${pdf.numPages} pages`);

    // Первая страница
    const page = await pdf.getPage(1);
    const viewport = page.getViewport({ scale: 1.5 });

    // Рендеринг на canvas
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    canvas.height = viewport.height;
    canvas.width = viewport.width;

    const renderContext = {
        canvasContext: context,
        viewport: viewport
    };

    await page.render(renderContext).promise;
    document.body.appendChild(canvas);
}
```

#### Извлечение текста с координатами

```javascript
import * as pdfjsLib from 'pdfjs-dist';

async function extractText() {
    const loadingTask = pdfjsLib.getDocument('document.pdf');
    const pdf = await loadingTask.promise;

    let fullText = '';

    // Текст со всех страниц
    for (let i = 1; i <= pdf.numPages; i++) {
        const page = await pdf.getPage(i);
        const textContent = await page.getTextContent();

        const pageText = textContent.items
            .map(item => item.str)
            .join(' ');

        fullText += `\n--- Page ${i} ---\n${pageText}`;

        // Текст с координатами для продвинутой обработки
        const textWithCoords = textContent.items.map(item => ({
            text: item.str,
            x: item.transform[4],
            y: item.transform[5],
            width: item.width,
            height: item.height
        }));
    }

    console.log(fullText);
    return fullText;
}
```

#### Извлечение аннотаций и форм

```javascript
import * as pdfjsLib from 'pdfjs-dist';

async function extractAnnotations() {
    const loadingTask = pdfjsLib.getDocument('annotated.pdf');
    const pdf = await loadingTask.promise;

    for (let i = 1; i <= pdf.numPages; i++) {
        const page = await pdf.getPage(i);
        const annotations = await page.getAnnotations();

        annotations.forEach(annotation => {
            console.log(`Annotation type: ${annotation.subtype}`);
            console.log(`Content: ${annotation.contents}`);
            console.log(`Coordinates: ${JSON.stringify(annotation.rect)}`);
        });
    }
}
```

## Продвинутые операции в командной строке

### Возможности poppler-utils

#### Текст с координатами ограничивающих рамок

```bash
# Извлечение текста с координатами рамок (нужно для структурированных данных)
pdftotext -bbox-layout document.pdf output.xml

# XML-вывод содержит точные координаты каждого текстового элемента
```

#### Продвинутое преобразование изображений

```bash
# Преобразование в PNG с заданным разрешением
pdftoppm -png -r 300 document.pdf output_prefix

# Диапазон страниц в высоком разрешении
pdftoppm -png -r 600 -f 1 -l 3 document.pdf high_res_pages

# Преобразование в JPEG с настройкой качества
pdftoppm -jpeg -jpegopt quality=85 -r 200 document.pdf jpeg_output
```

#### Извлечение встроенных изображений

```bash
# Все встроенные изображения с метаданными
pdfimages -j -p document.pdf page_images

# Список изображений без извлечения
pdfimages -list document.pdf

# Извлечение в исходном формате
pdfimages -all document.pdf images/img
```

### Возможности qpdf

#### Сложные операции со страницами

```bash
# Разбиение PDF на группы страниц
qpdf --split-pages=3 input.pdf output_group_%02d.pdf

# Отдельные страницы со сложными диапазонами
qpdf input.pdf --pages input.pdf 1,3-5,8,10-end -- extracted.pdf

# Объединение выбранных страниц из нескольких PDF
qpdf --empty --pages doc1.pdf 1-3 doc2.pdf 5-7 doc3.pdf 2,4 -- combined.pdf
```

#### Оптимизация и восстановление

```bash
# Оптимизация для веба (линеаризация для потоковой отдачи)
qpdf --linearize input.pdf optimized.pdf

# Удаление неиспользуемых объектов и сжатие
qpdf --optimize-level=all input.pdf compressed.pdf

# Попытка восстановить повреждённую структуру
qpdf --check input.pdf
qpdf --fix-qdf damaged.pdf repaired.pdf

# Подробная структура PDF для отладки
qpdf --show-all-pages input.pdf > structure.txt
```

#### Продвинутое шифрование

```bash
# Защита паролем с заданными разрешениями
qpdf --encrypt user_pass owner_pass 256 --print=none --modify=none -- input.pdf encrypted.pdf

# Проверка состояния шифрования
qpdf --show-encryption encrypted.pdf

# Снятие защиты (нужен пароль)
qpdf --password=secret123 --decrypt encrypted.pdf decrypted.pdf
```

## Продвинутые приёмы Python

### Возможности pdfplumber

#### Текст с точными координатами

```python
import pdfplumber

with pdfplumber.open("document.pdf") as pdf:
    page = pdf.pages[0]

    # Все символы с координатами
    chars = page.chars
    for char in chars[:10]:  # первые 10 символов
        print(f"Char: '{char['text']}' at x:{char['x0']:.1f} y:{char['y0']:.1f}")

    # Текст внутри рамки (left, top, right, bottom)
    bbox_text = page.within_bbox((100, 100, 400, 200)).extract_text()
```

#### Извлечение таблиц с настройками

```python
import pdfplumber
import pandas as pd

with pdfplumber.open("complex_table.pdf") as pdf:
    page = pdf.pages[0]

    # Настройки для сложных макетов
    table_settings = {
        "vertical_strategy": "lines",
        "horizontal_strategy": "lines",
        "snap_tolerance": 3,
        "intersection_tolerance": 15
    }
    tables = page.extract_tables(table_settings)

    # Визуальная отладка извлечения таблиц
    img = page.to_image(resolution=150)
    img.save("debug_layout.png")
```

### Возможности reportlab

#### Отчёт с таблицей

```python
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# Данные
data = [
    ['Product', 'Q1', 'Q2', 'Q3', 'Q4'],
    ['Widgets', '120', '135', '142', '158'],
    ['Gadgets', '85', '92', '98', '105']
]

# PDF с таблицей
doc = SimpleDocTemplate("report.pdf")
elements = []

# Заголовок
styles = getSampleStyleSheet()
title = Paragraph("Quarterly Sales Report", styles['Title'])
elements.append(title)

# Таблица с оформлением
table = Table(data)
table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 14),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
    ('GRID', (0, 0), (-1, -1), 1, colors.black)
]))
elements.append(table)

doc.build(elements)
```

## Сложные сценарии

### Извлечение рисунков и изображений

#### Способ 1: pdfimages (самый быстрый)

```bash
# Все изображения в исходном качестве
pdfimages -all document.pdf images/img
```

#### Способ 2: pypdfium2 и обработка изображений

```python
import pypdfium2 as pdfium
from PIL import Image
import numpy as np

def extract_figures(pdf_path, output_dir):
    pdf = pdfium.PdfDocument(pdf_path)

    for page_num, page in enumerate(pdf):
        # Рендеринг страницы в высоком разрешении
        bitmap = page.render(scale=3.0)
        img = bitmap.to_pil()

        # Преобразование в numpy для обработки
        img_array = np.array(img)

        # Простое обнаружение рисунков (небелые области)
        mask = np.any(img_array != [255, 255, 255], axis=2)

        # Поиск контуров и извлечение рамок
        # (упрощённо: реальная реализация требует более сложного обнаружения)

        # Сохранение найденных рисунков
        # ... реализация зависит от конкретной задачи
```

### Пакетная обработка с обработкой ошибок

```python
import os
import glob
from pypdf import PdfReader, PdfWriter
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def batch_process_pdfs(input_dir, operation='merge'):
    pdf_files = glob.glob(os.path.join(input_dir, "*.pdf"))

    if operation == 'merge':
        writer = PdfWriter()
        for pdf_file in pdf_files:
            try:
                reader = PdfReader(pdf_file)
                for page in reader.pages:
                    writer.add_page(page)
                logger.info(f"Processed: {pdf_file}")
            except Exception as e:
                logger.error(f"Failed to process {pdf_file}: {e}")
                continue

        with open("batch_merged.pdf", "wb") as output:
            writer.write(output)

    elif operation == 'extract_text':
        for pdf_file in pdf_files:
            try:
                reader = PdfReader(pdf_file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text()

                output_file = pdf_file.replace('.pdf', '.txt')
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(text)
                logger.info(f"Extracted text from: {pdf_file}")

            except Exception as e:
                logger.error(f"Failed to extract text from {pdf_file}: {e}")
                continue
```

### Обрезка PDF

```python
from pypdf import PdfWriter, PdfReader

reader = PdfReader("input.pdf")
writer = PdfWriter()

# Обрезка страницы (left, bottom, right, top в пунктах)
page = reader.pages[0]
page.mediabox.left = 50
page.mediabox.bottom = 50
page.mediabox.right = 550
page.mediabox.top = 750

writer.add_page(page)
with open("cropped.pdf", "wb") as output:
    writer.write(output)
```

## Производительность

### 1. Большие PDF

- Используй потоковые подходы вместо загрузки всего PDF в память.
- Для разбиения больших файлов применяй `qpdf --split-pages`.
- Обрабатывай страницы по одной через `pypdfium2`.

### 2. Извлечение текста

- `pdftotext` быстрее всего для простого текста.
- `pdfplumber` — для структурированных данных и таблиц.
- Избегай `pypdf.extract_text()` на очень больших документах.

### 3. Извлечение изображений

- `pdfimages` намного быстрее рендеринга страниц.
- Низкое разрешение — для предпросмотра, высокое — для итогового результата.

### 4. Заполнение форм

- `pdf-lib` сохраняет структуру формы лучше большинства альтернатив.
- Проверяй поля формы до обработки.

### 5. Работа с памятью

```python
# Обработка PDF частями
def process_large_pdf(pdf_path, chunk_size=10):
    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)

    for start_idx in range(0, total_pages, chunk_size):
        end_idx = min(start_idx + chunk_size, total_pages)
        writer = PdfWriter()

        for i in range(start_idx, end_idx):
            writer.add_page(reader.pages[i])

        # Обработка части
        with open(f"chunk_{start_idx//chunk_size}.pdf", "wb") as output:
            writer.write(output)
```

## Диагностика частых проблем

### Зашифрованные PDF

```python
# PDF под паролем
from pypdf import PdfReader

try:
    reader = PdfReader("encrypted.pdf")
    if reader.is_encrypted:
        reader.decrypt("password")
except Exception as e:
    print(f"Failed to decrypt: {e}")
```

### Повреждённые PDF

```bash
# Восстановление через qpdf
qpdf --check corrupted.pdf
qpdf --replace-input corrupted.pdf
```

### Проблемы с извлечением текста

```python
# Запасной вариант — OCR для сканированных PDF
import pytesseract
from pdf2image import convert_from_path

def extract_text_with_ocr(pdf_path):
    images = convert_from_path(pdf_path)
    text = ""
    for i, image in enumerate(images):
        text += pytesseract.image_to_string(image)
    return text
```

## Лицензии библиотек

- **pypdf**: BSD
- **pdfplumber**: MIT
- **pypdfium2**: Apache/BSD
- **reportlab**: BSD
- **poppler-utils**: GPL-2
- **qpdf**: Apache
- **pdf-lib**: MIT
- **pdfjs-dist**: Apache
