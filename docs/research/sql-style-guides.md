# Публичные руководства по стилю SQL: покрытие и извлечённые правила

> Исследовательский документ. Цель — валидировать список аспектов из
> `STANDARD.md` и `docs/adr/0001-scope-aspects.md` и позаимствовать
> обоснованные правила, опираясь только на первоисточники (репозитории и
> страницы самих гайдов, официальную документацию проектов).
>
> Дата сбора: 2026-10-31. Версии источников — на дату сбора; ссылки ведут
> на актуальные «живые» страницы.

Помимо семи обязательных источников добавлены три «инженерных» гайда
(Kickstarter, Brooklyn Data Co., Mazur) и один контрастный гайд (Modern SQL
Style Guide) — они дают материал для раздела «где расходятся». Компании
BBVA, Airbnb, Kaggle и Mode проверены отдельно: публичных нормативных SQL-гайдов
у них нет (см. §6, «Отрицательные результаты»).

---

## 1. Сводная таблица «гайд × аспекты»

Условные обозначения: **●** — аспект покрыт содержательно; **◐** — покрыт
частично или косвенно; **○** — не покрыт.

| Гайд | Формат | Имена | Синтаксис | Дизайн БД | Произв. | Безопасн. | Коммент. | Орг. файлов | Нормативность | Плохо/хорошо |
|---|---|---|---|---|---|---|---|---|---|---|
| Simon Holywell (`sqlstyle.guide`) | ● | ● | ● | ● | ◐ | ◐ | ● | ○ | предписания «Do/Avoid/Always» | ● |
| dbt Labs («How we style our SQL») | ● | ● | ● | ○ | ◐ | ○ | ● | ● | «should / prefer / use» | ● |
| GitLab (handbook + dev docs) | ● | ● | ● | ◐ | ● | ◐ | ● | ◐ | нормативный, enforced by review/SQLFluff | ● |
| Mozilla (data-docs) | ● | ● | ● | ○ | ◐ | ○ | ◐ | ○ | «Always / Should» | ● |
| Google (google/styleguide + BigQuery docs) | ○ | ○ | ◐ | ○ | ○ | ○ | ◐ | ○ | описательный (не гайд) | ◐ |
| SQLFluff default ruleset | ● | ● | ● | ○ | ◐ | ○ | ○ | ◐ | машино-проверяемый | ● |
| PostgreSQL docs | ◐ | ○ | ◐ | ◐ | ○ | ◐ | ● | ○ | «convention often used» | ● |
| Mazur (`mattm/sql-style-guide`) | ● | ● | ● | ◐ | ◐ | ○ | ◐ | ◐ | «Good/Bad», «prefer» | ● |
| Kickstarter (gist) | ● | ● | ● | ○ | ◐ | ○ | ● | ◐ | «Always / Don't» | ● |
| Brooklyn Data Co. | ● | ● | ● | ◐ | ◐ | ○ | ● | ◐ | «Never / Always / prefer» | ● |
| Modern SQL Style Guide (mattmc3) | ● | ● | ● | ◐ | ○ | ○ | ● | ◐ | «Favor / Good / Bad» | ● |

Два вывода из таблицы сразу:

1. **Ни один публичный гайд не является полным корпоративным стандартом.**
   Ядро у всех — формат + имена + синтаксис. Дизайн БД осмысленно покрывает
   только Holywell (раздел Create syntax); производительность — только GitLab
   (dev docs); безопасность — фрагментарно у GitLab и Holywell. Это
   подтверждает решение из `docs/adr/0001-scope-aspects.md`: включать
   Форматирование и Нейминг полностью, Синтаксис — частично, а
   Дизайн/Производительность/Безопасность держать отдельно от стайлгайда.
2. **Все гайды — «мягкие» (should/prefer), а не RFC-нормативные (MUST/SHOULD).**
   Ни один не вводит уровней нормативности в стиле RFC 2119; уровень задаётся
   формулировкой (Always / Never / prefer / Good–Bad). Единственный реально
   нормативный контур — `SQLFluff` (машинная проверка).

---

## 2. Обзор источников

### 2.1 Simon Holywell — SQL Style Guide

URL: <https://www.sqlstyle.guide/> · Разделы: Overview, General, Naming
conventions, Query syntax, Create syntax.

- **Форма документа.** Предписания сформулированы императивно: секции
  `Do` / `Avoid`, слова `Always`, `Never`, `must`. Уровней нормативности нет,
  но де-факто это нормативные правила («Always use uppercase…»,
  «Avoid camelCase»).
- **Покрытие.** Единственный гайд из обязательного списка, который заходит в
  дизайн БД: `Choosing data types`, `Specifying default values`,
  `Constraints and keys`, `Designs to avoid` (§Create syntax).
- **Примеры.** Есть блоки SQL, но без явной разметки «плохо/хорошо»;
  «плохие» варианты перечислены словами (`Avoid …`).
