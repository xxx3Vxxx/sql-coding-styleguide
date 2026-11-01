## Проверка

Стандарт проверяется скриптами; одна команда запускает обе проверки:

```bash
python3 scripts/check.py --all
```

Это корпус примеров и SQL-блоки «Хорошо» из `STANDARD.md` (`scripts/check.py`)
и сверка согласованности документа, §8-маппинга и конфигов
(`scripts/check_consistency.py`). Нужен SQLFluff (версия — `requirements.txt`).
Запуск линтера и интроспекция его правил — `docs/agents/sqlfluff-api.md`.
Инварианты «правило ↔ §8 ↔ конфиг» — `docs/agents/standard-model.md`.
Ту же команду гоняет включённый `.githooks/pre-commit`
(`git config core.hooksPath .githooks`).

## Agent skills

### Модель стандарта

Устройство правил, §8.2-маппинг и инварианты согласованности (правило ↔ §8 ↔
конфиг). See `docs/agents/standard-model.md`.

### Issue tracker

Issues and specs live as markdown files under `.scratch/`. See `docs/agents/issue-tracker.md`.

### Triage labels

The five canonical triage roles, each label string equal to its name. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `GLOSSARY.md` and `docs/adr/` at the repo root. See `docs/agents/domain.md`.
