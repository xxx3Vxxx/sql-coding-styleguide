## Проверка

Стандарт проверяется скриптами; одна команда запускает обе проверки:

```bash
python3 scripts/check.py --all
```

Это корпус примеров (`scripts/check.py`, линтер по `examples/`) и сверка
согласованности документа, §8-маппинга и конфигов (`scripts/check_consistency.py`).
Нужен SQLFluff (версия — `requirements.txt`). Запуск линтера и интроспекция его
правил — `docs/agents/sqlfluff-api.md`.

## Agent skills

### Issue tracker

Issues and specs live as markdown files under `.scratch/`. See `docs/agents/issue-tracker.md`.

### Triage labels

The five canonical triage roles, each label string equal to its name. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `GLOSSARY.md` and `docs/adr/` at the repo root. See `docs/agents/domain.md`.