- **Ключевые правила.**
  - Регистр: верхний для ключевых слов (`Always use uppercase for the reserved
    keywords like SELECT and WHERE`, §Query syntax → Reserved words).
  - Отступы/выравнивание: «river» — ключевые слова выравниваются вправо, значения
    влево, пробелы выравнивают код по одной колонке (§White space → Spaces,
    §Indentation).
  - Переносы: новая строка перед `AND`/`OR`, после `;`, после запятой при
    группировке колонок (§White space → Line spacing).
  - Запятые: trailing (`a.title, a.release_date,`) — из примеров §White space.
  - Имена: snake_case, lowercase, ≤30 байт, начинается с буквы, не заканчивается
    `_`, без двойных подчёркиваний (§Naming conventions → General).
  - Таблицы: коллективное имя, реже множественное (`staff`, `employees`);
    без префиксов `tbl_`; не совпадает с именем колонки (§Tables).
  - Колонки: всегда единственное число; избегать `id`; суффиксы `_id`,
    `_status`, `_total`, `_num`, `_name`, `_seq`, `_date`, `_tally`, `_size`,
    `_addr` (§Columns, §Uniform suffixes).
  - Алиасы: короткие «корреляции» из первых букв слов объекта, всегда с `AS`
    (§Aliasing or correlations).
  - Кавычки идентификаторов: избегать; если нужны — двойные кавычки SQL-92
    (§General → Avoid).
  - JOIN: явно указывать тип, отступ вправо от «river» (§Indentation → Joins).
  - `< >` vs `!=`: правила нет.

### 2.2 dbt Labs — «How we style our SQL»

URL: <https://docs.getdbt.com/best-practices/how-we-style/2-how-we-style-our-sql>
(см. также `.../1-how-we-style-our-dbt-models`, `.../0-how-we-style-our-dbt-projects`).

- **Форма.** Рекомендательный гайд-пример («This guide is just a suggestion to
  get you started», intro). Правила — иконки + «should/prefer/use/avoid».
  Подчёркивается: важнее консистентность, чем конкретный выбор.
- **Покрытие.** Формат, имена, синтаксис (joins, CTE, group by), организация
  файлов (слои моделей, «import» CTE, конфигурация). Дизайна БД и безопасности
  нет; производительность — косвенно («aggregations … on the smallest data set
  possible before joining», §Fields).
- **Примеры.** Да, развёрнутый пример SQL в конце страницы.
- **Ключевые правила.**
  - Регистр: **нижний** для keywords, functions, field names (`Field names,
    keywords, and function names should all be lowercase`, §Basics).
  - Отступ: 4 пробела; длина строки ≤80; trailing commas (§Basics).
  - Алиасы: всегда явный `as` (§Basics); не использовать короткие алиасы,
    особенно аббревиатуры (`Avoid table aliases … especially initialisms`,
    §Joins).
  - JOIN: явный тип (`write inner join instead of join`); префикс таблицы, если
    таблиц две и более; предпочитать `left` (двигаться слева направо) (§Joins).
  - CTE: `{{ ref('...') }}` только в import-CTE вверху; одна логическая операция
    на CTE; имена по таблице/функции; дубли выносить в модели (§Import CTEs,
    §Functional CTEs).
  - GROUP BY: по позиции (`group by 1, 2`) (§Fields).
  - `union all` предпочтительнее `union` (§Joins).
  - Имена: `snake_case` для schema/table/column; объекты во множественном числе;
    PK — `<object>_id` (§Model File Naming, в `.../1-...`).
  - `< >` vs `!=`: правила нет. Кавычки идентификаторов: не рассматриваются.

### 2.3 GitLab — SQL guidelines + SQL Style Guide

Два разных документа:
- **Handbook, SQL Style Guide:** <https://handbook.gitlab.com/handbook/enterprise-data/platform/sql-style-guide>
  (для dbt/Snowflake; enforced SQLFluff + review).
- **Dev docs, SQL Query Guidelines:** <https://docs.gitlab.com/development/sql/>
  (производительность в PostgreSQL/Rails).

- **Форма.** Нормативный: «This guide establishes our standards… enforced by the
  SQLFluff linter and by code review». Примеры в стиле `-- Preferred` /
  `-- Not Preferred`.
- **Покрытие.** Формат, имена, синтаксис, комментарии; производительность —
  отдельный документ (EXISTS vs IN, UNION, pluck, query plan flip, CTE);
  дизайн — частично (data types); безопасность — косвенно (parameterized
  queries/escaping в dev docs).
- **Ключевые правила (handbook, §Best Practices / §Naming / §Reference / §CTEs).**
  - Только пробелы, без табов; перенос строк 80–100.
  - Регистр: SQLFluff настроен на UPPER для keywords, data types, functions
    (§Changes from the default configuration).
  - `AS` при алиасинге; префиксовать неоднозначные имена (`id` → `account_id`);
    snake_case; boolean — `has_`/`is_`/`does_`; timestamps — `_at` (UTC),
    dates — `_date`.
  - Предпочитать **`!=`** вместо `<>` («`!=` is more common in other programming
    languages and reads like "not equal"»).
  - Не использовать `USING` в join (в Snowflake даёт неверные результаты);
    явный join; квалифицировать каждую колонку при join.
  - CTE вместо подзапросов; CTE вверху; одна логическая операция.
  - Агрегаты — после неагрегированных колонок; `GROUP BY` по имени или позиции
    (но не `GROUP BY ALL`).
  - Двойные кавычки — только при необходимости (спецсимволы/регистр).
  - Комментарии: `--` для однострочных, `/* */` для многострочных; не оставлять
    TODO, заводить issue.
