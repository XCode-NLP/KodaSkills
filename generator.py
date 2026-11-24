#!/usr/bin/env python3
"""
Скрипт для генерации metadata.json из директорий навыков.
Проходит по всем директориям skills/*, считывает frontmatter из SKILL.md,
собирает все файлы навыка и создаёт metadata.json.
"""

import hashlib
import json
import os
import re
import subprocess
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, NamedTuple
from urllib.parse import quote

import yaml

SKILL_FILE_NAME = 'SKILL.md'
SKILL_NAME_PATTERN = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
SKILL_TAG_PATTERN = re.compile(r'^[a-z0-9а-яё]+(?:-[a-z0-9а-яё]+)*$')
MAX_SKILL_TAGS = 5
IGNORED_FILE_NAMES = {'.DS_Store', 'Thumbs.db'}
IGNORED_DIR_NAMES = {'.git', '__pycache__', '.venv', 'node_modules'}
TIMESTAMP_FORMAT = '%Y-%m-%dT%H:%M:%SZ'


def parse_frontmatter(content: str) -> dict[str, Any] | None:
    """
    Парсит YAML frontmatter из содержимого файла.

    Frontmatter должен быть обёрнут в разделители ---.

    Args:
        content: Содержимое файла

    Returns:
        Словарь с данными frontmatter или None, если frontmatter не найден
    """
    pattern = r'^---\s*\n(.*?)\n---\s*\n'
    match = re.match(pattern, content, re.DOTALL)

    if not match:
        return None

    try:
        frontmatter = yaml.safe_load(match.group(1))
        return frontmatter if isinstance(frontmatter, dict) else None
    except yaml.YAMLError:
        return None


def find_skill_dirs(skills_dir: Path) -> list[Path]:
    """
    Находит директории навыков в директории skills на первом уровне вложенности.

    Навыком считается только директория, содержащая SKILL.md. Директории без
    этого файла пропускаются и не попадают в метаданные. Вложенные директории
    навыков не обрабатываются.

    Args:
        skills_dir: Путь к директории skills

    Returns:
        Список путей к директориям навыков
    """
    skill_dirs = []

    # Итерируем только по директориям первого уровня
    for item in sorted(skills_dir.iterdir()):
        if not item.is_dir():
            continue

        if not (item / SKILL_FILE_NAME).is_file():
            print(f"Пропущена директория без {SKILL_FILE_NAME}: {item}")
            continue

        skill_dirs.append(item)

    return skill_dirs


def find_skill_files(skill_dir: Path) -> list[Path]:
    """
    Находит все файлы директории навыка, включая SKILL.md и дополнительные файлы.

    Пропускает служебные файлы и директории, которые не относятся к навыку.
    SKILL.md всегда идёт первым, остальные файлы сортируются по относительному пути.

    Args:
        skill_dir: Путь к директории навыка

    Returns:
        Список путей к файлам навыка
    """
    files = []

    for path in skill_dir.rglob('*'):
        if not path.is_file():
            continue

        relative_parts = path.relative_to(skill_dir).parts
        if any(part in IGNORED_DIR_NAMES for part in relative_parts[:-1]):
            continue
        if path.name in IGNORED_FILE_NAMES or path.suffix == '.pyc':
            continue

        files.append(path)

    files.sort(
        key=lambda path: (
            path.relative_to(skill_dir).as_posix() != SKILL_FILE_NAME,
            path.relative_to(skill_dir).as_posix(),
        )
    )

    return files


def generate_raw_url(
    relative_path: str,
    repo_url: str,
    ref: str = 'main',
) -> str:
    """
    Генерирует ссылку на сырое содержимое файла навыка.

    Args:
        relative_path: Путь к файлу относительно корня репозитория
        repo_url: URL репозитория
        ref: Ветка или хэш коммита, к которому привязывается ссылка

    Returns:
        Прямая ссылка на сырое содержимое файла
    """
    repo_url = repo_url.rstrip('/')
    if repo_url.endswith('.git'):
        repo_url = repo_url[:-4]

    encoded_path = quote(relative_path, safe='/')
    repo_slug = repo_url.split('github.com/', 1)[-1].strip('/')

    return f"https://raw.githubusercontent.com/{repo_slug}/{ref}/{encoded_path}"


