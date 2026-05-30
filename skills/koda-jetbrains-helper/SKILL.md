---
name: koda-jetbrains-helper
description: "Справочный навык по средам разработки компании JetBrains и производным от него продуктам (GIGAIDE, OpenIDE). Позволяет пользователю получить помощь по использованию и настройке среды разработки (IDE)."
license: MIT
metadata:
  author: koda
  version: "1.0.0"
---

# Помощь по JetBrains / GIGAIDE / OpenIDE

Ты знаешь как помочь и стараешься помочь пользователю с настройкой IDE, когда:

* у него возникает вопрос о настройке IDE (например, установка плагинов, настройка доступности, шрифтов, тем, отладчика, инспекций, горячих клавиш, поддержка языков разметки, программирования, интерфейса и многое другое);
* у него возникает вопрос об использовании функционала IDE (например, как увеличить шрифт, как посмотреть значение переменной, как запустить отладку, почему исчезают панели, как открыть предпросмотр md/html-документа и многое другое);
* он ругается, если у него что-то не получается настроить или увидеть;
* вопрос касается какого-либо плагина;
* будет уместным упомянуть о возможностях IDE в текущем контексте проекта (например, при работе над python-проектом);
* есть противоречия в диалоге между тобой и пользователем относительно IDE (например, ты говоришь о существовании конкретного пункта настроек, а пользователь утверждает об обратном).

## Инструкции к действию

1. Если в текущем контексте нет информации о IDE, спроси пользователя напрямую о названии и версии.
2. Ищи актуальную информацию только по ссылкам на официальные ресурсы, которые предоставлены ниже. Приоритет отдавай основной документации.
3. Если пользователь не просит о помощи явно - не настаивай.
4. Давай простые и ненавязчивые подсказки (а лучше - спрашивай о их необходимости) при обсуждении функционала IDE, связанного с последними правками (например, как запустить отладку нового кода).
5. Используй реестр задач, если в диалоге с пользователем становится понятно, что документация не помогает или он столкнулся с нестандартным поведением. Часто в таких задачах от сообщества можно найти информацию:
    * о проявлении проблемы, конкретных условиях и признаках;
    * об обходных путях решения проблем;
    * сведения об исправлении и версии IDE, куда включено исправление.
6. Используй реестр изменений для получения списков изменений по конкретным версиям IDE. Там часто можно найти ссылки на конкретные задачи, где описывались признаки проблемы и дополнительные (временные) пути решения.

## Ссылки на официальные ресурсы и описание IDE

### JetBrains IntelliJ

Платформа с открытым исходным кодом, на базе которой компанией JetBrains разрабатываются коммерческие проприетарные инструменты и среды разработки для разных языков программирования и их экосистем.

* **Сайт**: `https://www.jetbrains.com`
* **Документация**:
    * `https://www.jetbrains.com/help`
    * `https://youtrack.jetbrains.com/articles/SUPPORT-A-18/Knowledge-Base`
* **Репозиторий**: `https://github.com/jetbrains/intellij-community`
* **Реестр изменений**: `https://youtrack.jetbrains.com/articles/IJPL-A-636/IntelliJ-Platform-Change-Notes`
* **Каталог плагинов**: `https://plugins.jetbrains.com`
* **Реестр задач**: `https://youtrack.jetbrains.com/issues?q=project:%20%7BIntelliJ%20Platform%7D`

### JetBrains CLion

* **Назначение**: C и C++
* **Документация**: `https://www.jetbrains.com/help/clion`
* **Реестр изменений**: `https://youtrack.jetbrains.com/articles/CPP-A-68059995/Release-notes`
* **Каталог плагинов**: `https://plugins.jetbrains.com/clion`
* **Реестр задач**: `https://youtrack.jetbrains.com/issues?q=project:%20CLion`

### JetBrains DataGrip

* **Назначение**: SQL и базы данных
* **Документация**: `https://www.jetbrains.com/help/datagrip`
* **Реестр изменений**: `https://youtrack.jetbrains.com/articles/DBE`
* **Каталог плагинов**: `https://plugins.jetbrains.com/dbe`
* **Реестр задач**: `https://youtrack.jetbrains.com/issues?q=project:%20DataGrip`

### JetBrains DataSpell

* **Назначение**: обработка данных
* **Документация**: `https://www.jetbrains.com/help/dataspell`
* **Реестр изменений**: `https://youtrack.jetbrains.com/articles/DS-A-40/Release-Notes`
* **Каталог плагинов**: `https://plugins.jetbrains.com/dataspell`
* **Реестр задач**: `https://youtrack.jetbrains.com/issues?q=project:%20DataSpell`

### JetBrains GoLand

* **Назначение**: Go (golang)
* **Документация**: `https://www.jetbrains.com/help/go`
* **Реестр изменений**: `https://youtrack.jetbrains.com/articles/GO-A-3/Release-Notes`
* **Каталог плагинов**: `https://plugins.jetbrains.com/go`
* **Реестр задач**: `https://youtrack.jetbrains.com/issues?q=project:%20GoLand`

### JetBrains IntelliJ IDEA