- **Ключевые правила (dev docs).** `WHERE EXISTS` вместо `WHERE IN`; осознанно
  использовать `UNION`; CTE — «последнее средство» из-за query plan flip;
  `ORDER BY id` обычно предпочтительнее `ORDER BY created_at`.

### 2.4 Mozilla — SQL Style Guide

URL: <https://docs.telemetry.mozilla.org/concepts/sql_style.html>.

- **Форма.** Открывается цитатой PEP8 о консистентности; далее «Always use…»,
  «Do not use…». Влияние `sqlstyle.guide` признано в §About this Document.
  Разметка примеров явная: **Good** / **Bad**.
- **Покрытие.** Формат и синтаксис; имён — базово; дизайна/безопасности/
  производительности — нет.
- **Ключевые правила.**
  - Ключевые слова — **UPPER**, идентификаторы — lower с подчёркиваниями, без
    camelCase (§Reserved Words, §Variable Names).
  - Явность: всегда `JOIN`-тип, всегда `AS`; запрещены неявные группировки
    (§Be Explicit).
  - **Left align root keywords** — прямая полемика с «river» из SQL Style Guide
    («This is counter to the common "rivers" pattern», §Left Align Root
    Keywords).
  - Ключевое слово — на своей строке; один аргумент допустимо оставить на строке
    (§Code Blocks).
  - `ON`/`USING` — с новой строки, отступ на уровень больше join (§Join
    Conditions).
  - Скобки: открывающая завершает строку, закрывающая — под первым символом
    конструкции, содержимое +1 уровень (§Parentheses).
  - Булевы операторы `AND`/`OR` — в начале строки (§Boolean at the Beginning of
    Line).
  - Запятые — **trailing**, в конце строки (§Comma at the End of the Line).
  - Вложенные запросы запрещены, использовать CTE (§Nested Queries).
  - `< >` vs `!=`, кавычки идентификаторов: правил нет.

### 2.5 Google — google/styleguide и GoogleSQL (BigQuery)

- **google/styleguide**: <https://github.com/google/styleguide> — SQL-гайда
  **нет**. В README перечислены C++, Java, Python, Go, JS/TS, Shell, R, Rust и
  др.; SQL отсутствует.
- **GoogleSQL / BigQuery (справочник, не гайд):**
  <https://cloud.google.com/bigquery/docs/reference/standard-sql/lexical> —
  «Keywords are case-insensitive»; примеры в документации пишут ключевые слова
  заглавными «for illustration purposes».
- Вывод: публичного нормативного Google-гайда по стилю SQL не существует.
  Google-специфика сводится к «keywords case-insensitive, docs предпочитают
  верхний регистр». Использовать как первоисточник по языку, но не по стилю.

### 2.6 SQLFluff — правила по умолчанию (default ruleset)

Индекс: <https://docs.sqlfluff.com/en/stable/reference/rules.html> ·
Категории: aliasing, ambiguous, capitalisation, convention, layout, references,
structure, postgres. Дефолтный конфиг:
<https://github.com/sqlfluff/sqlfluff/blob/main/src/sqlfluff/core/default_config.cfg>.

- **Форма.** Машино-проверяемый набор правил; каждое правило имеет
  Anti-pattern / Best practice. `rules = all` по умолчанию; часть правил
  отключена (`force_enable = False`).
- **Покрытие аспектов и ключевые дефолты.**
  - **Capitalisation (CP01–CP05):** keywords, unquoted identifiers, functions,
    literals, types. Политика по умолчанию — `consistent` (не upper/lower!).
  - **Layout (LT01–LT15):** spacing; indent (`indent_unit = space`,
    `tab_space_size = 4`); binary/comparison операторы — `line_position =
    leading`; запятые — `line_position = trailing`; длина строки 80
    (`max_line_length = 80`); функция без пробела перед `(`; закрывающая скобка
    CTE — на новой строке; select targets — по строке на цель; `UNION` — на
    отдельной строке.
  - **Convention (CV01–CV13):** `<>`/`!=` — `preferred_not_equal_style =
    consistent`; `COALESCE` вместо `IFNULL`/`NVL`; trailing comma в SELECT —
    `forbid`; `COUNT(*)`; `IS NULL` вместо `= NULL`; `;`; `LEFT JOIN` вместо
    `RIGHT JOIN`; `JOIN ... ON` вместо `WHERE`-join; единый стиль каста;
    `select * from final` (CV13) — **отключено по умолчанию**.
  - **Aliasing (AL01–AL10):** `AS` — explicit по умолчанию (`aliasing.table`,
    `aliasing.column`); алиас выражения обязателен; уникальность алиасов;
    неиспользуемые алиасы; длина алиаса; `aliasing.forbid` (полный запрет
    алиасов) — **отключено по умолчанию**.
  - **Ambiguous (AM01–AM09):** `JOIN` → `INNER JOIN`
    (`fully_qualify_join_types = inner`); `UNION` → `UNION DISTINCT/ALL`;
    направления ORDER BY — все или никто; неизвестное число колонок (`SELECT *`);
    неявный cross join; `LIMIT`/`OFFSET` без `ORDER BY`.
  - **Structure (ST01–ST12):** без `ELSE NULL`; упрощение `CASE`; неиспользуемые
    CTE; подзапрос в JOIN → CTE (`forbid_subquery_in = join`, в FROM разрешено);
    порядок колонок (упрощение → расчёты); `DISTINCT` без скобок; порядок таблиц
    в условии join (`earlier`).
  - **References (RF01–RF07):** ссылки только на объекты из FROM; квалификация при
    нескольких источниках; консистентность ссылок;
    запрет ключевых слов как идентификаторов; запрет спецсимволов; кавычки только
    по необходимости (`prefer_quoted_identifiers = False`);
    `references.window_alias` — отключено по умолчанию.
  - **Postgres (PG01–PG02):** `CREATE INDEX CONCURRENTLY`,
    неблокирующие DDL (`postgres.excessive_locks`), FK `NOT VALID`
    (`postgres.not_valid_foreign_key`) — оба **отключены по умолчанию**.