def to_utc_timestamp(value: str) -> str:
    """
    Приводит дату в формате ISO 8601 к виду RFC 3339 в часовом поясе UTC.

    Args:
        value: Дата в формате ISO 8601, например 2026-07-21T09:27:18+03:00

    Returns:
        Дата в формате ГГГГ-ММ-ДДTЧЧ:ММ:ССZ
    """
    try:
        moment = datetime.fromisoformat(value)
    except ValueError:
        return value

    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)

    return moment.astimezone(timezone.utc).strftime(TIMESTAMP_FORMAT)


def sha256_hex(data: bytes) -> str:
    """
    Считает хэш SHA-256 переданного содержимого.

    Args:
        data: Содержимое файла

    Returns:
        Хэш в шестнадцатеричном виде в нижнем регистре
    """
    return hashlib.sha256(data).hexdigest()


def read_git_blobs(repo_root: Path, specs: dict[str, str]) -> dict[str, bytes]:
    """
    Читает содержимое файлов из Git по спецификациям «коммит:путь».

    Хэш и размер считаются по версии из коммита, а не по рабочей копии, чтобы
    они совпадали с содержимым, которое отдают ссылки на этот коммит.

    Args:
        repo_root: Путь к корню репозитория
        specs: Словарь «ключ» → «коммит:путь»

    Returns:
        Словарь «ключ» → содержимое файла. Для отсутствующих объектов ключа нет
    """
    if not specs:
        return {}

    keys = list(specs)
    payload = ''.join(f"{specs[key]}\n" for key in keys).encode('utf-8')

    try:
        completed = subprocess.run(
            ['git', '-C', str(repo_root), 'cat-file', '--batch'],
            input=payload,
            capture_output=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        print("Предупреждение: не удалось прочитать файлы из Git, используется рабочая копия")
        return {}

    data = completed.stdout
    position = 0
    blobs: dict[str, bytes] = {}

    for key in keys:
        newline = data.find(b'\n', position)
        if newline == -1:
            break

        header = data[position:newline].decode('utf-8', 'replace')
        position = newline + 1
        parts = header.split(' ')

        # Для отсутствующего объекта Git отвечает «<спецификация> missing»
        if len(parts) != 3 or parts[1] != 'blob':
            continue

        size = int(parts[2])
        blobs[key] = data[position:position + size]
        position += size + 1

    return blobs


class FileRevision(NamedTuple):
    """Коммит, изменивший файл."""

    commit: str
    date: str


class RepoHistory(NamedTuple):
    """История файлов репозитория по данным Git."""

    last: dict[str, FileRevision]
    """Последний коммит, изменивший файл."""

    first: dict[str, FileRevision]
    """Первый коммит, добавивший файл."""


def get_file_history(repo_root: Path) -> RepoHistory:
    """
    Собирает историю коммитов для файлов репозитория.

    Позволяет получить стабильные метки времени и хэши коммитов независимо от
    времени клонирования. Для мелких клонов без истории данные будут неполными.

    Args:
        repo_root: Путь к корню репозитория

    Returns:
        История файлов: последний и первый коммиты для каждого пути
        относительно корня репозитория
    """
    empty = RepoHistory(last={}, first={})

    try:
        completed = subprocess.run(
            [
                'git',
                '-c', 'core.quotePath=false',
                '-C', str(repo_root),
                'log',
                '--format=%x00%H %cI',
                '--name-only',
            ],
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        print("Предупреждение: не удалось получить историю Git, используется время изменения файлов")
        return empty

    last: dict[str, FileRevision] = {}
    first: dict[str, FileRevision] = {}
    current: FileRevision | None = None

    # Журнал отдаётся от свежих коммитов к старым, поэтому первая встреченная
    # запись пути — самая свежая, а последняя — самая старая
    for line in completed.stdout.splitlines():
        if line.startswith('\x00'):
            commit, _, date = line[1:].strip().partition(' ')
            current = FileRevision(commit=commit, date=to_utc_timestamp(date))
        elif current and line.strip():
            path = line.strip()
            last.setdefault(path, current)
            first[path] = current

    return RepoHistory(last=last, first=first)


def file_timestamps(
    file_path: Path,
    repo_root: Path,
    history: RepoHistory,
) -> tuple[str, str]:
    """
    Определяет метки времени добавления и последнего изменения файла.

    Приоритет у дат коммитов Git. Если истории нет, используется время
    изменения файла в файловой системе.

    Args:
        file_path: Путь к файлу
        repo_root: Путь к корню репозитория
        history: История файлов репозитория

    Returns:
        Кортеж «добавлен», «обновлён» в формате ГГГГ-ММ-ДДTЧЧ:ММ:ССZ
    """
    relative_path = file_path.relative_to(repo_root).as_posix()
    first = history.first.get(relative_path)
    last = history.last.get(relative_path)

    if first and last:
        return first.date, last.date

    modified = datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc)
    fallback = modified.strftime(TIMESTAMP_FORMAT)

    return fallback, fallback


def skill_timestamps(file_timestamps_map: dict[Path, tuple[str, str]]) -> tuple[str, str]:
    """
    Определяет метки времени добавления и последнего обновления навыка.

    Навык добавлен вместе со своим самым старым файлом и обновлён вместе с
    самым свежим из них.

    Args:
        file_timestamps_map: Метки времени файлов навыка

    Returns:
        Кортеж «добавлен», «обновлён» в формате ГГГГ-ММ-ДДTЧЧ:ММ:ССZ
    """
    # Метки времени в формате RFC 3339 в UTC сравниваются лексикографически
    return (
        min(added for added, _ in file_timestamps_map.values()),
        max(updated for _, updated in file_timestamps_map.values()),
    )


def has_uncommitted_changes(repo_root: Path) -> bool:
    """
    Проверяет, есть ли в репозитории незакоммиченные изменения.

    Метаданные описывают закоммиченное состояние: sha256, size, revision и ссылки
    берутся из Git. Поэтому незакоммиченные правки в метаданные не попадают, и об
    этом стоит предупредить.

    Args:
        repo_root: Путь к корню репозитория

    Returns:
        True, если рабочее дерево содержит изменения
    """
    try:
        completed = subprocess.run(
            ['git', '-C', str(repo_root), 'status', '--porcelain'],
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return False

    return bool(completed.stdout.strip())


def metadata_value_to_string(value: Any) -> str | None:
    """
    Приводит значение из frontmatter к строке для карты metadata.

    По спецификации Agent Skills карта metadata содержит только строковые
    значения. Вложенные структуры и пустые значения отбрасываются.

    Args:
        value: Значение из frontmatter

    Returns:
        Строковое представление или None, если значение не подходит
    """
    if value is None or isinstance(value, (dict, list, set, tuple)):
        return None

    if isinstance(value, bool):
        return 'true' if value else 'false'

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    return str(value)


def build_skill_metadata_map(frontmatter: dict[str, Any], skill_path: Path) -> dict[str, str]:
    """
    Собирает карту дополнительных свойств навыка из поля metadata.

    Args:
        frontmatter: Разобранный frontmatter
        skill_path: Путь к SKILL.md для сообщений об ошибках

    Returns:
        Словарь со строковыми значениями. Пустой, если поле не задано
    """
    raw_metadata = frontmatter.get('metadata')

    if raw_metadata is None:
        return {}

    if not isinstance(raw_metadata, dict):
        print(f"Поле metadata должно быть отображением ключ-значение: {skill_path}")
        return {}

    metadata_map = {}

    for key, value in raw_metadata.items():
        # Теги переносятся в отдельное поле навыка, а не в карту строковых свойств
        if key == 'tags':
            continue

        string_value = metadata_value_to_string(value)

        if string_value is None:
            print(f"Значение metadata.{key} пропущено: поддерживаются только строки: {skill_path}")
            continue

        metadata_map[str(key)] = string_value

    return metadata_map


def read_skill_tags(
    frontmatter: dict[str, Any],
    skill_path: Path,
    report_missing: bool = True,
) -> list[str] | None:
    """
    Читает теги навыка из поля metadata.tags.

    Теги описывают тему, язык, бренд или стек навыка и нужны для фильтрации
    каталога маркетплейса. Допускается от 1 до 5 тегов: каждое значение —
    слово на латинице или кириллице, состоящее из букв, цифр и дефисов.
    Приведение к нижнему регистру делает фильтрацию регистронезависимой.

    Отсутствие тегов не выводится отдельной строкой на каждый навык: такие
    случаи собирает `report_missing_tags`, чтобы не заваливать вывод.

    Args:
        frontmatter: Разобранный frontmatter
        skill_path: Путь к SKILL.md для сообщений об ошибках
        report_missing: Выводить ли сообщение об отсутствии поля tags

    Returns:
        Список тегов или None, если теги не заданы или заданы некорректно
    """
    raw_metadata = frontmatter.get('metadata')

    if not isinstance(raw_metadata, dict):
        if report_missing:
            print(f"Не заданы теги навыка: укажите metadata.tags: {skill_path}")
        return None

    raw_tags = raw_metadata.get('tags')

    if raw_tags is None:
        if report_missing:
            print(f"Не заданы теги навыка: укажите metadata.tags: {skill_path}")
        return None

    if not isinstance(raw_tags, list):
        print(f"Поле metadata.tags должно быть массивом строк: {skill_path}")
        return None

    tags = []

    for value in raw_tags:
        if not isinstance(value, str):
            print(f"Тег пропущен: ожидается строка: {skill_path}")
            continue

        tag = value.strip().lower()

        if not SKILL_TAG_PATTERN.fullmatch(tag):
            print(
                "Тег пропущен: допустимы буквы, цифры и дефис, "
                f"например api или база-данных: {skill_path}: {value}"
            )
            continue

        if tag in tags:
            print(f"Повторяющийся тег пропущен: {skill_path}: {tag}")
            continue

        tags.append(tag)

    if not tags:
        if report_missing:
            print(f"Не заданы теги навыка: укажите metadata.tags: {skill_path}")
        return None

    if len(tags) > MAX_SKILL_TAGS:
        print(
            f"Допускается не более {MAX_SKILL_TAGS} тегов, "
            f"лишние пропущены: {skill_path}"
        )
        tags = tags[:MAX_SKILL_TAGS]

    return tags


def read_optional_string(
    frontmatter: dict[str, Any],
    field: str,
    skill_path: Path,
) -> str | None:
    """
    Читает необязательное строковое поле frontmatter.

    Некорректное значение не отбрасывает навык целиком, а пропускается
    с предупреждением.

    Args:
        frontmatter: Разобранный frontmatter
        field: Имя поля
        skill_path: Путь к SKILL.md для сообщений об ошибках

    Returns:
        Значение поля или None, если поле отсутствует или некорректно
    """
    value = frontmatter.get(field)

    if value is None:
        return None

    if not isinstance(value, str):
        print(f"Поле {field} должно быть строкой: {skill_path}")
        return None

    value = value.strip()

    if not value:
        print(f"Поле {field} пустое и пропущено: {skill_path}")
        return None

    return value


def extract_skill_metadata(
    skill_dir: Path,
    repo_root: Path,
    repo_url: str,
    history: RepoHistory,
) -> dict[str, Any] | None:
    """
    Извлекает метаданные навыка из директории навыка.

    Frontmatter читается из рабочей копии `SKILL.md`: теги, имя и описание
    должны попадать в `metadata.json` сразу после правки файла, без коммита.
    Хэши, размеры и ревизии при этом считаются по версии из Git, чтобы
    `sha256` и `url.raw` описывали одну и ту же версию файла.

    Args:
        skill_dir: Путь к директории навыка
        repo_root: Путь к корню репозитория
        repo_url: URL репозитория
        history: История файлов репозитория

    Returns:
        Словарь с метаданными навыка или None, если данные некорректны
    """
    skill_path = skill_dir / SKILL_FILE_NAME

    if not skill_path.is_file():
        print(f"Файл {SKILL_FILE_NAME} не найден, директория не считается навыком: {skill_dir}")
        return None

    skills_dir = repo_root / 'skills'
    skill_files = find_skill_files(skill_dir)

    # Хэши и ссылки берём из коммита, чтобы они совпадали с тем, что отдаёт
    # url.raw, привязанная к revision
    blob_specs = {}
    for file_path in skill_files:
        relative_to_repo = file_path.relative_to(repo_root).as_posix()
        revision = history.last.get(relative_to_repo)
        if revision is not None:
            blob_specs[relative_to_repo] = f"{revision.commit}:{relative_to_repo}"

    blobs = read_git_blobs(repo_root, blob_specs)

    try:
        skill_text = skill_path.read_text(encoding='utf-8', errors='replace')
    except (IOError, OSError):
        print(f"Ошибка чтения файла: {skill_path}")
        return None

    frontmatter = parse_frontmatter(skill_text)

    if not frontmatter:
        print(f"Frontmatter не найден в файле: {skill_path}")
        return None

    name = frontmatter.get('name')
    description = frontmatter.get('description')

    if not isinstance(name, str) or not SKILL_NAME_PATTERN.fullmatch(name):
        print(f"Некорректное имя навыка в файле: {skill_path}")
        return None

    if name != skill_dir.name:
        print(f"Имя навыка не совпадает с именем директории: {skill_path}")
        return None

    if not isinstance(description, str) or not 1 <= len(description) <= 1024:
        print(f"Некорректное описание навыка в файле: {skill_path}")
        return None

    # Необязательные поля frontmatter из спецификации Agent Skills
    license_name = read_optional_string(frontmatter, 'license', skill_path)
    metadata_map = build_skill_metadata_map(frontmatter, skill_path)
    # Об отсутствии тегов сообщает сводка в конце: строка на каждый навык
    # утопила бы остальные предупреждения
    tags = read_skill_tags(frontmatter, skill_path, report_missing=False)

    files = []
    timestamps_by_file: dict[Path, tuple[str, str]] = {}

    for file_path in skill_files:
        relative_to_repo = file_path.relative_to(repo_root).as_posix()
        # Путь относительно skills/ без имени файла: <имя_навыка> или <имя_навыка>/scripts
        relative_dir = file_path.parent.relative_to(skills_dir).as_posix()
        revision = history.last.get(relative_to_repo)

        if revision is None:
            print(f"Предупреждение: файл не найден в истории Git: {relative_to_repo}")

        content = blobs.get(relative_to_repo)
        if content is None:
            content = file_path.read_bytes()

        file_entry = {
            "name": file_path.name,
            "path": relative_dir,
            # Ссылка привязывается к коммиту файла, поэтому всегда отдаёт ту версию,
            # для которой посчитан sha256
            "url": {
                "raw": generate_raw_url(
                    relative_to_repo,
                    repo_url,
                    revision.commit if revision else 'main',
                ),
            },
        }

        if revision is not None:
            file_entry["revision"] = revision.commit

        added, updated = file_timestamps(file_path, repo_root, history)
        timestamps_by_file[file_path] = (added, updated)

        file_entry.update({
            "sha256": sha256_hex(content),
            "size": len(content),
            "updatedAt": updated,
        })

        files.append(file_entry)

    added_at, updated_at = skill_timestamps(timestamps_by_file)

    skill_entry = {
        "name": name,
        "description": description,
    }

    if tags:
        skill_entry["tags"] = tags

    if license_name is not None:
        skill_entry["license"] = license_name

    if metadata_map:
        skill_entry["metadata"] = metadata_map

    skill_entry["addedAt"] = added_at
    skill_entry["updatedAt"] = updated_at
    skill_entry["files"] = files

    return skill_entry


def validate_metadata(metadata: dict[str, Any], schema_path: Path) -> None:
    """
    Проверяет метаданные по JSON Schema.

    Args:
        metadata: Сгенерированные метаданные
        schema_path: Путь к файлу metadata-schema.json

    Raises:
        ValueError: Если метаданные не соответствуют схеме
    """
    try:
        import jsonschema
    except ImportError:
        print("Предупреждение: модуль jsonschema не установлен, проверка по схеме пропущена")
        return

    schema = json.loads(schema_path.read_text(encoding='utf-8'))
    validator = jsonschema.Draft202012Validator(
        schema,
        format_checker=jsonschema.FormatChecker(),
    )
    errors = sorted(validator.iter_errors(metadata), key=lambda error: list(error.path))

    if errors:
        messages = "\n".join(f"- {error.message}" for error in errors)
        raise ValueError(f"metadata.json не соответствует схеме:\n{messages}")


def generate_metadata(
    repo_root: Path,
    repo_url: str,
) -> dict[str, Any]:
    """
    Генерирует структуру metadata.json.

    Args:
        repo_root: Путь к корню репозитория
        repo_url: URL репозитория

    Returns:
        Словарь с метаданными
    """
    skills_dir = repo_root / 'skills'

    if not skills_dir.exists():
        print(f"Директория skills не найдена: {skills_dir}")
        return {}

    skill_dirs = find_skill_dirs(skills_dir)

    if not skill_dirs:
        print("Директории навыков не найдены")
        return {}

    skills = []
    history = get_file_history(repo_root)

    if has_uncommitted_changes(repo_root):
        print(
            "Предупреждение: в рабочем дереве есть незакоммиченные изменения. "
            "Frontmatter берётся из рабочей копии, а хэши, размеры и ревизии — "
            "из последнего коммита, поэтому они совпадут с содержимым файлов "
            "только после коммита."
        )

    for skill_dir in skill_dirs:
        skill_metadata = extract_skill_metadata(
            skill_dir,
            repo_root,
            repo_url,
            history,
        )
        if skill_metadata:
            skills.append(skill_metadata)
            print(f"> Обработан навык: {skill_metadata['name']}")

    return {
        "skills": skills,
        "updatedAt": datetime.now(timezone.utc).strftime(TIMESTAMP_FORMAT),
    }


def report_missing_tags(metadata: dict[str, Any]) -> bool:
    """
    Проверяет, что у каждого навыка заданы теги.

    Теги обязательны: по ним клиенты фильтруют каталог маркетплейса. Ошибка
    выводится одной сводкой, чтобы не тонуть в сообщениях схемы.

    Args:
        metadata: Сгенерированные метаданные

    Returns:
        True, если теги заданы у всех навыков
    """
    missing = [skill['name'] for skill in metadata['skills'] if not skill.get('tags')]

    if not missing:
        return True

    preview = ', '.join(missing[:10])
    if len(missing) > 10:
        preview += f" и ещё {len(missing) - 10}"

    print(f"Ошибка: не заданы metadata.tags у навыков ({len(missing)}): {preview}")
    print("Добавьте metadata.tags в frontmatter SKILL.md: от 1 до 5 тегов.")

    return False


def main():
    """Основная функция скрипта."""
    # Определяем корень репозитория
    script_dir = Path(__file__).parent.resolve()
    repo_root = script_dir

    # URL репозитория (можно переопределить через переменную окружения)
    repo_url = os.environ.get('REPO_URL', 'https://github.com/XCode-NLP/KodaSkills')

    print(f"Корень репозитория: {repo_root}")
    print(f"URL репозитория: {repo_url}\n")
    print("Генерация metadata.json...")

    metadata = generate_metadata(repo_root, repo_url)

    if not metadata:
        print("Ошибка: не удалось сгенерировать метаданные")
        return 1

    if not report_missing_tags(metadata):
        return 1

    schema_path = repo_root / 'metadata-schema.json'
    if schema_path.exists():
        try:
            validate_metadata(metadata, schema_path)
        except ValueError as error:
            print(f"Ошибка: {error}")
            return 1
    else:
        print(f"Предупреждение: схема не найдена: {schema_path}")

    # Записываем metadata.json
    output_path = repo_root / 'metadata.json'

    # Минифицированный вывод: без отступов и лишних пробелов, чтобы экономить место
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, separators=(',', ':'))
        f.write('\n')

    print(f"\nФайл metadata.json успешно создан: {output_path}")
    print(f"Обработано навыков: {len(metadata['skills'])}")

    return 0


if __name__ == '__main__':
    exit(main())
