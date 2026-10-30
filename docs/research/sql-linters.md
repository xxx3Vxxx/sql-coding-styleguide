# Ландшафт инструментов проверки и форматирования SQL

Дата обзора: **2026-10-31**.
Контекст проекта: корпоративный стайлгайд SQL; основная СУБД — **PostgreSQL**, второстепенная — **SQLite**; профиль нагрузки — **OLTP**; много хранимых функций/процедур на **plpgsql**, но **plpgsql вне области стандарта**. Дополнительный артефакт проекта — эталонный (референсный) конфиг линтера.

## Как читать этот документ

* Каждое фактическое утверждение сопровождается ссылкой на первоисточник (официальный репозиторий, официальная документация, страница релизов).
* Непроверенные или косвенные сведения помечены явно как **[не проверено]**.
* Оценки «подходит / не подходит» — это выводы под задачу проекта, а не свойство инструментов.
* Часть цифр (число правил, число диалектов) меняется от релиза к релизу; они приведены как ориентир на дату обзора со ссылкой.

## Терминология (используется в отчёте)

* **Linter (линтер)** — инструмент с движком правил, выдающий диагностики.
* **Formatter (форматтер)** — инструмент, переписывающий код в единый стиль без движка правил.
* **Auto-fix** — автоматическое исправление нарушений.
* **CST/AST** — дерево разбора (конкретного/абстрактного синтаксиса).
* **plpgsql** — процедурный язык PostgreSQL (тела `CREATE FUNCTION/PROCEDURE ... LANGUAGE plpgsql`).

---

## 1. SQLFluff

**Источники:** <https://github.com/sqlfluff/sqlfluff>, <https://docs.sqlfluff.com/>