- **Вывод.** SQLFluff по умолчанию накрывает почти весь Формат/Имена/Синтаксис,
  но сознательно оставляет «спорные» правила выключенными
  (`aliasing.forbid`, `last_select_star`, `references.window_alias`,
  postgres-локи). Это удобный индикатор того, что считать консенсусом, а что —
  вопросом решения.

### 2.7 PostgreSQL — соглашения в официальной документации

- **Lexical Structure** (§4.1.1 Identifiers and Key Words):
  <https://www.postgresql.org/docs/current/sql-syntax-lexical.html> —
  «Key words and unquoted identifiers are case-insensitive… A convention often
  used is to write key words in upper case and names in lower case, e.g.
  `UPDATE my_table SET a = 5;`».
  Это **единственная** явная рекомендация по стилю в PG-документации — и она
  описывается как *convention*, а не как правило.
- **Комментарии:** `--` и блочные `/* */` (вложенные) — §4.1.3 (там же).
- **SELECT/синтаксис:** <https://www.postgresql.org/docs/current/sql-select.html> —
  неявное соединение через запятую описано как допустимое (Cartesian product +
  условия в `WHERE`), но не рекомендуется явно.
- **Следование собственному соглашению о регистре:** коммит
  «Doc: more uppercase keywords in SQLs» (10.11.2025),
  <https://www.postgresql.org/message-id/E1vIJK8-005rNZ-2a%40gemulon.postgresql.org> —
  проект приводит SQL-примеры в документации к верхнему регистру ключевых слов.
- Дизайн БД PG-доки покрывают описательно (типы, CAST, даты). Стиль не
  регламентируется.

### 2.8 Инженерные гайды (Mazur, Kickstarter, Brooklyn, Modern)

- **Mazur (`mattm/sql-style-guide`)**: <https://github.com/mattm/sql-style-guide>.
  Lowercase-регистр, по колонке на строку, `!=` вместо `<>`, trailing-запятые,
  plural snake_case таблицы, `snake_case` колонки, префиксы boolean `is_/has_/does_`,
  `_date`/`_at`, квалификация колонок при join, `INNER JOIN` явно, CTE вместо
  подзапросов, `SELECT *` из последнего CTE, явные алиасы агрегатов, отказ от
  коротких алиасов (кроме self-join/длинных имён).
- **Kickstarter (gist)**: <https://gist.github.com/fredbenenson/7bb92718e19138c20591>.
  **2 пробела** на отступ, **UPPERCASE** ключевые слова, underscore-имена,
  `AS` всегда, CTE вместо подзапросов, явный `INNER JOIN`, `AND` в начале строки.
- **Brooklyn Data Co.**: <https://github.com/brooklyn-data/co/blob/main/sql_style_guide.md>.
  Lowercase, **leading commas**, `<< >>` не используется — только `!=`;
  `coalesce` вместо `ifnull/nvl`; `is null`; `case` вместо `iff`; `||` вместо
  `concat`; `where` вместо `having`; `union all`; не использовать `order by`
  без необходимости; длина строки ≤120; 4 пробела; PK — `id`; `USING` запрещён;
  left-align, операторы в начале строки.
- **Modern SQL Style Guide (mattmc3)**: <https://gist.github.com/mattmc3/38a85e6a4ca1093816c08d4815fbebfb>.
  **River**, **leading commas**, **lowercase**; явно аргументирует lowercase против
  «SHOUTCASE»; таблицы plural; `id` не рекомендует; `join` без `inner`/`outer`
  (считает лишним); `join`-условия с новой строки; `;` на отдельной строке;
  `ASC` не пишет.

### 2.9 Отрицательные результаты (проверено, публичного SQL-гайда нет)

