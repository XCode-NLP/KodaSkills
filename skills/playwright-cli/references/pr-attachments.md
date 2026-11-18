# Прикрепление скриншотов и видео к pull request

`gh` 2.99+ загружает локальные изображения и видео повторяемой опцией `--attach` в `gh pr create`, `gh pr comment`, `gh pr edit`, `gh issue create`, `gh issue comment` и `gh issue edit`. Принимаются PNG, JPEG, GIF, WebP, SVG, MP4, MOV и WebM, поэтому результат `playwright-cli screenshot` и `video-start` можно прикреплять как есть.

## Когда прикреплять

Прикрепляй визуальные доказательства, когда это избавляет проверяющего от необходимости разворачивать проект локально: скриншот исправления интерфейса, пара «до/после», короткое видео нового пользовательского сценария или состояние сбоя при оформлении бага. Пропускай это для рефакторингов, изменений только в бэкенде и всего, что уже видно в диффе.

## Из локальной сессии

```bash
# снять доказательства
playwright-cli open http://localhost:3000/settings
playwright-cli screenshot --filename=settings-after.png
playwright-cli video-start settings-flow.webm
playwright-cli click e5
playwright-cli fill e7 "New name" --submit
playwright-cli video-stop

# прикрепить при создании PR; альтернативный текст идёт после "#" (только для изображений)
gh pr create --title "fix(settings): keep name after save" --body-file body.md \
  --attach './settings-after.png#Settings page after saving' --attach ./settings-flow.webm

# или прокомментировать существующий PR или issue
gh pr comment 123 --body "Recorded the new flow end to end." --attach ./settings-flow.webm
gh issue comment 456 --body "Failure state after submitting the form." --attach ./failure.png
```

Сошлись на файл в теле как `![alt](./settings-after.png)`, чтобы вставить его в текст, — `gh` перепишет путь на URL загруженного файла. Вложения, на которые нет ссылок, добавляются в конец в порядке флагов.

## Ограничения

- Изображения до 10 МБ, видео до 10 МБ на бесплатных планах и до 100 МБ на платных, поэтому делай записи короткими.
- Альтернативный текст для видео не поддерживается.
- Для загрузки нужен доступ на push в репозиторий.
- Доступно только на GitHub.com и GitHub Enterprise Cloud.

## Из CI

Прикрепляй скриншоты и видео, которые Playwright Test уже сохраняет в `test-results` (`screenshot: 'only-on-failure'`, `video: 'retain-on-failure'`), той же командой:

```yaml
permissions:
  pull-requests: write
steps:
  - run: npx playwright test
  - name: Attach failure screenshots and videos to the PR
    if: failure() && github.event_name == 'pull_request'
    env:
      GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    run: |
      files=$(find test-results -name '*.png' -o -name '*.webm' | head -20)
      if [ -n "$files" ]; then
        gh pr comment ${{ github.event.pull_request.number }} \
          --body "Failure screenshots and videos from run ${{ github.run_id }}." \
          $(printf -- '--attach %s ' $files)
      fi
```

Чтобы показать новую возможность красиво, запиши сценарий-витрину, как описано в [video-recording.md](video-recording.md), и прикрепи получившийся WebM тем же способом.
