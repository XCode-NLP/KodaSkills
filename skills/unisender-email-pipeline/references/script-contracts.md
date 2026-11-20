# Контракты локальных скриптов

Все пути входа/выхода передавать явно; скрипты не выполняют сеть или запись в
UniSender. Команды ниже: <ROOT> — установленная папка текущего навыка,
<WORK> — отдельная рабочая папка проекта. Python 3.9+ без сторонних зависимостей.

- `python3 <ROOT>/scripts/calculate_email_audit.py <WORK>/input.json --output <WORK>/audit.json`
  Контракт кампаний описан в audit-and-attribution.md. Из state сначала выбрать
  последний as_of каждого campaign_id+window; скрипт блокирует дубли окна.
- `python3 <ROOT>/scripts/manage_pipeline_state.py validate <WORK>/state.json`
- `python3 <ROOT>/scripts/manage_pipeline_state.py plan <WORK>/state.json --as-of <ISO> --output <WORK>/plan.json`
- `python3 <ROOT>/scripts/manage_pipeline_state.py merge <WORK>/state.json <WORK>/delta.json --output <WORK>/next.json`
  Поля/ключи описаны в state-and-incremental-runs.md. Не писать next поверх базы;
  проверить next перед атомарной заменой средствами хранилища.
- `python3 <ROOT>/scripts/build_tracking_urls.py <WORK>/placements.json --campaign digest_2026_10_07_sample --output <WORK>/urls.json`
  placements: [{id, url, track: true/false}]. Системные ссылки track=false.
  Сохраняются destination/неуправляемые параметры, PII запрещены.
- `python3 <ROOT>/scripts/rank_digest_topics.py <WORK>/topics.json --output <WORK>/ranking.json`
  candidates 5–10: id/title/editorial_axis/material_urls (0–5), wordstat_status,
  scores {demand,momentum,product_fit,audience_value,actionability,novelty} 0–5,
  wordstat_queries [{phrase,frequency}], optional emerging_reason. При missing
  demand=null; concrete URLs любых разрешённых источников, не рубрики/главные.
- `python3 <ROOT>/scripts/validate_email_draft.py <WORK>/draft.json --output <WORK>/qa.json`
  subject, preheader, utm_campaign, expected_articles 3–5, html,
  brand_profile {brand_name, sender_name, font_family, colors: {background,paper,
  text,paragraph,muted,accent,dark,light}, optional required_labels}. Все значения
  принадлежат текущему бизнесу. Валидатор сверяет обязательные токены с профилем,
  а не палитру/портрет методолога. operational-ссылки не требуют UTM.

Ошибка входа/файла → ERROR и ненулевой exit code; blocked QA/ranking без допустимой
темы → ненулевой код. Это статическая QA, не доказательство отображения в email-
клиенте: preview/отписку проверить отдельно, если доступна платформа.