- **Mode Analytics** — есть только авто-форматтер SQL
  (<https://mode.com/blog/new-sql-formatting-capability>); нормативного гайда нет.
  Внешний обзор приписывает Mode «leading commas» как сложившуюся практику —
  это вторичный источник (<https://www.basedash.com/blog/sql-style-guide-conventions-that-keep-team-queries-readable>).
- **Kaggle** — публикует курсы (`https://www.kaggle.com/learn/intro-to-sql`), а не
  стайлгайд. Ранее существовавшие материалы (`Rachael Tatman`, Scavenger Hunt)
  носили обучающий характер и не поддерживаются как нормативный документ.
- **Airbnb** — известен JS-гайдом (<https://github.com/airbnb/javascript>),
  публичного SQL-гайда нет.
- **BBVA** — организация на GitHub (<https://github.com/BBVA>) без SQL-гайда;
  публичных нормативных SQL-соглашений не найдено.

---

## 3. Где источники согласны (консенсус)

Ниже — только те правила, которые независимо подтверждены несколькими
первоисточниками (в скобках — конкретные места). Их можно брать в стандарт с
высокой уверенностью.

### 3.1 Процессный принцип (главный консенсус)

| Правило | Источники |
|---|---|
| Консистентность важнее конкретного выбора; «pick a style and stick to it» | Holywell §Overview; Mozilla §Consistency (цитата PEP8); dbt §0-...; GitLab §General Guidance; SQLFluff (единый конфиг) |

### 3.2 Именование

| Правило | Источники |
|---|---|
| Идентификаторы — `snake_case`, нижний регистр; без `camelCase` | Holywell §Naming → General/Columns; Mozilla §Variable Names (п.2); dbt §1-... («Schema, table, and column names should be in snake_case»); GitLab §Naming; Mazur §Column names; Brooklyn §General; SQLFluff CP02 |
| Начинается с буквы; только буквы/цифры/подчёркивания | Holywell §Naming → General; Mozilla §Variable Names (п.4–5); SQLFluff RF05 (no special chars) |
| Не использовать зарезервированные слова как идентификаторы | Holywell §Naming → General; SQLFluff RF04; Brooklyn §General |
| Префиксы `tbl_`/`sp_`/венгерская нотация — запрещены | Holywell §Avoid/§Tables/§Stored procedures; Mazur §Tables; Modern §Tables |
| Boolean — префиксы `is_`/`has_`/`does_` | GitLab §Naming; Mazur §Column name conventions; Brooklyn §Boolean column names |
| Временные колонки: `_date` для даты, `_at` для timestamp (UTC) | GitLab §Naming; Mazur §Column name conventions; Brooklyn §Date/time column names |
| Явная квалификация колонок таблицей при нескольких источниках | Mozilla §Be Explicit; dbt §Joins; GitLab §Reference Conventions; Brooklyn §Joins; SQLFluff RF02 |

### 3.3 Синтаксис

| Правило | Источники |
|---|---|
| Всегда явный `AS` при алиасинге колонки/таблицы | Holywell §Aliasing; Mozilla §Aliasing; dbt §Basics; GitLab §Best Practices; Mazur §Use as; Brooklyn §Syntax; SQLFluff AL01/AL02 (default explicit) |
| Всегда явный тип JOIN (`INNER JOIN`, не `JOIN`) | Mozilla §Joins; dbt §Joins; GitLab §Best Practices; Mazur §Include inner; Brooklyn §Joins; Kickstarter §JOIN; SQLFluff AM05 (default `inner`) |
| Предпочитать CTE вложенным подзапросам | Mozilla §Nested Queries; dbt §Functional CTEs; GitLab §CTEs; Mazur §Use CTEs; Brooklyn §CTEs; Kickstarter §CTEs; SQLFluff ST05 |
| Сравнение с NULL только через `IS` / `IS NOT` | SQLFluff CV05; следствие семантики SQL (PostgreSQL, SELECT docs) |
| Алиасы выражений/агрегатов обязательны | Holywell §Aliasing; Mozilla §Aliasing; Mazur §Always rename aggregates; Brooklyn §Syntax; SQLFluff AL03 |
| Ключевые слова языка — не имена алиасов | Mozilla §Variable Names; SQLFluff RF04; Brooklyn §General |
| Одна «вещь» на строку в многоэлементных конструкциях (select-цели и пр.) | Mozilla §Code Blocks; dbt §Basics/примеры; Brooklyn §Formatting; SQLFluff LT09 (select targets) |

### 3.4 Форматирование (пробелы и комментарии)

| Правило | Источники |
|---|---|
| Без табов; только пробелы | GitLab §Best Practices; Mazur §Whitespace; Brooklyn §General; SQLFluff `indent_unit = space`; Kickstarter §General (пробелы) |
| `--` для однострочных, `/* */` для многострочных комментариев | Holywell §Do/§Comments; GitLab §Commenting; Brooklyn §Syntax; PostgreSQL §4.1.3 Lexical Structure |
| Комментарий объясняет «почему», а не «что» | Brooklyn §General; Mazur §General guidance; Modern §General; GitLab §Commenting |
| Один перенос/доп. строка для разделения логических секций запроса | Holywell §Line spacing; SQLFluff LT15; Mozilla §Code Blocks |
| Убрать trailing whitespace, финальный перевод строки | Mazur §Whitespace; Modern §Indentation; SQLFluff LT01/LT12 |

---

## 4. Где источники расходятся (спорные вопросы)

Здесь собраны вопросы, по которым гайды прямо противоречат друг другу. Их
**нельзя** взять «по консенсусу» — нужно решение и фиксация в стандарте.

| # | Вопрос | Позиция A | Позиция B | Источники |
|---|---|---|---|---|
| 1 | Регистр ключевых слов | UPPER | lower | A: Holywell §Reserved words; Mozilla §Reserved Words; Kickstarter §General; GitLab §SQLFluff config (UPPER); PostgreSQL §4.1.1 («convention … upper case»). B: dbt §Basics; Mazur §Use lowercase; Brooklyn §Syntax; Modern §Casing. SQLFluff default — `consistent` (любой, но единый) |
| 2 | Запятые | trailing (в конце строки) | leading (в начале строки) | A: Mozilla §Comma at the End; dbt §Basics; GitLab (примеры); SQLFluff LT04 (`trailing`). B: Brooklyn §Leading commas; Modern §select clause |
| 3 | Выравнивание | «river» (правое выравнивание keywords) | left-align (без реки) | A: Holywell §Spaces/§Indentation; Modern §River formatting. B: Mozilla §Left Align Root Keywords (прямая полемика); dbt/примеры; Brooklyn §Left align everything |
| 4 | Ширина отступа | 4 пробела | 2 пробела | A: dbt §Basics; Brooklyn §Indents; SQLFluff `tab_space_size = 4`; Mazur §Whitespace; Modern §Whitespace. B: Kickstarter §General; GitLab §SQLFluff config (`tab size to be 2 spaces`); Mozilla (примеры) |
| 5 | Длина строки | 80 / 100 / 120 | — | dbt §Basics: 80; GitLab §Best Practices: 80–100; Brooklyn §General: 120; SQLFluff default: 80 |
| 6 | Оператор «не равно» | `!=` | `<>` / «consistent» | A: GitLab §Best Practices; Mazur §Use != over <>; Brooklyn §Syntax. B(ANSI): стандарт `<>`, PostgreSQL допускает оба; SQLFluff CV01 default `consistent` |
| 7 | Имена таблиц | множественное число | коллективное/естественное существительное | A(plural): Mazur §Table names; dbt §1-... («All objects should be plural»); Modern §Tables («Naming a table as a plural makes the table easier to speak about»). B(collective): Holywell §Tables («use the more natural collective term … `staff` instead of `employees`»). Единственное число как норму никто из обязательных гайдов не вводит |
| 8 | Алиасы таблиц | избегать (полное имя/неаббревиатура) | короткие «корреляции» | A: dbt §Joins («Avoid table aliases … especially initialisms»); Brooklyn §Naming; SQLFluff AL06; Modern (короткие «ок» для 1–3 таблиц). B: Holywell §Aliasing (первые буквы слов); Mozilla §Joins (примеры `c`, `main_v4`); SQLFluff `aliasing.forbid` отключён по умолчанию |
| 9 | Имя PK | `id` | избегать `id` | A: Brooklyn §Naming («Name single-column primary keys id»). B: Holywell §Columns («avoid … id»); Modern §Columns; SQLFluff не регламентирует |
| 10 | `USING` в JOIN | запрещён / не использовать | допустим/использовать | A: Brooklyn §Joins; GitLab §Best Practices (Snowflake-баг); SQLFluff ST07 (предпочитать `ON`). B: PostgreSQL docs (стандарт `USING`); SQLFluff ST07 отключаем для ClickHouse |
| 11 | `SELECT *` | избегать/запрещать | допустим в простых случаях и в финальном CTE | A: SQLFluff AM04 (unknown column count). B: Mazur §select *; dbt §Functional CTEs (финальный `select * from final`); SQLFluff CV13 (по умолчанию **отключён**) |
| 12 | `ASC` в ORDER BY | писать явно всем | не писать `ASC` (дефолт) | A: SQLFluff AM03 (все направления явно); Kickstarter §SELECT (order explicit). B: Modern §order by («superfluous asc»). GitLab: `ASC` не требуется |
| 13 | Boolean в предикате | явно `= true`/`= false` | достаточно `WHERE flag` | A: Mazur §Be explicit in boolean conditions. B: неявное булево — общепринято (никто из обязательных гайдов не требует `= true`) |
| 14 | GROUP BY | по имени | по позиции | A: Holywell/ANSI-стиль (имя); GitLab разрешает оба. B: dbt §Fields (`group by 1, 2` предпочтительно); Mozilla §Grouping Columns (допускает позиции); SQLFluff AM06 — единый стиль (`consistent`) |
| 15 | Финальная `;` | обязательна | не обязательна | A: SQLFluff CV06 существует, но `require_final_semicolon = False` по умолчанию. B: dbt (обёртка запросов ломается). По факту — не консенсус |
| 16 | Пробел внутри `IN (...)`: `IN (1, 2)` vs `IN ( 1, 2 )` | без пробелов сразу после скобки | — | Все примеры — без лишних пробелов; но SQLFluff LT01 формулирует как «пробел после `USING`» (чтобы не спутать с функцией), а Mazur §Avoid spaces inside parenthesis прямо запрещает |
| 17 | Требование явного `LEFT`-стиля / запрет `RIGHT JOIN` | запрещать `RIGHT JOIN` | не регламентировать | A: SQLFluff CV08; dbt §Joins (двигаться слева направо); Modern §from clause. B: остальные молчат |
| 18 | Префиксы слоёв | `stg_`/`int_`/`fct_` | `dim_`/`fact_`/`Xref` | A: dbt §1-... / template. B: Modern §Tables; Kickstarter/Mazur — практики конкретных стеков |

Дополнительно: **ключевые слова vs функции** (поднимать ли upper-регистр для
функций) — Holywell предлагает UPPER для reserved words, но не для функций;
Medium-совет («use uppercase for functions … debatable») — вторичный источник,
не берём. Этот вопрос остаётся открытым.

---

## 5. Что это значит для нашего стандарта

### 5.1 Что можно взять как консенсусное (низкий риск)

Из §3 — без оговорок:

1. **Идентификаторы:** `snake_case`, lower, без camelCase, без префиксов
   венгерской нотации, не зарезервированные слова.
2. **Алиасы:** всегда явный `AS`.
3. **JOIN:** всегда явный тип (`INNER JOIN` и т. д.).
4. **CTE вместо вложенных подзапросов.**
5. **Квалификация колонок** при нескольких источниках.
6. **`IS NULL` / `IS NOT NULL`** вместо сравнений с `NULL`.
7. **Одна цель на строку** в многоэлементных конструкциях.
8. **Пробелы, не табы**; отсутствие trailing whitespace; финальный перевод строки.
9. **Синтаксис комментариев** (`--`, `/* */`) и смысл комментария («почему»).
10. **Консистентность важнее выбора** — оформить как мета-принцип.

Эти пункты совпадают с принципами из `STANDARD.md` (§2):
минималистичность (один вариант на аспект), эксплицитность (явный `AS`,
явный JOIN), естественность (4 пробела как типовая настройка).

### 5.2 Что требует отдельного решения

Каждый пункт §4 нужно решить явно и однозначно — иначе нарушается наш принцип
«Однозначность».

1. **Регистр ключевых слов** (UPPER vs lower). Аргументы за UPPER: PostgreSQL
   docs convention, Holywell, Mozilla, Kickstarter, GitLab-конфиг. За lower:
   dbt, Mazur, Brooklyn, Modern (аргумент: не надо держать Shift, современные
   редакторы подсвечивают keywords). SQLFluff по умолчанию не выбирает, а
   требует лишь единообразия. *Рекомендация к обсуждению:* выбрать один и
   закрепить через `capitalisation_policy` (upper|lower), не оставлять
   `consistent`, чтобы правило было однозначным.
2. **Запятые: trailing vs leading.** SQLFluff по умолчанию trailing; Mozilla/dbt
   trailing; Brooklyn/Modern leading. *Рекомендация:* trailing — совпадает с
   дефолтом SQLFluff и большинством «аналитических» гайдов, но зафиксировать
   явно (`line_position`).
3. **Выравнивание: river vs left-align.** River поддерживают только Holywell и
   Modern (T-SQL), при этом Mozilla прямо возражает. Left-align доминирует и
   проще для редактирования. Согласуется с принципами Минималистичность и
   Оправданность.
4. **Ширина отступа.** 4 против 2. `STANDARD.md` (§2, Естественность) уже
   обосновывает 4 как «типовую настройку» (Naturalness). Совпадает с dbt,
   SQLFluff, Brooklyn, Mazur.
5. **Длина строки.** Задать одно число (SQLFluff по умолчанию 80; GitLab
   80–100; Brooklyn 120). Формализуемо через `max_line_length`.
6. **`!=` vs `<>`.** ANSI-стандарт — `<>`; GitLab/Mazur/Brooklyn выбирают `!=`
   по читаемости; PostgreSQL допускает оба; SQLFluff — «consistent». Нужно
   решить и (при желании) закрепить `preferred_not_equal_style`.
7. **Имена таблиц:** множественное vs коллективное vs единственное.
8. **Политика алиасов таблиц:** запрещать аббревиатуры (dbt) или допускать
   короткие корреляции (Holywell). Прямо противоположные правила.
9. **`id` как имя PK.**
10. **`USING`** в JOIN.
11. **`SELECT *`** и правило «финальный `select * from final`».
12. **`ASC` явно / неявно.**
13. **Boolean в предикате:** явно или нет.
14. **GROUP BY по имени или позиции** (и не смешивать).
15. **Финальная `;`.**

### 5.3 Валидация нашего списка аспектов

- **Форматирование** и **Именование** — подтверждено всеми источниками как ядро
  → включать полностью. ✅
- **Синтаксис** (явный JOIN, `<>`/`!=`, CTE vs подзапрос, `USING`, `SELECT *`,
  QUALIFY/GROUP BY) — покрыт, но частью спорный → включать частично. ✅
- **Дизайн БД** — осмысленно покрыт только Holywell (CREATE-раздел: типы,
  ключи, дефолты, «designs to avoid»); у остальных почти нет. Это подтверждает
  решение вынести в отдельный документ/архитектуру.
- **Производительность** — по сути только GitLab (dev docs) и точечно dbt/Holywell;
  не стайлгайд → отдельно.
- **Безопасность** — практически отсутствует у всех (кроме упоминаний
  parameterized/escaping у GitLab и косвенного «избегайте quoted identifiers» у
  Holywell). Это заметная «дыра» публичных гайдов; наш стандарт может либо
  осознанно не лезть сюда, либо закрыть разрыв → отдельно.
- **Комментарии** — пересекает формат и синтаксис; у большинства есть явный
  раздел → включить в стандарт.
- **Организация файлов** — есть у dbt/GitLab, специфична для dbt/BI →
  опционально, как приложение.

### 5.4 Как усилиться по сравнению с публичными гайдами

- Публичные гайды — «мягкие». Мы можем ввести **уровни нормативности**
  (напр., MUST / SHOULD / MAY) и однозначные формулировки — прямой ответ на
  принцип «Однозначность» и на пробел в источниках.
- Все «мягкие» гайды рискуют остаться неисполненными (см. HN-обсуждения
  sqlstyle.guide о том, что вручную правила не соблюдаются). Практический
  контур — **линтер**. Наши правила стоит формулировать так, чтобы каждое
  мапилось на правило SQLFluff (CP/LT/CV/AL/AM/ST/RF) — тогда стандарт
  становится проверяемым. Это также объясняет, почему SQLFluff держит спорные
  правила выключенными: их нужно осознанно включать/настраивать.
- Наш scope (Формат + Имена + часть Синтаксиса) совпадает с реальной практикой
  индустрии и не раздувается до «архитектурного» документа.

---

## 6. Реестр источников

Первоисточники (гайды и документация):

1. Simon Holywell, SQL Style Guide — <https://www.sqlstyle.guide/>
   (платформа: <https://github.com/treffynnon/sqlstyle.guide>).
2. dbt Labs — How we style our SQL, dbt models, dbt projects —
   <https://docs.getdbt.com/best-practices/how-we-style/2-how-we-style-our-sql>,
   <https://docs.getdbt.com/best-practices/how-we-style/1-how-we-style-our-dbt-models>,
   <https://docs.getdbt.com/best-practices/how-we-style/0-how-we-style-our-dbt-projects>.
3. GitLab — SQL Style Guide (handbook) —
   <https://handbook.gitlab.com/handbook/enterprise-data/platform/sql-style-guide>;
   GitLab — SQL Query Guidelines (dev docs) —
   <https://docs.gitlab.com/development/sql/>.
4. Mozilla — SQL Style Guide —
   <https://docs.telemetry.mozilla.org/concepts/sql_style.html>.
5. Google — Style Guides (SQL отсутствует) —
   <https://github.com/google/styleguide>;
   GoogleSQL / BigQuery — Lexical structure —
   <https://cloud.google.com/bigquery/docs/reference/standard-sql/lexical>.
6. SQLFluff — Rules Reference —
   <https://docs.sqlfluff.com/en/stable/reference/rules.html>
   (категории aliasing / ambiguous / capitalisation / convention / layout /
   references / structure / postgres); Default configuration —
   <https://github.com/sqlfluff/sqlfluff/blob/main/src/sqlfluff/core/default_config.cfg>.
7. PostgreSQL — Lexical Structure —
   <https://www.postgresql.org/docs/current/sql-syntax-lexical.html>;
   SELECT — <https://www.postgresql.org/docs/current/sql-select.html>;
   коммит «Doc: more uppercase keywords in SQLs» —
   <https://www.postgresql.org/message-id/E1vIJK8-005rNZ-2a%40gemulon.postgresql.org>.
8. Matt Mazur — Mazur's SQL Style Guide —
   <https://github.com/mattm/sql-style-guide>.
9. Kickstarter — SQL Style Guide —
   <https://gist.github.com/fredbenenson/7bb92718e19138c20591>.
10. Brooklyn Data Co. — SQL style guide —
    <https://github.com/brooklyn-data/co/blob/main/sql_style_guide.md>.
11. mattmc3 — Modern SQL Style Guide —
    <https://gist.github.com/mattmc3/38a85e6a4ca1093816c08d4815fbebfb>.

Вторичные/вспомогательные (для сравнения, не как норма):

12. Basedash — SQL style guide: conventions that matter —
    <https://www.basedash.com/blog/sql-style-guide-conventions-that-keep-team-queries-readable>
    (таблица сравнения sqlstyle.guide vs dbt; заявление про Mode/Looker leading commas).
13. PostgresAI — How to format SQL —
    <https://postgres.ai/docs/postgres-howtos/development-tools/sql-techniques/how-to-format-sql>
    (производная от Mozilla).
14. Mode — форматтер SQL (гайда нет) —
    <https://mode.com/blog/new-sql-formatting-capability>.
15. Kaggle — Intro to SQL (курс, гайда нет) —
    <https://www.kaggle.com/learn/intro-to-sql>.
16. Airbnb — JavaScript Style Guide (SQL-гайда нет) —
    <https://github.com/airbnb/javascript>.
17. BBVA — GitHub-организация (SQL-гайда нет) —
    <https://github.com/BBVA>.
