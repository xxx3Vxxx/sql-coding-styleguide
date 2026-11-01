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

`scripts/check.py` находит линтер в порядке: `$SQLFLUFF` → `.venv/bin/sqlfluff`
текущего каталога → `.venv/bin/sqlfluff` **основного checkout** (путь берётся из
`git rev-parse --git-common-dir`; это спасает git-worktree, где `.venv` нет) →
`sqlfluff` в `PATH`. Выбрать конфиг: `--config .sqlfluff.base`.

## Список правил (CLI)

```bash
.venv/bin/sqlfluff rules          # код, имя, группы, алиасы — все правила
.venv/bin/sqlfluff rules -vv      # подробнее
```

Вывод вида `CP02: [capitalisation.identifiers] ... groups: all, core, ...` —
это источник точных кодов и имён правил для `.sqlfluff`.

## Секции раскладки (layout)

Какие `[sqlfluff:layout:type:*]` вообще существуют, видно в дефолтном конфиге
установленной версии:

```bash
grep -oE '^\[sqlfluff:layout:type:[a-z_]+\]' \
  .venv/lib/python*/site-packages/sqlfluff/core/default_config.cfg
```

Секция с именем, для которого парсер **не** строит узел (в 4.5.0 так с
`returning_clause`), принимается конфигом, но ни на что не влияет: наличие
секции в дефолте ещё не значит, что рычаг работает. Проверяйте фактом —
`sqlfluff lint`/`sqlfluff parse` на пробном файле, а не наличием секции.

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

## Пробы конфига

Чтобы проверить, как линтер поведёт себя с другой секцией или значением, не
правьте `.sqlfluff` — соберите временный конфиг и прогоните по нему CLI:

```bash
cp .sqlfluff /tmp/probe.sqlfluff
printf '\n[sqlfluff:layout:type:common_table_expression]\nspacing_within = single\n' >> /tmp/probe.sqlfluff
.venv/bin/sqlfluff lint --config /tmp/probe.sqlfluff path/to/file.sql
```

Подменять существующее значение удобнее `sed` по точному якорю
(`sed 's/^indent_unit = space/indent_unit = space\nindented_joins = True/'`), а
не догадываясь о структуре файла.

Ловушки (4.5.0):

- `FluffConfig.from_string(...)` падает, если одна INI-секция встречается
  дважды (например, вы дописываете `[sqlfluff:rules:X]` к конфигу, где она уже
  есть). Для проб надёжнее файл + `--config`, а не сборка строки в Python.
- При линте файла **вне** репозитория `sqlfluff lint` без `--config` не находит
  `.sqlfluff` и падает с `No dialect was specified`. Диалект берётся из
  конфига, а конфиг ищется вверх по дереву от линтуемого пути: для файлов в
  `/tmp` передавайте `--config` **явно**.
