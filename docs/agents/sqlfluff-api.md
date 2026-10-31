# SQLFluff 4.5.0: API и запуск

Справка для агентов и мейнтейнеров: как запускать линтер в этом репозитории и как
интроспектировать правила, не подбирая внутренний API заново. Версия закреплена в
`requirements.txt` (`4.5.0`).

## Запуск

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt

python3 scripts/check.py --all   # корпус примеров + сверка согласованности
```

`scripts/check.py` находит линтер в порядке: `$SQLFLUFF` → `.venv/bin/sqlfluff` →
`sqlfluff` в `PATH`. Выбрать конфиг: `--config .sqlfluff.base`.

## Список правил (CLI)

```bash
.venv/bin/sqlfluff rules          # код, имя, группы, алиасы — все правила
.venv/bin/sqlfluff rules -vv      # подробнее
```

Вывод вида `CP02: [capitalisation.identifiers] ... groups: all, core, ...` —
это источник точных кодов и имён правил для `.sqlfluff`.

## Интроспекция из Python

Рабочие вызовы на 4.5.0 (проверялись на этой версии):

```python
from sqlfluff.core import Linter, FluffConfig

cfg = FluffConfig(overrides={"dialect": "postgres"})
linter = Linter(config=cfg)

# Прогнать строку и получить коды сработавших правил.
result = linter.lint_string("select ID from t where a != 1\n")
codes = sorted({v.rule_code() for v in result.violations})

# Полный набор правил, доступных в текущей конфигурации.
rules = linter.get_rulepack().rules        # list[BaseRule], ~79 на 4.5.0
codes = [r.code for r in rules]            # 'CP02', 'LT02', ...
names = [r.name for r in rules]            # 'capitalisation.identifiers', ...
groups = rules[0].groups                   # ('all', 'core', ...)

# Карта «устаревший код → новые коды» (L010 → {CP01, CP02, CP03}).
from sqlfluff.core.rules import get_ruleset
reference_map = get_ruleset().rule_reference_map()   # это МЕТОД, вызвать ()
```

### Ловушки 4.5.0

Здесь легко потерять время — эти формы **не** работают:

- `get_ruleset().rules` — такого атрибута нет; список правил берётся из
  `Linter(...).get_rulepack().rules`.
- `get_ruleset().rule_reference_map` без вызова — в 4.5.0 это **метод**;
  `len(...)` на нём даёт `TypeError`.
- Атрибуты `FluffConfig` читаются через методы/словари, а не как свойства;
  не угадывать — смотреть `dir()`/исходники установленной версии.
- Импорты вида `sqlfluff.core.plugin.hook`, `sqlfluff.core.plugin.load_all_plugins`
  на 4.5.0 не существуют.

Общее правило: при сомнении сначала `sqlfluff rules` (CLI) — он всегда
показывает фактический набор правил установленной версии.
