#!/usr/bin/env python3
"""
Скрипт для генерации metadata.json из SKILL.md файлов.
Проходит по всем директориям skills/*, считывает frontmatter и создаёт metadata.json.
"""

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


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


def find_skill_files(skills_dir: Path) -> list[Path]:
    """
    Находит файлы SKILL.md в директории skills на первом уровне вложенности.

    Обрабатывает только skills/*/SKILL.md, игнорируя вложенные директории.

    Args:
        skills_dir: Путь к директории skills

    Returns:
        Список путей к файлам SKILL.md
    """
    skill_files = []

    # Итерируем только по директориям первого уровня
    for item in skills_dir.iterdir():
        if item.is_dir():
            skill_file = item / 'SKILL.md'
            if skill_file.exists():
                skill_files.append(skill_file)

    return sorted(skill_files)


def generate_urls(skill_path: Path, skills_dir: Path, repo_url: str) -> dict[str, str]:
    """
    Генерирует URL для файла навыка.

    Args:
        skill_path: Путь к файлу SKILL.md
        skills_dir: Путь к директории skills
        repo_url: URL репозитория

    Returns:
        Словарь с полями web и raw
    """
    # Относительный путь от корня репозитория
    rel_path = skill_path.relative_to(skills_dir.parent)

    # Формируем URL для GitHub
    web_url = f"{repo_url}/blob/main/{rel_path}"
    raw_url = f"https://raw.githubusercontent.com/{repo_url.split('github.com/')[-1]}/main/{rel_path}"

    return {
        "web": web_url,
        "raw": raw_url
    }


def extract_skill_metadata(skill_path: Path, skills_dir: Path, repo_url: str) -> dict[str, Any] | None:
    """
    Извлекает метаданные навыка из файла SKILL.md.

    Args:
        skill_path: Путь к файлу SKILL.md
        skills_dir: Путь к директории skills
        repo_url: URL репозитория

    Returns:
        Словарь с метаданными навыка или None, если данные некорректны
    """
    try:
        content = skill_path.read_text(encoding='utf-8')
    except (IOError, OSError):
        print(f"Ошибка чтения файла: {skill_path}")
        return None

    frontmatter = parse_frontmatter(content)

    if not frontmatter:
        print(f"Frontmatter не найден в файле: {skill_path}")
        return None

    # Проверяем обязательные поля
    if 'name' not in frontmatter or 'description' not in frontmatter:
        print(f"Отсутствуют обязательные поля в файле: {skill_path}")
        return None

    # Извлекаем версию из metadata или устанавливаем значение по умолчанию
    version = "1.0.0"
    if 'metadata' in frontmatter and isinstance(frontmatter['metadata'], dict):
        version = frontmatter['metadata'].get('version', version)

    urls = generate_urls(skill_path, skills_dir, repo_url)

    return {
        "name": frontmatter['name'],
        "description": frontmatter['description'],
        "version": version,
        "url": urls
    }


def generate_metadata(repo_root: Path, repo_url: str) -> dict[str, Any]:
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

    skill_files = find_skill_files(skills_dir)

    if not skill_files:
        print("Файлы SKILL.md не найдены")
        return {}

    skills = []

    for skill_file in skill_files:
        skill_metadata = extract_skill_metadata(skill_file, skills_dir, repo_url)
        if skill_metadata:
            skills.append(skill_metadata)
            print(f"> Обработан навык: {skill_metadata['name']}")

    return {
        "skills": skills,
        "count": len(skills),
        "lastUpdate": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    }


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

    # Записываем metadata.json
    output_path = repo_root / 'metadata.json'

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=4)
        f.write('\n')

    print(f"\nФайл metadata.json успешно создан: {output_path}")
    print(f"Обработано навыков: {metadata['count']}")

    return 0


if __name__ == '__main__':
    exit(main())