### 1.1. Что это
Модульный линтер SQL с авто-форматированием, написанный на Python. Позиционируется как dialect-flexible и configurable, ориентирован на ELT/аналитику, поддерживает Jinja-шаблоны и dbt ([README](https://github.com/sqlfluff/sqlfluff)). Это **линтер + авто-форматтер**, а не чистый форматтер.

### 1.2. Диалекты: PostgreSQL, SQLite
* Поддерживается диалект **`postgres`** и диалект **`sqlite`** ([страница диалектов](https://docs.sqlfluff.com/en/stable/reference/dialects.html)).
* Диалект `postgres` «based around the PostgreSQL spec» ([страница диалектов](https://docs.sqlfluff.com/en/stable/reference/dialects.html)). `redshift` и `greenplum` наследуются от `postgres`.
* Всего поддерживается порядка 28 диалектов ([страница диалектов](https://docs.sqlfluff.com/en/stable/reference/dialects.html)) — то есть это широкий, но не полный парсер PostgreSQL. Диалекты активно правятся (в релиз-ноутах упомянуты десятки исправлений парсера PostgreSQL, SQLite и др., см. [releases](https://github.com/sqlfluff/sqlfluff/releases)).
* **Важно:** грамматика PostgreSQL в SQLFluff не совпадает с реальным парсером Postgres; это отдельная реализация на Python, поэтому возможны «unparsable section» на нестандартном/редком синтаксисе.

### 1.3. Возможности: правила, настройка, отключение, severity, авто-фикс, плагины
* **79 правил в 11 категориях** ([Rules Reference](https://docs.sqlfluff.com/en/stable/reference/rules.html)). Категории: Aliasing (AL), Ambiguous (AM), Capitalisation (CP), Convention (CV), Jinja (JJ), Layout (LT), Oracle (OR), Postgres (PG), References (RF), Structure (ST), Tsql (TQ).
* Правила включаются/отключаются через конфиг: `rules` и `exclude_rules` в секции `[sqlfluff]` ([Rule Configuration](https://docs.sqlfluff.com/en/latest/configuration/rule_configuration.html)); можно указывать как код, так и имя правила, а также группу `core` (единственная встроенная группа) ([Rule Configuration](https://docs.sqlfluff.com/en/latest/configuration/rule_configuration.html)).
* **Подавление по месту:** строки/диапазоны/файлы через `-- noqa` и `-- sqlfluff:`; `PRS` (parse) и `TMP` (templating) тоже можно игнорировать ([Ignoring errors](https://docs.sqlfluff.com/en/stable/configuration/ignoring.html)).
* **Понижение до warning:** правила, перечисленные в `warnings`, не валят сборку, но показываются ([Rule Configuration](https://docs.sqlfluff.com/en/latest/configuration/rule_configuration.html)). Полноценных «severity levels» (error/warn/info/hint), как в некоторых линтерах, в ядре нет — есть бинарное «ошибка / warning». Отдельные уровни severity есть только в VS Code-расширении (`sqlfluff.linter.diagnosticSeverity`, `diagnosticSeverityByRule`) ([package.json расширения](https://github.com/sqlfluff/vscode-sqlfluff/blob/master/package.json)).
* **Авто-фикс:** `sqlfluff fix` и `sqlfluff format`; большинство правил fix-совместимы (в [Rules Reference](https://docs.sqlfluff.com/en/stable/reference/rules.html) у каждого правила явно указано «Auto-fixable»). Безопасность: fix не трогает файлы с parse/templating-ошибками, если только не задан `fix_even_unparsable` ([pre-commit](https://docs.sqlfluff.com/en/stable/usage/pre-commit.html)).
* **Плагины и кастомные правила:** архитектура на [pluggy](https://pluggy.readthedocs.io/), плагин должен быть установлен как Python-пакет с entry point `sqlfluff` ([Custom Rules](https://docs.sqlfluff.com/en/stable/development/custom-rules.html), [Plugins](https://docs.sqlfluff.com/en/stable/development/plugins.html)). Есть [example plugin](https://github.com/sqlfluff/sqlfluff/tree/main/plugins/sqlfluff-plugin-example).

### 1.4. Форматирование (стиль)
* Длина строки: `max_line_length` (по умолчанию 80) ([Configuration](https://docs.sqlfluff.com/en/stable/configuration.html), [Layout](https://docs.sqlfluff.com/en/stable/configuration/layout.html)).
* Отступы: секция `[sqlfluff:indentation]` — `indented_joins`, `indented_using_on`, `indented_on_contents`, `indented_ctes`, `indented_then`, `implicit_indents`, `template_blocks_indent` и др. ([Layout](https://docs.sqlfluff.com/en/stable/configuration/layout.html)); размер шага отступа задаётся `tab_space_size`, и в in-file директивах показан `tab_space_size:2` ([Configuration](https://docs.sqlfluff.com/en/stable/configuration.html)). Hanging indents с 2.0 не поддерживаются ([Layout](https://docs.sqlfluff.com/en/stable/configuration/layout.html)).
* Регистр ключевых слов/идентификаторов/функций/литералов/типов — правилами CP01–CP05 (`capitalisation_policy` / `extended_capitalisation_policy`, значения `upper`, `lower`, `capitalise`, `consistent`, а для идентификаторов ещё `pascal`/`snake`/`camel`) ([Capitalisation rules](https://docs.sqlfluff.com/en/stable/reference/rules/capitalisation.html)).
* Выравнивание (align) — через `[sqlfluff:layout:type:<type>]`: `spacing_before/after/within`, `line_position` (`trailing`/`leading`/`alone`/`:strict`/`:attached`), `keyword_line_position`, `align_within`, `align_scope`, `alignment_coordinate_space` ([Layout](https://docs.sqlfluff.com/en/stable/configuration/layout.html)).
* Переносы: `list_wrapping` (по умолчанию каждый элемент списка на своей строке либо `fill`) ([Layout](https://docs.sqlfluff.com/en/stable/configuration/layout.html)).
* Точку размещения запятых (leading/trailing) задаёт `[sqlfluff:layout:type:comma] line_position` ([Layout](https://docs.sqlfluff.com/en/stable/configuration/layout.html)).

### 1.5. Стиль именования
* Встроенных правил «именование с префиксами/суффиксами» **нет**. Есть:
  * `CP02 capitalisation.identifiers` — регистр/регистр-стиль неквотированных идентификаторов, включая `snake`/`camel`/`pascal` ([Capitalisation rules](https://docs.sqlfluff.com/en/stable/reference/rules/capitalisation.html));
  * `RF04 references.keywords` (не использовать ключевые слова как идентификаторы), `RF05 references.special_chars` (только буквы/цифры/`_`), `RF06 references.quoting` ([References rules](https://docs.sqlfluff.com/en/stable/reference/rules/references.html));
  * `AL06 aliasing.length` (мин./макс. длина алиаса) ([Aliasing rules](https://docs.sqlfluff.com/en/stable/reference/rules/aliasing.html)).
* Для корпоративных нейминг-конвенций существует сторонний плагин **`sqlfluff-common-conventions`** с правилами CC01–CC06 (boolean-колонки `is_*`/`has_*`, суффиксы `at`/`date`, списки разрешённых/запрещённых строк, regex для имён колонок/таблиц). Плагин заявляет совместимость с **PostgreSQL** (а также BigQuery/Databricks) и поддержку snake_case/camelCase/PascalCase ([sqlfluff-common-conventions on PyPI](https://pypi.org/project/sqlfluff-common-conventions/)). Релиз 0.4.0 — 2024-06-12, один мейнтейнер; зрелость средняя. **[не проверено]** актуальность для SQLFluff 4.x.

### 1.6. plpgsql и хранимые процедуры
* SQLFluff **не разбирает тела plpgsql**: внутренности функции/процедуры трактуются как строковый литерал и не линтуются — это явно описано в issue [#3093](https://github.com/sqlfluff/sqlfluff/issues/3093) (функциональность так и не сделана на дату обзора; PL/pgSQL не поддерживается).
* Поддерживаются SQL-тела функций (в т.ч. SQL-стандартный `BEGIN ATOMIC`), например в релиз-ноутах есть правки «Allow PostgreSQL `BEGIN ATOMIC` function bodies to parse `UNION ALL`» ([releases](https://github.com/sqlfluff/sqlfluff/releases)).
* **Для нашего проекта это скорее плюс:** plpgsql вне области стандарта, поэтому «слепое пятно» SQLFluff совпадает с границей стандарта. Заголовок функции (`CREATE FUNCTION ... RETURNS ... LANGUAGE ...`) и внешний DDL при этом линтуются.

### 1.7. Интеграции
* **CLI:** `lint`, `fix`, `format`, `parse`, `render`, `rules`, `dialects` ([CLI reference](https://docs.sqlfluff.com/en/stable/reference/cli.html)).
* **CI:** встроенные форматы `github-annotation` и `github-annotation-native` (аннотации PR), а также `--format gitlab` для GitLab Code Quality report ([CI/CD Integration](https://docs.sqlfluff.com/en/stable/usage/ci-cd.html)). Ограничение: GitHub показывает ограниченное число нативных аннотаций за прогон, рекомендуется yuzutech-annotation ([CI/CD Integration](https://docs.sqlfluff.com/en/stable/usage/ci-cd.html)).
* **pre-commit:** хуки `sqlfluff-lint` и `sqlfluff-fix` ([pre-commit](https://docs.sqlfluff.com/en/stable/usage/pre-commit.html)).
* **VS Code:** расширение [sqlfluff/vscode-sqlfluff](https://github.com/sqlfluff/vscode-sqlfluff).
* **Docker-образ:** [hub.docker.com/r/sqlfluff/sqlfluff](https://hub.docker.com/r/sqlfluff/sqlfluff).

### 1.8. Материалы проекта и стабильность
* **Лицензия:** MIT ([README](https://github.com/sqlfluff/sqlfluff)).
* **Активность:** релизы ежемесячно ([README](https://github.com/sqlfluff/sqlfluff)); в релиз-ноутах анонсируются десятки контрибьюторов на релиз ([releases](https://github.com/sqlfluff/sqlfluff/releases)). Текущая мажорная ветка — **4.x** (в [release notes](https://docs.sqlfluff.com/en/stable/reference/release-notes.html) есть «Upgrading to 4.2», в примере pre-commit — `rev: 4.5.0`).
* **Стабильность API:** 2.0 и 3.0 несли ломающие изменения (переименование правил `L0XX` → группы, смена настроек layout) ([release notes](https://docs.sqlfluff.com/en/stable/reference/release-notes.html)); на 4.x — относительно спокойно, но API парсера/дерева может меняться между минорными версиями.
* **Сообщество:** Slack (приглашение в шапке docs), большое число контрибьюторов, сторонние плагины.

### 1.9. Ограничения и подводные камни в CI
* Производительность: чистый Python, на больших репозиториях медленнее Rust-аналогов; есть опциональный Rust-парсер (`pip install sqlfluff[rs]`, «experimental until 5.x») ([README](https://github.com/sqlfluff/sqlfluff), [release notes](https://docs.sqlfluff.com/en/stable/reference/release-notes.html)).
* Возможны «unparsable section» и ложные срабатывания на нестандартном синтаксисе — не совпадающий с PostgreSQL парсер.
* Фиксы могут менять семантику в диалектах, чувствительных к регистру (предупреждение в [Capitalisation rules](https://docs.sqlfluff.com/en/stable/reference/rules/capitalisation.html) про CP02).
* Templating (Jinja/dbt) усложняет конфигурацию и замедляет; при отсутствии шаблонов следует использовать `templater = raw`.
* GitHub-аннотации ограничены по количеству ([CI/CD Integration](https://docs.sqlfluff.com/en/stable/usage/ci-cd.html)).

---

## 2. sqruff

**Источники:** <https://github.com/quarylabs/sqruff>, <https://playground.quary.dev/docs/>

### 2.1. Что это
SQL-линтер и форматтер на **Rust**, сознательно совместимый с SQLFluff: «Sqruff is designed to be compatible with SQLFluff … Copy SQLFluff tests» ([CLAUDE.md](https://github.com/quarylabs/sqruff/blob/main/CLAUDE.md)). Позиционируется как быстрый аналог SQLFluff ([README](https://github.com/quarylabs/sqruff)).

### 2.2. Диалекты
* В документации перечислено **27 диалектов**, среди них **`postgres`** и **`sqlite`** ([Dialects](https://playground.quary.dev/docs/reference/dialects/)).
* Для `postgres` есть опции `pg_trgm` и `pgvector` ([Dialects](https://playground.quary.dev/docs/reference/dialects/)).
* Релиз v0.44.0 содержит правки парсера SQLite (`ATTACH`, `DETACH`, `VACUUM`, `REINDEX`, `ANALYZE`) ([releases](https://github.com/quarylabs/sqruff/releases)).

### 2.3. Правила и настройка
* Реализует тот же набор кодов/имён, что SQLFluff: AL, AM, CP, CV, JJ, LT (LT01–LT15), OR, PG (PG01/PG02), RF (RF01–RF07), ST (ST01–ST12), TQ ([Rules](https://playground.quary.dev/docs/reference/rules/)). Часть правил помечена как Core Rule.
* Конфиг — файл `.sqruff` (INI) в стиле SQLFluff: секции `[sqruff]`, `[sqruff:rules:...]`, `[sqruff:layout:type:...]`; `dialect`, `exclude_rules` ([README](https://github.com/quarylabs/sqruff), [Rules](https://playground.quary.dev/docs/reference/rules/)).
* Есть `noqa`-подавление и ignore-files ([docs](https://playground.quary.dev/docs/usage/noqa/)).
* Авто-фикс: `sqruff fix` ([README](https://github.com/quarylabs/sqruff)); у правил указан флаг Fixable ([Rules](https://playground.quary.dev/docs/reference/rules/)).

### 2.4. Форматирование и именование
* Форматирование настраивается теми же layout-секциями, что в SQLFluff (`[sqruff:layout:type:<type>]`) ([Dialects](https://playground.quary.dev/docs/reference/dialects/), [Rules](https://playground.quary.dev/docs/reference/rules/)).
* Правила именования — те же, что в SQLFluff (CP02, RF04/RF05/RF06, AL06); отдельных naming-convention правил нет (совместимость с SQLFluff-набором).

### 2.5. plpgsql
* **[не проверено]** явной документации о поддержке тел plpgsql не найдено; учитывая совместимость с SQLFluff, вероятно такое же ограничение (тело функции не линтуется). Требует отдельной проверки при реальном использовании.

### 2.6. Интеграции
* CLI (`sqruff lint`, `sqruff fix`) и **LSP-сервер** (`sqruff lsp`) ([README](https://github.com/quarylabs/sqruff)).
* Редакторы: VS Code и Zed (в самом репозитории, каталоги `editors/code`, `editors/zed`) ([README](https://github.com/quarylabs/sqruff)).
* CI: добавлена генерация **GitLab Code Quality reports** ([releases v0.44.0](https://github.com/quarylabs/sqruff/releases)). **[не проверено]** наличие готовых GitHub Action и pre-commit-хука.
* Python-биндинги (PyO3), WASM-плейграунд ([CLAUDE.md](https://github.com/quarylabs/sqruff/blob/main/CLAUDE.md), [README](https://github.com/quarylabs/sqruff)).

### 2.7. Материалы проекта и стабильность
* **Лицензия:** Apache-2.0 ([LICENSE](https://github.com/quarylabs/sqruff/blob/main/LICENSE), [README](https://github.com/quarylabs/sqruff)).
* **Активность:** очень высокая; последний релиз на дату обзора — **v0.44.0 от 2026-10-30** ([releases](https://github.com/quarylabs/sqruff/releases)).
* **Стабильность API:** версия **< 1.0** (0.44.x); возможны изменения. Проект сознательно следует SQLFluff, отслеживает SHA upstream ([CLAUDE.md](https://github.com/quarylabs/sqruff/blob/main/CLAUDE.md)).

### 2.8. Ограничения
* Ещё до 1.0 — риск несовместимых изменений.
* Полнота парсера/правил, вероятно, ниже SQLFluff, несмотря на совместимый набор кодов (сторонние бенчмарки говорят о меньшем числе «активных» правил, но это сторонний источник — [crates.io/…/sqrust-core](https://crates.io/crates/sqrust-core), **[не проверено]** как оценка sqruff).

---

## 3. sqlfmt

**Источники:** <https://github.com/tconbeer/sqlfmt>, <https://sqlfmt.com/>

### 3.1. Что это
Опinionated **форматтер** (аналог Black/gofmt для SQL), написанный на Python. Явно **не линтер**: не строит AST, только лексирует и следит за небольшим набором токенов ([README](https://github.com/tconbeer/sqlfmt)).

### 3.2. Диалекты, область применения
* Использует «polyglot»-диалект, покрывающий почти все SQL-диалекты без настройки; исключение — ClickHouse (чувствителен к регистру, есть флаг `--dialect clickhouse`) ([README](https://github.com/tconbeer/sqlfmt)).
* Работает только со statements `select`, `delete`, `grant`, `revoke`, `create function` ([README](https://github.com/tconbeer/sqlfmt), [docs](https://sqlfmt.com/docs/intro)).

### 3.3. Настраиваемость, форматирование
* **Не настраивается, кроме длины строки** (по умолчанию 88, флаги `-l`/`--line-length`); навязывает единственный стиль ([README](https://github.com/tconbeer/sqlfmt), [Configuring sqlfmt](https://sqlfmt.com/docs/getting-started/configuring-sqlfmt)).
* Правил линтинга, нейминг-правил, severity — нет.

### 3.4. plpgsql
* Форматтер работает с `create function`, но это лексический форматтер без разбора plpgsql; **[не проверено]** корректность форматирования тел plpgsql.

### 3.5. Интеграции
* CLI с `--check`/`--diff` (для CI), stdin (`-`) ([README](https://github.com/tconbeer/sqlfmt)).
* pre-commit, VS Code, Docker, GitHub Actions; интеграция с SQLFluff (форматтер + линтер) ([README](https://github.com/tconbeer/sqlfmt)).
* Питает кнопку Format в dbt Cloud IDE ([README](https://github.com/tconbeer/sqlfmt)).

### 3.6. Материалы и ограничения
* **Лицензия:** Apache-2.0 ([LICENSE](https://raw.githubusercontent.com/tconbeer/sqlfmt/main/LICENSE)).
* **Активность:** релизы регулярные; последний в истории PyPI на дату обзора — 0.30.0 (май 2026) ([shandy-sqlfmt on PyPI](https://pypi.org/project/shandy-sqlfmt/)). Пакет на PyPI называется `shandy-sqlfmt`, не `sqlfmt` ([README](https://github.com/tconbeer/sqlfmt)).
* **Ограничения:** в README есть прямое предупреждение — «sqlfmt may not always produce the formatted output you want. It might even break your SQL syntax… only run on files in a version control system» ([README](https://github.com/tconbeer/sqlfmt)). Не подходит как основной инструмент для корпоративного стандарта с настраиваемым стилем.

---

## 4. pgFormatter (pg_format)

**Источники:** <https://github.com/darold/pgFormatter>, <http://sqlformat.darold.net/>

### 4.1. Что это
Форматтер/beautifier SQL и **PL/pgSQL** на Perl; «the most advanced SQL and PL/pgSQL code formatter… dedicated to PostgreSQL» ([release announcement v5.7](https://www.postgresql.org/about/news/pgformatter-v57-has-been-released-3125)). Является **только форматтером**, движка правил/линта нет.

### 4.2. Диалекты
* Ориентирован на PostgreSQL (SQL-92/99/2003/2008/2011 + специфичные ключевые слова PostgreSQL), «Works with any other databases too» ([README/man](https://raw.githubusercontent.com/darold/pgFormatter/master/README)); про SQLite специально ничего не заявлено.

### 4.3. Настраиваемость (из man-страницы, [README](https://raw.githubusercontent.com/darold/pgFormatter/master/README))
* Отступ: `-s/--spaces` (по умолчанию 4), `-T/--tabs`.
* Регистр: `-u/--keyword-case` (по умолчанию 2 = uppercase), `-U/--type-case` (по умолчанию 1 = lowercase), `-f/--function-case`, `-I/--ident-case`.
* Переносы/ширина: `-w/--wrap-limit`, `-W/--wrap-after`, `-C/--wrap-comment`.
* Запятые: `-b/--comma-start`, `-e/--comma-end`.
* Прочее: `-i/--inplace`, `-n/--nocomment`, `-k/--keep-newline`, `--extra-keyword`, `--extra-function`, `--no-space-function`, `--redundant-parenthesis`, `--matching-paren-newline`, `--vertical-align` (выравнивание определений колонок в `CREATE TABLE`).
* Конфиг-файл: `./.pg_format`, `$HOME/.pg_format` или `$XDG_CONFIG_HOME/pg_format/pg_format.conf`, либо `-c/--config` ([README](https://raw.githubusercontent.com/darold/pgFormatter/master/README)).
* Регистр идентификаторов: квотированные идентификаторы не меняются ([README](https://raw.githubusercontent.com/darold/pgFormatter/master/README)).

### 4.4. Именование, правила, plpgsql
* Правил линтинга и нейминг-правил нет.
* PL/pgSQL форматируется (есть `-k/--keep-newline` для пустых строк в plpgsql) ([README](https://raw.githubusercontent.com/darold/pgFormatter/master/README)); в релизе v5.10 (2026-05-11) отмечены правки форматирования `DO $$ ... $$`, `RETURNING ... INTO`, `CREATE POLICY`, MERGE ([pgFormatter v5.10](https://www.postgresql.org/about/news/pgformatter-v510-has-been-released-3294/)).

### 4.5. Интеграции
* CLI и CGI (HTML/JSON API) ([README](https://raw.githubusercontent.com/darold/pgFormatter/master/README)).
* pre-commit-хук `pg_format` (пример: `--inplace --wrap-limit 120 --files '.*\.sql$'`) ([README](https://raw.githubusercontent.com/darold/pgFormatter/master/README)).
* Плагины редакторов: (Neo)vim, VS Code (bradymholt.pgformatter), Atom, Node-обёртка ([README](https://raw.githubusercontent.com/darold/pgFormatter/master/README)).

### 4.6. Материалы и ограничения
* **Лицензия:** PostgreSQL Licence ([README](https://raw.githubusercontent.com/darold/pgFormatter/master/README)).
* **Активность:** регулярные релизы — v5.6 (2025-03), v5.7 (2025-08), v5.8 (2025-09), v5.10 (2026-05) ([pgFormatter news](https://www.postgresql.org/about/news/pgformatter-v58-has-been-released-3137/)).
* **Ограничения:** не линтер; нет правил, нет severity, нет авто-исправления «по правилам» (по сути единственный режим — переформатировать). «even if not perfect» — формулировка самого автора ([v5.7 announcement](https://www.postgresql.org/about/news/pgformatter-v57-has-been-released-3125)).

---

## 5. Postgres Language Server (postgres_lsp / postgres-language-server)

**Источники:** <https://github.com/supabase-community/postgres-language-server>, <https://pg-language-server.com/>

### 5.1. Что это
Набор языковых инструментов и LSP-реализация для Postgres, построенная на **собственном парсере Postgres `libpg_query`** «to ensure 100% syntax compatibility» ([README](https://github.com/supabase-community/postgres-language-server)). Есть CLI, LSP, HTTP API и WASM.

### 5.2. Диалекты
* Только **PostgreSQL**; SQLite не поддерживается (следует из позиционирования и парсера).

### 5.3. Форматтер
* Форматтер в статусе **preview** ([Formatting](https://pg-language-server.com/latest/features/formatting/)).
* Опции (в `postgres-language-server.jsonc`): `lineWidth` (100), `indentSize` (2), `indentStyle`, `keywordCase`, `constantCase`, `typeCase`, `commaStyle`, `logicalOperatorPlacement`, `layout` (`fit`/`expanded`), `castStyle`, `clauseBodyStyle`, `isolateSemicolon`, `functionArgumentGroups` ([Formatting](https://pg-language-server.com/latest/features/formatting/)).
* **Важно про plpgsql:** тела функций и `DO` **сохраняются байт-в-байт** (и всегда оборачиваются в dollar-quotes); переформатируются только тела `language sql`, если не задан `skipFnBodies` ([Formatting](https://pg-language-server.com/latest/features/formatting/)). То есть форматирование plpgsql не делается (осознанно, ради сохранности).
* Форматтер проверяет, что отформатированное высказывание парсится в то же дерево; иначе оставляет как есть и выдаёт диагностику ([Formatting](https://pg-language-server.com/latest/features/formatting/)).

### 5.4. Линтер
* Правила сгруппированы: **Correctness, Destructive, Safety, Style, Typecheck**; есть «recommended preset»; часть правил работает только в каталоге миграций, часть требует подключения к БД ([Linter Rules](https://pg-language-server.com/latest/reference/rules/)).
* Значительная часть правил — про безопасность миграций/DDL (locks, table rewrite, `NOT VALID`, `CONCURRENTLY`), а не про стиль/нейминг ([Linter Rules](https://pg-language-server.com/latest/reference/rules/)).
* Для стиля/нейминга: отдельных naming-правил нет; раздел Style — это предпочтения типов (`preferBigInt`, `preferTextField`, `preferIdentity`, `preferJsonb`, `preferTimestamptz`, `banCharField`, `creatingEnum`) ([Linter Rules](https://pg-language-server.com/latest/reference/rules/)).

### 5.5. plpgsql
* Поддержка **частичная**: по умолчанию тело парсится через `libpg_query` и показываются синтаксические ошибки **без точной локации** (вся функция); для глубокого анализа рекомендуется расширение `plpgsql_check` в dev-БД, диагностики которого LSP подхватывает ([PL/pgSQL Support](https://pg-language-server.com/latest/features/plpgsql/)).

### 5.6. Интеграции
* LSP: VSCode, Cursor, Neovim, Zed, Sublime Text ([README](https://github.com/supabase-community/postgres-language-server)).
* CI: first-party **GitHub Action** (`supabase-community/pglt-cli-action`), команда `postgres-language-server check [--skip-db] <path>`; можно поднимать сервис Postgres для расширенных проверок ([Continuous Integration](https://pg-language-server.com/latest/guides/continuous_integration/)).

### 5.7. Материалы и ограничения
* **Лицензия:** MIT ([README](https://github.com/supabase-community/postgres-language-server)).
* **Активность:** высокая (1 100+ коммитов, 5.3k звёзд) ([README](https://github.com/supabase-community/postgres-language-server)); в документации фигурирует гайд «Upgrading to 0.27», т.е. версия ~0.27.x ([Continuous Integration](https://pg-language-server.com/latest/guides/continuous_integration/)).
* **Ограничения:** до 1.0; форматтер preview; не поддерживает SQLite; стилевой линтинг ограничен.

---

## 6. squawk

**Источники:** <https://github.com/sbdchd/squawk>, <https://squawkhq.com/>

### 6.1. Что это
Линтер **безопасности миграций и SQL для PostgreSQL** на Rust («Linter for Postgres migrations & SQL») ([README](https://github.com/sbdchd/squawk)). Не форматтер.

### 6.2. Диалекты
* Только **PostgreSQL** (есть настройка `pg_version`) ([CLI](https://squawkhq.com/docs/cli)). SQLite не поддерживается.

### 6.3. Правила и настройка
* Большой набор правил: `adding-*`, `ban-*` (drop column/table/schema/view/type/function/trigger/constraint и др.), `prefer-*` (bigint, identity, text, timestamptz, robust-stmts), `require-*` (concurrent index creation/deletion, timeout settings, lock timeout), плюс `syntax-error`, `semantic-error`, `identifier-too-long` ([Rules Overview](https://squawkhq.com/docs/rules)).
* Отключение/включение: `--exclude`, `--include` (exclude имеет приоритет), `--exclude-path` ([CLI](https://squawkhq.com/docs/cli)).
* Конфиг `.squawk.toml` вверх по дереву, `-c/--config`; параметры `pg_version`, `assume_in_transaction` ([CLI](https://squawkhq.com/docs/cli)).
* Severity-уровней нет; правила либо включены, либо нет.

### 6.4. Форматирование, именование, plpgsql
* Форматирования нет; naming-правил нет; специальной работы с plpgsql нет.

### 6.5. Интеграции
* CLI, чтение из stdin ([CLI](https://squawkhq.com/docs/cli)).
* GitHub Action ([squawk-action](https://github.com/sbdchd/squawk-action)) и GitHub App / `upload-to-github` для комментариев в PR ([GitHub Integration](https://squawkhq.com/docs/github_app)).
* LSP-сервер `squawk server` ([CLI](https://squawkhq.com/docs/cli)), VS Code-расширение ([Quick Start](https://squawkhq.com/docs/)).
* pre-commit (id `squawk`), npm/pip/Docker ([README](https://github.com/sbdchd/squawk)).

### 6.6. Материалы и ограничения
* **Лицензия:** Apache-2.0 / MIT (файлы `LICENSE-APACHE`, `LICENSE-MIT`) ([README](https://github.com/sbdchd/squawk)).
* **Активность:** высокая; последний релиз v2.70.0 ([releases](https://github.com/sbdchd/squawk/releases)).
* **Ограничения:** не про стиль/форматирование/нейминг; только Postgres. Полезен как дополнение (безопасность DDL), но не как ядро стайлгайд-инструмента.

---

## 7. pglast и libpg_query (низкоуровневые парсеры)

**Источники:** <https://github.com/lelit/pglast>, <https://github.com/pganalyze/libpg_query>

### pglast
* Python-модуль, экспонирующий parse-дерево Postgres (через `libpg_query`); «PostgreSQL Languages AST and statements prettifier» ([README](https://github.com/lelit/pglast)).
* Версии веток покрывают PG10…PG18 ([README](https://github.com/lelit/pglast)).
* **Лицензия:** GPL-3.0-or-later ([README](https://github.com/lelit/pglast)). **Важно для корпоративного использования.**
* Есть некий «prettifier», но это библиотека, а не линтер: нет движка правил, нет конфигурации стиля, нет интеграций. Годится как основа для собственных правил/скриптов.

### libpg_query
* C-библиотека, извлекающая парсер Postgres для использования вне сервера ([README](https://github.com/pganalyze/libpg_query)).
* Умеет **парсить PL/pgSQL**: `pg_query_parse_plpgsql` возвращает `PLpgSQL_function` со структурированным телом (см. пример в README) ([README](https://github.com/pganalyze/libpg_query)). Это ключевой факт: реальный анализ plpgsql строится на `libpg_query`/`plpgsql_check`, а не на «общих» линтерах.
* Есть обёртки: Ruby, Go, Rust, Node, Python (pglast, psqlparse), OCaml ([README](https://github.com/pganalyze/libpg_query)).
* **Лицензия:** BSD-3-Clause (части — PostgreSQL licence) ([README](https://github.com/pganalyze/libpg_query)).
* **Активность:** ветка `18-latest` — active development; предыдущие ветки только critical fixes ([README](https://github.com/pganalyze/libpg_query)).

---

## 8. SQLCheck

**Источник:** <https://github.com/jarulraj/sqlcheck>

* C++-инструмент, автоматически ищет SQL-антипаттерны; заявляет «targets all major SQL dialects» (теги включают PostgreSQL, SQLite, MySQL, MSSQL, Oracle) ([README](https://github.com/jarulraj/sqlcheck)).
* Категории правил: Logical/Physical Design, Query, Application anti-patterns; выбор риска `-r` (1 — все, 2 — medium+high, 3 — high), файл `-f`, цвет `-c`, verbose `-v` ([README](https://github.com/jarulraj/sqlcheck)).
* **Лицензия:** Apache-2.0 ([README](https://github.com/jarulraj/sqlcheck)).
* **Активность/статус:** последний релиз v1.3; агрегатор analysis-tools помечает проект как **Deprecated** ([analysis-tools/sqlcheck](https://analysis-tools.dev/tool/sqlcheck)); по данным стороннего каталога — последний коммит ~2 года назад, обновление зеркала 2022-07 ([softono](https://softono.com/software/sqlcheck), [SourceForge mirror](https://sourceforge.net/projects/sqlcheck.mirror)).
* **Вывод:** не подходит — нет форматирования, нет настраиваемого стиля, фактически не поддерживается.

---

## 9. Прочие специализированные и низкоуровневые инструменты

### 9.1. pgsanity
* Проверка **синтаксиса** SQL для PostgreSQL через `ecpg` (тот же парсер, что в Postgres) ([README](https://github.com/markdrago/pgsanity)).
* Только синтаксис; нет правил/форматирования/нейминга. CLI, stdin, xargs ([README](https://github.com/markdrago/pgsanity)).
* **Лицензия:** MIT ([PyPI](https://pypi.org/project/pgsanity/0.3.0)). Активность низкая/неактивная (Snyk: maintenance INACTIVE, последний релиз ~11 мес. назад на дату обзора) ([Snyk](https://security.snyk.io/package/pip/pgsanity)).

### 9.2. sqlint (purcell/sqlint)
* Ruby-linter, проверяет ANSI/PostgreSQL синтаксис через парсер Postgres; интеграции с Emacs/Vim/Sublime, pre-commit ([README](https://github.com/purcell/sqlint)).
* **Лицензия:** MIT ([README](https://github.com/purcell/sqlint)). Старый проект (создан 2015), только синтаксис, без стилевого движка.

### 9.3. sqlint (npm, joe-re/sql-language-server)
* Node-линтер с набором правил (`align-column-to-the-first`, `column-new-line`, `linebreak-after-clause-keyword` и др.), `--fix`, `--stdin` ([npm](https://www.npmjs.com/package/sqlint)).
* **Лицензия:** MIT. Последняя публикация ~2 года назад ([npm](https://www.npmjs.com/package/sqlint)). Малые масштабы/активность — не корпоративный кандидат.

### 9.4. sqlglot
* Python-парсер/транспайлер/оптимизатор/движок; «no-dependency»; официальные диалекты **Postgres** и **SQLite** ([README](https://github.com/tobymao/sqlglot)).
* Умеет форматировать (`pretty=True`, `identify=True`), ловить синтаксические ошибки (`ParseError`), строить/менять AST, кастомные диалекты ([README](https://github.com/tobymao/sqlglot)).
* **Это не линтер стиля** — нет движка правил/конфигурации стиля/severity. Но отличная основа для кастомных проверок и трансформаций.
* **Лицензия:** MIT ([README](https://github.com/tobymao/sqlglot)). Очень активный (9.7k звёзд) ([README](https://github.com/tobymao/sqlglot)).

### 9.5. sqlparse
* Python-токенизатор/форматтер без валидации; диалект-агностик; CLI `sqlformat` (`--reindent`, `--keyword-case`, `--strip-comments`, `--indent-width`, `--in-place`) ([README](https://github.com/andialbrecht/sqlparse)).
* pre-commit-хук `sqlformat` ([README](https://github.com/andialbrecht/sqlparse)).
* **Лицензия:** BSD-3-Clause ([README](https://github.com/andialbrecht/sqlparse)). Правил линтинга/нейминга нет; форматирование грубое.

### 9.6. plpgsql_check (расширение PostgreSQL)
* Полноценный статический анализатор **plpgsql**: проверка полей объектов в встроенном SQL, типов параметров, неиспользуемых переменных/OUT, мёртвого кода, отсутствующего `RETURN`, скрытых кастов, SQL-инъекций в `EXECUTE` ([README](https://github.com/okbob/plpgsql_check)).
* Требует установки расширения в БД; поддержка PostgreSQL 14–20 ([README](https://github.com/okbob/plpgsql_check)). Есть активный и пассивный режимы, настройка уровней предупреждений, PRAGMA/comment-опции ([README](https://github.com/okbob/plpgsql_check)).
* **Релевантность:** plpgsql вне области стандарта, но это единственный зрелый инструмент для его статического анализа; его подхватывает Postgres Language Server ([PL/pgSQL Support](https://pg-language-server.com/latest/features/plpgsql/)).
* **Лицензия:** см. LICENSE репозитория (**[не проверено]** — тип лицензии в рамках обзора не подтверждён).

### 9.7. Линтеры миграций (обзорно, вне области стайлгайда)
* **MigrationPilot** — PostgreSQL migration linter, MIT, 112 правил, свой встроенный парсер Postgres, CLI/GitHub Action/MCP, есть SARIF ([README](https://github.com/mickelsamuel/migrationpilot)).
* **pg-migration-lint** — 54 правила, SARIF/SonarQube выходы, ориентирован на PG14+ ([README](https://github.com/robert-sjoblom/pg-migration-lint)).
* **Eugene**, **pgfence**, **Atlas** — упоминаются как аналоги в сравнительных таблицах этих проектов ([README pg-migration-lint](https://github.com/robert-sjoblom/pg-migration-lint), [README migrationpilot](https://github.com/mickelsamuel/migrationpilot)).
* Все — про безопасность миграций, не про форматирование/нейминг.

### 9.8. Ранние/экспериментальные
* **SQRust** — новый Rust-линтер («Ruff for SQL»), ANSI-only диалекты, заявляет 165–330 правил; ранняя стадия, один мейнтейнер ([crates.io/…/sqrust-core](https://crates.io/crates/sqrust-core)). Не кандидат для корпоративного внедрения сейчас.
* **PgTidy** — greenfield-проект (план, не релиз) PostgreSQL-линтера/форматтера на Go с упором на форматирование plpgsql ([plan.md](https://git.warky.dev/wdevs/PgTidy/raw/commit/cba0975a904c36ed690140b3b50009ae9ac6347f/docs/plan.md)). Следить, но не опираться.
* **apache/druid** — это **СУБД/аналитический движок**, а не линтер; к задаче не относится. (У sqlglot есть community-диалект `Druid` — [README](https://github.com/tobymao/sqlglot).)

---

## 10. Сравнительная таблица

| Инструмент | Язык / лицензия | Тип | PostgreSQL | SQLite | plpgsql | Авто-фикс | Правила/стиль | Настраиваемость | CI / редакторы | Активность |
|---|---|---|---|---|---|---|---|---|---|---|
| **SQLFluff** | Python / MIT | линтер + форматтер | да (`postgres`) | да (`sqlite`) | тела не линтуются (issue #3093) | да | 79 правил, 11 категорий | очень высокая (rules, layout, indentation, warnings, `noqa`) | GitHub/GitLab форматтеры, pre-commit, VS Code, Docker | очень высокая, 4.x, ежемесячно |
| **sqruff** | Rust / Apache-2.0 | линтер + форматтер (совместим с SQLFluff) | да | да | **[не проверено]** | да | набор кодов SQLFluff (AL..TQ) | высокая (`.sqruff`, layout, exclude_rules) | CLI, LSP, VS Code/Zed, GitLab CQ; GitHub Action **[не проверено]** | очень высокая, v0.44 (2026-10-30), < 1.0 |
| **sqlfmt** | Python / Apache-2.0 | форматтер (opinionated) | полиглот | полиглот | `create function` да, качество **[не проверено]** | да (переформат) | нет движка правил | только длина строки | pre-commit, VS Code, Docker, GH Actions | высокая, 0.30.0 (2026) |
| **pgFormatter** | Perl / PostgreSQL Licence | форматтер | да (ядро) | нет заявки | да (PL/pgSQL) | да (переформат) | нет движка правил | высокая для форматирования (spaces/tabs/case/wrap/config) | CLI/CGI, pre-commit, VS Code/vim | высокая, v5.10 (2026-05) |
| **Postgres Language Server** | Rust / MIT | LSP + CLI + форматтер + линтер | да (100% парсер) | нет | частично (тела сохраняются; опц. `plpgsql_check`) | нет (форматтер переформатирует) | группы Correctness/Destructive/Safety/Style/Typecheck | высокая (JSONC: lineWidth, indent, case, layout…) | LSP (VS Code и др.), GitHub Action, Postgres-сервис | высокая, ~0.27, форматтер preview |
| **squawk** | Rust / Apache-2.0 + MIT | линтер (безопасность миграций) | да | нет | нет | нет | много правил `ban-*`/`require-*`/`prefer-*` | средняя (`--exclude/--include`, `.squawk.toml`, `pg_version`) | CLI, GitHub Action/App, LSP, pre-commit, VS Code | высокая, v2.70 |
| **pglast** | Python / GPL-3.0+ | библиотека (AST) | да (PG10–18) | нет | через libpg_query | нет | нет | только API | нет готовых интеграций | высокая (в рамках libpg_query) |
| **libpg_query** | C / BSD-3 | библиотека (парсер Postgres + plpgsql) | да (18-latest) | нет | **да** (`pg_query_parse_plpgsql`) | нет | нет | API | обёртки для многих языков | высокая |
| **SQLCheck** | C++ / Apache-2.0 | линтер антипаттернов | да (заявлено) | да (заявлено) | нет | нет | 4 категории антипаттернов | низкая | CLI | **deprecated / неактивен** |
| **pgsanity** | Python / MIT | проверка синтаксиса | да | нет | нет | нет | нет | нет | CLI | неактивен |
| **sqlint (purcell)** | Ruby / MIT | проверка синтаксиса | да | нет | нет | нет | нет | нет | CLI, pre-commit, редакторы | старый |
| **sqlint (npm)** | JS / MIT | линтер + fix | диалект-агностик | да | нет | да | стилевые правила | средняя (JSON rules) | CLI, LSP | неактивен (~2 года) |
| **sqlglot** | Python / MIT | парсер/транспайлер/форматтер | да (official) | да (official) | нет | нет | нет (есть анализ AST) | API | библиотека | очень высокая |
| **sqlparse** | Python / BSD-3 | форматтер/токенизатор | диалект-агностик | да | нет | да (переформат) | нет | узкая (reindent, keyword case) | CLI, pre-commit | умеренная |
| **plpgsql_check** | C (расширение PG) | статический анализатор plpgsql | да (PG14–20) | нет | **да** | нет | богатый анализ plpgsql | высокая (warnings-флаги, PRAGMA) | SQL-функции в БД; интеграция в Postgres LSP | высокая |

---

## 11. Рекомендация

### 11.1. Основной инструмент — **SQLFluff**
Причины (все опираются на разделы выше):
1. **Покрывает обе целевые СУБД**: диалекты `postgres` и `sqlite` ([диалекты](https://docs.sqlfluff.com/en/stable/reference/dialects.html)).
2. **Совмещает линт и авто-формат** — можно и проверять стиль, и автоматически приводить код к нему ([README](https://github.com/sqlfluff/sqlfluff)).
3. **Максимальная настраиваемость под корпоративный стайлгайд**: правила/исключения, `warnings` (переходный режим), layout/indentation-конфиг, `noqa` ([Rule Configuration](https://docs.sqlfluff.com/en/latest/configuration/rule_configuration.html), [Layout](https://docs.sqlfluff.com/en/stable/configuration/layout.html)). Конфиг сам по себе становится документацией стандарта ([Configuration](https://docs.sqlfluff.com/en/stable/configuration.html)).
4. **Пригоден для кастомных и нейминг-правил** через pluggy-плагины и сторонний `sqlfluff-common-conventions` ([Custom Rules](https://docs.sqlfluff.com/en/stable/development/custom-rules.html), [common-conventions](https://pypi.org/project/sqlfluff-common-conventions/)).
5. **Готовые интеграции**: GitHub/GitLab CI, pre-commit, VS Code ([CI/CD](https://docs.sqlfluff.com/en/stable/usage/ci-cd.html), [pre-commit](https://docs.sqlfluff.com/en/stable/usage/pre-commit.html)).
6. **Слепое пятно по plpgsql совпадает с границей проекта**: тела plpgsql не линтуются (issue [#3093](https://github.com/sqlfluff/sqlfluff/issues/3093)), а по условию plpgsql вне области стандарта.
7. **Живой проект**: MIT, ежемесячные релизы, сообщество ([README](https://github.com/sqlfluff/sqlfluff)).

Основные риски и как их закрыть:
* «Unparsable» на нестандартном синтаксисе → держать `templater = raw`, при необходимости добавлять `-- noqa: PRS` в исключительных местах.
* Медленный Python → при росте репозитория рассмотреть Rust-парсер (`sqlfluff[rs]`).

### 11.2. Запасной инструмент — **sqruff**
* **Почему запасной:** совместим с SQLFluff по конфигу и набору правил, поддерживает `postgres`/`sqlite`, на порядок быстрее (Rust), есть LSP ([README](https://github.com/quarylabs/sqruff), [Dialects](https://playground.quary.dev/docs/reference/dialects/), [Rules](https://playground.quary.dev/docs/reference/rules/)).
* **Почему не основной:** версия **< 1.0** (0.44.x), риск ломающих изменений; полнота парсера/правил и интеграций недостаточно подтверждена; plpgsql-поведение **[не проверено]** ([releases](https://github.com/quarylabs/sqruff/releases)).
* **Стратегия:** держать один и тот же `.sqlfluff`/`.sqruff`-подобный конфиг и периодически прогонять оба линтера, чтобы иметь проверенный путь миграции при проблемах с производительностью SQLFluff.

### 11.3. Форматтер-компаньон
* Если нужен именно жёсткий единый вид **и SQL, и plpgsql** без правил — **pgFormatter** (PostgreSQL Licence, активные релизы) ([README](https://raw.githubusercontent.com/darold/pgFormatter/master/README)).
* Если нужен opinionated-формат SQL «без настроек» (Black-стиль) — **sqlfmt** (Apache-2.0) ([docs](https://sqlfmt.com/docs/intro)).
* Для PostgreSQL-only с сохранением тел функций как есть — форматтер **Postgres Language Server** (MIT) ([Formatting](https://pg-language-server.com/latest/features/formatting/)).

### 11.4. Дополнения вне области стайлгайда (по желанию)
* **Безопасность DDL/миграций (Postgres):** `squawk` или линтер Postgres Language Server ([Rules Overview](https://squawkhq.com/docs/rules), [Linter Rules](https://pg-language-server.com/latest/reference/rules/)).
* **Анализ plpgsql (вне области стандарта, но полезно):** `plpgsql_check` ([README](https://github.com/okbob/plpgsql_check)).
* **Кастомные проверки/трансформации:** `libpg_query` или `sqlglot` как фундамент ([README libpg_query](https://github.com/pganalyze/libpg_query), [README sqlglot](https://github.com/tobymao/sqlglot)).

---

## 12. Референсный конфиг: как он может быть устроен

### 12.1. Идея
Референсный конфиг (пример ниже — для SQLFluff) — это **исполняемое представление стандарта**: то, что нельзя выразить правилом, описывается словами в документе, а всё механически проверяемое выносится в конфиг. Рекомендуется два профиля:
* **baseline (блокирующий)** — то, что команда уже соблюдает и что валит CI;
* **aspirational (предупреждения)** — новые/спорные правила, включённые через `warnings`, чтобы «показать, но не блокировать» ([Rule Configuration](https://docs.sqlfluff.com/en/latest/configuration/rule_configuration.html)).

### 12.2. Каркас `.sqlfluff`

```ini
[sqlfluff]
# --- база ---
dialect = postgres            # основной; для SQLite — отдельный прогон с dialect = sqlite
templater = raw               # шаблонов нет; проще и быстрее (см. Configuration)
# max_line_length = 120       # длина строки — решение стандарта

# --- что блокируем ---
rules = ...                   # можно ссылаться на группы/имена: capitalisation, layout, ...
exclude_rules = ...           # осознанные исключения (см. 12.4)

# --- переходный режим ---
warnings = ...                # правила-кандидаты: показываем, но не валим сборку

[sqlfluff:indentation]
# indent_unit / tab_space_size / indented_joins / indented_using_on /
# implicit_indents / indented_ctes ...   (см. Layout)
```

Дополнительно конфиг можно раскладывать по каталогам (nesting) и точечно переопределять в файле директивами `-- sqlfluff:...` ([Configuration](https://docs.sqlfluff.com/en/stable/configuration.html)).

### 12.3. Какие классы правил стоит **включить**
Формулировки — по [Rules Reference](https://docs.sqlfluff.com/en/stable/reference/rules.html).

* **Capitalisation (CP01–CP05)** — регистр ключевых слов/функций/литералов/типов и регистр-стиль идентификаторов (`extended_capitalisation_policy = snake` для `CP02`) ([Capitalisation rules](https://docs.sqlfluff.com/en/stable/reference/rules/capitalisation.html)).
* **Layout (LT):** `LT02` (отступы), `LT01` (пробелы), `LT05` (длина строки), `LT04` (запятые), `LT12`/`LT13` (начало/конец файла), `LT07`/`LT08` (CTE-скобки/пустая строка), `LT11` (set-операторы) ([Layout rules](https://docs.sqlfluff.com/en/stable/reference/rules/layout.html)).
* **Convention (CV):** `CV01` (`!=` vs `<>`), `CV05` (`IS NULL`), `CV03` (trailing comma), `CV11` (стиль каста), `CV12` (условие join в `ON`), `CV08` (`LEFT JOIN` вместо `RIGHT JOIN`), `CV04` (`COUNT(*)`) ([Convention rules](https://docs.sqlfluff.com/en/stable/reference/rules/convention.html)).
* **Aliasing (AL):** `AL01`/`AL02` (явный `AS`), `AL04`/`AL08` (уникальность алиасов), `AL09` (self-alias), `AL10` (алиас для подзапроса в `FROM`) ([Aliasing rules](https://docs.sqlfluff.com/en/stable/reference/rules/aliasing.html)).
* **References (RF):** `RF01` (ссылка на отсутствующий объект), `RF04` (ключевые слова как идентификаторы), `RF05` (спецсимволы), `RF06` (лишние кавычки) ([References rules](https://docs.sqlfluff.com/en/stable/reference/rules/references.html)).
* **Structure (ST):** `ST03` (неиспользуемый CTE) и другие по вкусу ([Structure rules](https://docs.sqlfluff.com/en/stable/reference/rules/structure.html)).
* **Ambiguous (AM):** `AM02` (`UNION ALL/DISTINCT`), `AM09` (`LIMIT` без `ORDER BY`) ([Ambiguous rules](https://docs.sqlfluff.com/en/stable/reference/rules/ambiguous.html)).
* **Именование:** `CP02` (snake_case) + `RF04`/`RF05` как база; при потребности — сторонние CC04/CC05/CC06 (regex, allow/deny-списки, суффиксы) из `sqlfluff-common-conventions` ([PyPI](https://pypi.org/project/sqlfluff-common-conventions/)).

### 12.4. Что стоит **исключить** или держать в warnings
* **Спорные/очень строгие правила:**
  * `AL07 aliasing.forbid` — «запретить алиасы» (по умолчанию выключено; сам автор называет правило controversial) ([Aliasing rules](https://docs.sqlfluff.com/en/stable/reference/rules/aliasing.html));
  * `ST06 structure.column_order` и `AM04 ambiguous.column_count` — SQLFluff сам приводит их как примеры «controversial» в стартовой конфигурации ([Configuration](https://docs.sqlfluff.com/en/stable/configuration.html));
  * `CV13 convention.last_select_star` — dbt-специфичная конвенция, по умолчанию выключена ([Convention rules](https://docs.sqlfluff.com/en/stable/reference/rules/convention.html));
  * `RF02 references.qualification` / `RF03 references.consistent` — квалификация ссылок, вопрос вкуса ([References rules](https://docs.sqlfluff.com/en/stable/reference/rules/references.html));
  * `AL06 aliasing.length` — если в команде приняты короткие алиасы ([Aliasing rules](https://docs.sqlfluff.com/en/stable/reference/rules/aliasing.html));
  * `ST05 structure.subquery` (требование заменять подзапросы на CTE) — не всегда уместно для OLTP ([Structure rules](https://docs.sqlfluff.com/en/stable/reference/rules/structure.html)).
* **Правило-заглушка под проектное ограничение:** `CV09 convention.blocked_words` — используется для запрета конкретных устаревших таблиц/слов проекта ([Convention rules](https://docs.sqlfluff.com/en/stable/reference/rules/convention.html)); включать осознанно.
* **Postgres-специфичные `PG01`/`PG02`** (excessive locks, NOT VALID FK) — это про безопасность миграций, по умолчанию выключены; в стайлгайд не входят, но могут быть полезны отдельно ([Postgres rules](https://docs.sqlfluff.com/en/stable/reference/rules/postgres.html)).
* **Jinja `JJ01`** — только если реально есть Jinja-шаблоны ([Jinja rules](https://docs.sqlfluff.com/en/stable/reference/rules/jinja.html)).
* **Правила, специфичные для чужих диалектов** (TQ*, OR*) — не включать.

### 12.5. Схема развёртывания
* Прогон **двух конфигов**: `dialect = postgres` и `dialect = sqlite` (второй — с редуцированным набором правил, т.к. часть грамматики/правил специфична).
* CI: `sqlfluff lint --format gitlab --write-output gl-code-quality-report.json` ([CI/CD](https://docs.sqlfluff.com/en/stable/usage/ci-cd.html)); локально/хуком — `sqlfluff-fix` ([pre-commit](https://docs.sqlfluff.com/en/stable/usage/pre-commit.html)).
* Плагины с кастомными правилами ставить в CI/pip/pre-commit через `additional_dependencies` ([pre-commit](https://docs.sqlfluff.com/en/stable/usage/pre-commit.html), [Custom Rules](https://docs.sqlfluff.com/en/stable/development/custom-rules.html)).

---

## 13. Ограничения обзора и непроверенное

* **plpgsql у sqruff** — не подтверждено документацией; вероятное ограничение унаследовано от SQLFluff. **[не проверено]**
* **Интеграции sqruff** (GitHub Action, pre-commit) — не найдены в проверенных страницах. **[не проверено]** (GitLab CQ подтверждён в changelog v0.44.0).
* **Лицензия plpgsql_check** — тип не подтверждён по первоисточнику в рамках этого обзора. **[не проверено]**
* **Зрелость стороннего плагина** `sqlfluff-common-conventions` для SQLFluff 4.x — не подтверждена (релиз 2024-06). **[не проверено]**
* **Число правил/диалектов** меняется между релизами; значения приведены на дату обзора со ссылками.
* Реальные возможности парсеров PostgreSQL/SQLite у SQLFluff/sqruff на **нашем** коде не измерялись — это следующий шаг (пилот на корпусе хранимых объектов и миграций).