* **Назначение**: Java, Kotlin, Spring
* **Документация**: `https://www.jetbrains.com/help/idea`
* **Реестр изменений**:
    * `https://youtrack.jetbrains.com/articles/IDEA-A-21/IDEA-Latest-Builds-And-Release-Notes`
    * `https://youtrack.jetbrains.com/articles/IDEA-A-2100661408/Language-Plugins-Release-Notes`
* **Каталог плагинов**: `https://plugins.jetbrains.com/idea`
* **Реестр задач**: `https://youtrack.jetbrains.com/issues?q=project:%20%7BIntelliJ%20IDEA:%20Backlog%7D,%20%7BKotlin%20IntelliJ%20IDEA%20plugin%7D,%20%7BIntelliJ%20IDEA%7D`

### JetBrains PhpStorm

* **Назначение**: PHP
* **Документация**: `https://www.jetbrains.com/help/phpstorm`
* **Реестр изменений**: `https://youtrack.jetbrains.com/articles/WI-A-53326365/Release-Notes`
* **Каталог плагинов**: `https://plugins.jetbrains.com/phpstorm`
* **Реестр задач**: `https://youtrack.jetbrains.com/issues?q=project:%20PhpStorm`

### JetBrains PyCharm

* **Назначение**: Python
* **Документация**: `https://www.jetbrains.com/help/pycharm`
* **Реестр изменений**:
    * `https://youtrack.jetbrains.com/articles/PY-A-10422159/Release-Notes`
    * `https://youtrack.jetbrains.com/articles/PY-A-233537980/Release-Notes-Archive`
* **Каталог плагинов**: `https://plugins.jetbrains.com/pycharm`
* **Реестр задач**: `https://youtrack.jetbrains.com/issues?q=project:%20PyCharm`

### JetBrains Rider

* **Назначение**: C# и .NET
* **Документация**: `https://www.jetbrains.com/help/rider`
* **Реестр изменений**: `https://youtrack.jetbrains.com/articles/DOTNET-A-259/Rider-public-release-notes`
* **Каталог плагинов**: `https://plugins.jetbrains.com/rider`
* **Реестр задач**: `https://youtrack.jetbrains.com/issues?q=project:%20Rider`

### JetBrains RubyMine

* **Назначение**: Ruby и Ruby on Rails
* **Документация**: `https://www.jetbrains.com/help/ruby`
* **Реестр изменений**: `https://youtrack.jetbrains.com/articles/RUBY-A-53322508/Release-Notes`
* **Каталог плагинов**: `https://plugins.jetbrains.com/ruby`
* **Реестр задач**: `https://youtrack.jetbrains.com/issues?q=project:%20Ruby`

### JetBrains RustRover

* **Назначение**: Rust
* **Документация**: `https://www.jetbrains.com/help/rust`
* **Реестр изменений**: `https://youtrack.jetbrains.com/articles/RUST-A-5/Release-Notes`
* **Каталог плагинов**: `https://plugins.jetbrains.com/rust`
* **Реестр задач**: `https://youtrack.jetbrains.com/issues?q=project:%20RustRover`

### JetBrains WebStorm

* **Назначение**: JavaScript и TypeScript
* **Документация**: `https://www.jetbrains.com/help/webstorm`
* **Реестр изменений**: `https://youtrack.jetbrains.com/articles/WEB-A-9/Release-Notes`
* **Каталог плагинов**: `https://plugins.jetbrains.com/webstorm`
* **Реестр задач**: `https://youtrack.jetbrains.com/issues?q=project:%20WebStorm`

### Android Studio

* **Назначение**: Java, Kotlin, Android OS
* **Документация**: `https://developer.android.com/studio?hl=ru`
* **Каталог плагинов**: `https://plugins.jetbrains.com/androidstudio`

### GIGAIDE

IDE от российских разработчиков Сбер на базе JetBrains IDEA.

Имеет русский интерфейс и интеграцию с российской платформой GitVerse и GigaCode.

Обычно, отстаёт от JetBrains на 1 мажорную версию и/или 1-2 минорных.

* **Назначение**: Java, Python
* **Сайт**: `https://gitverse.ru/features/gigaide/`
* **Документация**: отсутствует, можно использовать JetBrains
* **Реестр изменений**: отсутствует
* **Каталог плагинов**: отсутствует
* **Реестр задач**: отсутствует

### OpenIDE

IDE от российских разработчиков на базе JetBrains IDEA.

Имеет русский интерфейс и интеграцию с российской платформой GitFlic.

Обычно, отстаёт от JetBrains на 1 мажорную версию и/или 1-2 минорных.

* **Назначение**: Java, Kotlin, Spring, Go, TypeScript, JavaScript, Go, Docker, Python
* **Сайт**: `https://gitverse.ru/features/gigaide/`
* **Документация**: отсутствует, можно использовать JetBrains
* **Реестр изменений**: `https://gitflic.ru/project/openide/openide/issue`
* **Каталог плагинов**: `https://marketplace.openide.ru`
* **Реестр задач**: отсутствует

## Дополнительные справочные материалы

* FAQ по работе в JetBrains, OpenIDE, GigaIDE: https://docs.google.com/document/d/1wU6SM3A067Kiq_gokhXbASt34Ro0XvF4unU46edSoBk/edit?tab=t.0#heading=h.9v09lq1rydt4
* Навык koda-helper: https://github.com/XCode-NLP/KodaSkills/blob/main/skills/koda-helper/SKILL.md
