#!/usr/bin/env python3
"""Сверка согласованности: STANDARD.md ↔ §8-маппинг ↔ референсный конфиг линтера.

Второй шов проверки (первый — прогон линтера по корпусу в `check.py`). Скрипт
проверяет, что ID правил стандарта, таблица маппинга (§8.2) и конфиги SQLFluff
(`.sqlfluff` — полный профиль, `.sqlfluff.base` — базовый) не расходятся:

- у каждого правила стандарта корректный ID вида `FMT|NAM|SYN`-NNN;
- таблица §8.2 покрывает ровно все правила документа, уровни и признак
  «проверяется линтером» совпадают;
- для каждого правила «проверяется линтером: да» соответствующее правило
  SQLFluff включено в полном профиле (forward);
- каждое включённое правило SQLFluff ссылается на правило стандарта (reverse);
- каждая секция `[sqlfluff:rules:*]` в конфиге сопровождена комментарием со
  ссылкой на ID правила, и все упомянутые ID существуют;
- профили согласованы: `MUST` ↔ `error`, `SHOULD` ↔ `warning` (ключ `warnings`),
  базовый профиль исключает SHOULD-проверяемые правила (`exclude_rules`);
- корпус фикстур соответствует признаку «проверяется линтером»: у каждого
  правила «да» есть пара `examples/<id>-good.sql` + `examples/<id>-bad.sql`,
  у правила «нет» фикстур нет, а все файлы названы по этому шаблону;
- профили совпадают во всём, кроме `rules`/`warnings`/`exclude_rules` (любая
  layout-секция или значение, забытые в одном из файлов, ловятся);
- в прозе `*.md` нет отсылок к несуществующим путям из известных корней
  (`docs/`, `.scratch/`, `examples/`, `scripts/`);
- версия стандарта в шапке `STANDARD.md` совпадает с версией в шапке
  `README.md`;
- число фикстур, зашитое в `README.md` как ожидаемый результат прогона, равно
  фактическому числу `examples/*.sql`.

Выход: 0 — всё согласовано; 1 — есть расхождения.

Зависимостей вне стандартной библиотеки нет.
"""
import os
import re
import sys

RULE_ID_RE = re.compile(r"^(FMT|NAM|SYN)-\d{3}$")
HEADER_RE = re.compile(r"^###\s+((?:FMT|NAM|SYN)-\d{3})\b")
LEVEL_RE = re.compile(r"\*\*Уровень нормативности:\*\*\s*(MUST|SHOULD|MAY)")
LINT_RE = re.compile(r"\*\*Проверяется линтером:\*\*\s*(да|нет)")
COMMENT_ID_RE = re.compile(r"\b(?:FMT|NAM|SYN)-\d{3}\b")
# Версия стандарта в шапке: «Версия: **0.3.0**» / «версия **0.3.0**».
VERSION_RE = re.compile(r"^>.*?[Вв]ерсия:?\s*\*\*(\d+\.\d+\.\d+)\*\*", re.MULTILINE)
# Число фикстур, зашитое в README как ожидаемый результат прогона.
FIXTURE_COUNT_RE = re.compile(r"OK:\s*(\d+)\s+фикстур")
# Имя правила SQLFluff: строчное с точками, напр. layout.indent, ambiguous.join.
RULE_NAME_RE = re.compile(r"[a-z][a-z0-9]*(?:\.[a-z_][a-z0-9_]*)+")


def repo_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read_text(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def parse_doc_version(text):
    """Версия стандарта из шапки документа или None, если шапки нет."""
    match = VERSION_RE.search(text)
    return match.group(1) if match else None


# ---------------------------------------------------------------------------
# Разбор STANDARD.md
# ---------------------------------------------------------------------------

def parse_doc_rules(text):
    """Вернуть (rules, errors): упорядоченный список {id, level, lint} и ошибки.

    Правило описывается заголовком `### FMT-001 — ...` и телом до следующего
    заголовка; из тела берём `**Уровень нормативности:**` и
    `**Проверяется линтером:**`.
    """
    rules = []
    errors = []
    lines = text.splitlines()
    i = 0
    n = len(lines)
    while i < n:
        match = HEADER_RE.match(lines[i].strip())
        if not match:
            i += 1
            continue
        rule_id = match.group(1)
        body = []
        j = i + 1
        while j < n:
            stripped = lines[j].strip()
            if stripped.startswith("### ") or stripped.startswith("## "):
                break
            body.append(stripped)
            j += 1
        bloc = "\n".join(body)

        level_m = LEVEL_RE.search(bloc)
        lint_m = LINT_RE.search(bloc)

        if not RULE_ID_RE.fullmatch(rule_id):
            errors.append(
                "некорректный ID правила: {!r}".format(rule_id)
            )
        if not level_m:
            errors.append(
                "{}: не найдено поле «Уровень нормативности»".format(rule_id)
            )
        if not lint_m:
            errors.append(
                "{}: не найдено поле «Проверяется линтером»".format(rule_id)
            )

        rules.append(
            {
                "id": rule_id,
                "level": level_m.group(1) if level_m else None,
                "lint": (lint_m.group(1) == "да") if lint_m else None,
            }
        )
        i = j
    return rules, errors


def parse_table(text):
    """Вернуть (rows, errors): упорядоченный список {id, level, lint, cell}.

    Строки — это строки таблицы §8.2 (заголовок содержит `| ID |` и
    `| SQLFluff`). Ячейки: ID, Уровень, Проверяется линтером, SQLFluff.
    """
    rows = []
    errors = []
    lines = text.splitlines()
    # Ищем строку-заголовок таблицы §8.2.
    header_idx = None
    for idx, line in enumerate(lines):
        if line.strip().startswith("|") and "| ID |" in line and "SQLFluff" in line:
            header_idx = idx
            break
    if header_idx is None:
        return rows, ["не найдена таблица маппинга §8.2 (заголовок «| ID | …»)"]

    for line in lines[header_idx + 1:]:
        stripped = line.strip()
        if not stripped.startswith("|"):
            break  # конец таблицы
        # Пропускаем разделитель | --- | --- | --- | --- |
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if all(set(c) <= {"-", " ", ":"} or c == "" for c in cells):
            continue
        if len(cells) < 4:
            errors.append("строка таблицы не разбирается: {!r}".format(stripped))
            continue
        rule_id, level, lint, cell = cells[0], cells[1], cells[2], cells[3]
        if not RULE_ID_RE.fullmatch(rule_id):
            errors.append("некорректный ID в таблице §8: {!r}".format(rule_id))
        rows.append(
            {
                "id": rule_id,
                "level": level,
                "lint": lint,
                "cell": cell,
            }
        )
    return rows, errors


# ---------------------------------------------------------------------------
# Разбор конфигов SQLFluff
# ---------------------------------------------------------------------------

def split_list(value):
    if value is None:
        return set()
    return {part.strip() for part in value.split(",") if part.strip()}


def parse_config(path):
    """Разобрать INI-конфиг SQLFluff.

    Возвращает:
      rules_set      — имена включённых правил (`rules =`),
      warnings_set   — `warnings =`,
      exclude_set    — `exclude_rules =`,
      comment_refs   — {имя секции: {ID правила из комментариев}},
      rule_sections  — {имя правила: {ID правила}} для `[sqlfluff:rules:*]`.
    """
    options = {}  # секция -> {key: value}
    comment_refs = {}
    current = None
    pending_comments = []

    with open(path, encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if not line:
                continue
            if line.startswith("#"):
                pending_comments.append(line.lstrip("#").strip())
                continue
            m = re.match(r"^\[(.*)\]$", line)
            if m:
                current = m.group(1).strip()
                options.setdefault(current, {})
                refs = set()
                for comment in pending_comments:
                    refs.update(COMMENT_ID_RE.findall(comment))
                comment_refs[current] = refs
                pending_comments = []
                continue
            if "=" in line and current:
                key, _, value = line.partition("=")
                options[current][key.strip()] = value.strip()

    sqlfluff = options.get("sqlfluff", {})
    rules_set = split_list(sqlfluff.get("rules"))
    warnings_set = split_list(sqlfluff.get("warnings"))
    exclude_set = split_list(sqlfluff.get("exclude_rules"))

    rule_sections = {}
    for section, refs in comment_refs.items():
        if section.startswith("sqlfluff:rules:"):
            rule_name = section[len("sqlfluff:rules:"):]
            rule_sections[rule_name] = refs

    return {
        "rules_set": rules_set,
        "warnings_set": warnings_set,
        "exclude_set": exclude_set,
        "comment_refs": comment_refs,
        "rule_sections": rule_sections,
        "options": options,
    }


def dotted_names(text):
    return set(RULE_NAME_RE.findall(text))


# Ключи секции `[sqlfluff]`, которые законно различаются между профилями.
PROFILE_ONLY_KEYS = ("rules", "warnings", "exclude_rules")


def profile_sections(options):
    """Секции профиля без ключей, различающихся между профилями по назначению."""
    sections = {}
    for section, values in options.items():
        if section == "sqlfluff":
            values = {k: v for k, v in values.items() if k not in PROFILE_ONLY_KEYS}
        if values:
            sections[section] = dict(values)
    return sections


# Проверка отсылок к файлам: только пути из известных корней репозитория.
REF_ROOTS = ("docs/", ".scratch/", "examples/", "scripts/")
# Шаблоны/диапазоны/перечисления — не конкретные пути.
REF_SKIP_RE = re.compile(r"[<>{}~*,]|\u2013|\u2014|\.\.\.")
INLINE_CODE_RE = re.compile(r"`([^`\n]+)`")
FENCED_BLOCK_RE = re.compile(r"```.*?```", re.S)
MARKDOWN_DOCS = ("AGENTS.md", "README.md", "GLOSSARY.md", "STANDARD.md")


def iter_markdown_docs(root):
    docs = []
    for name in MARKDOWN_DOCS:
        path = os.path.join(root, name)
        if os.path.exists(path):
            docs.append(path)
    for top in ("docs", ".scratch"):
        for dirpath, _dirs, names in os.walk(os.path.join(root, top)):
            docs.extend(
                os.path.join(dirpath, name)
                for name in sorted(names)
                if name.endswith(".md")
            )
    return docs


def find_broken_refs(root):
    """Пути из известных корней, упомянутые в прозе `*.md`, но отсутствующие."""
    missing = []
    for path in iter_markdown_docs(root):
        text = FENCED_BLOCK_RE.sub("", read_text(path))  # игнорируем код-блоки
        rel = os.path.relpath(path, root)
        for span in INLINE_CODE_RE.findall(text):
            candidate = span.strip()
            if not candidate or " " in candidate:
                continue
            if REF_SKIP_RE.search(candidate):
                continue
            if not candidate.startswith(REF_ROOTS):
                continue
            if not os.path.exists(os.path.join(root, candidate)):
                missing.append("{}: `{}`".format(rel, candidate))
    return sorted(set(missing))


# ---------------------------------------------------------------------------
# Проверки
# ---------------------------------------------------------------------------

def main():
    root = repo_root()
    standard_path = os.path.join(root, "STANDARD.md")
    full_path = os.path.join(root, ".sqlfluff")
    base_path = os.path.join(root, ".sqlfluff.base")

    failures = []
    checks_run = 0

    def note(ok, message):
        nonlocal checks_run
        checks_run += 1
        tag = "ok  " if ok else "FAIL"
        print("{tag} {message}".format(tag=tag, message=message))
        if not ok:
            failures.append(message)

    text = read_text(standard_path)

    # 1) Правила документа.
    doc_rules, doc_errors = parse_doc_rules(text)
    for err in doc_errors:
        note(False, "документ: " + err)
    doc_ids = [r["id"] for r in doc_rules]
    note(
        doc_errors == [],
        "извлечено правил из STANDARD.md: {n} ({ids_sorted})".format(
            n=len(doc_rules),
            ids_sorted=", ".join(sorted(doc_ids)),
        ),
    )
    if len(set(doc_ids)) != len(doc_ids):
        note(False, "в документе есть дублирующиеся ID правил")

    # 1b) Версия стандарта совпадает в шапках STANDARD.md и README.md.
    readme_path = os.path.join(root, "README.md")
    readme_text = read_text(readme_path) if os.path.exists(readme_path) else ""
    standard_version = parse_doc_version(text)
    readme_version = parse_doc_version(readme_text)
    versions_agree = (
        standard_version is not None
        and readme_version is not None
        and standard_version == readme_version
    )
    note(
        versions_agree,
        "версия: STANDARD.md и README.md совпадают"
        + (
            ""
            if versions_agree
            else " (STANDARD={!r}, README={!r})".format(
                standard_version, readme_version
            )
        ),
    )

    # 2) Таблица §8.2.
    table_rows, table_errors = parse_table(text)
    for err in table_errors:
        note(False, "§8: " + err)
    table_ids = [r["id"] for r in table_rows]
    table_by_id = {r["id"]: r for r in table_rows}

    missing_in_table = sorted(set(doc_ids) - set(table_ids))
    extra_in_table = sorted(set(table_ids) - set(doc_ids))
    note(
        not missing_in_table,
        "§8: каждое правило документа покрыто таблицей"
        + ("" if not missing_in_table else " (нет: {})".format(", ".join(missing_in_table))),
    )
    note(
        not extra_in_table,
        "§8: в таблице нет лишних правил"
        + ("" if not extra_in_table else " (лишние: {})".format(", ".join(extra_in_table))),
    )

    # 3) Уровни и признак «проверяется линтером» в таблице == документ.
    mismatched_fields = []
    for rid in sorted(set(doc_ids) & set(table_ids)):
        doc = {r["id"]: r for r in doc_rules}[rid]
        row = table_by_id[rid]
        if row["level"] != doc["level"]:
            mismatched_fields.append(
                "{}: уровень в §8={!r}, в документе={!r}".format(rid, row["level"], doc["level"])
            )
        expected_lint_flag = "да" if doc["lint"] else "нет"
        if row["lint"] != expected_lint_flag:
            mismatched_fields.append(
                "{}: «проверяется линтером» в §8={!r}, в документе={!r}".format(
                    rid, row["lint"], expected_lint_flag
                )
            )
    note(
        not mismatched_fields,
        "§8: уровни и признак «проверяется линтером» совпадают с документом"
        + ("" if not mismatched_fields else "\n  - " + "\n  - ".join(mismatched_fields)),
    )

    # 4) Конфиги.
    full = parse_config(full_path)
    base = parse_config(base_path)

    def config_label(path):
        return os.path.basename(path)

    # Forward: «да» → правило включено в полном профиле.
    forward_fail = []
    checkable_rules = [r for r in doc_rules if r["lint"]]
    referenced_names = set()
    for rule in checkable_rules:
        row = table_by_id.get(rule["id"])
        names = dotted_names(row["cell"]) if row else set()
        referenced_names |= names
        enabled = names & full["rules_set"]
        if not enabled:
            forward_fail.append(
                "{id}: «да», но ни одно правило ({names}) не включено в конфиг".format(
                    id=rule["id"],
                    names=", ".join(sorted(names)) if names else "нет в §8",
                )
            )
    note(
        not forward_fail,
        "полный профиль: все правила «проверяется линтером: да» включены"
        + ("" if not forward_fail else "\n  - " + "\n  - ".join(forward_fail)),
    )

    # Reverse: каждое включённое правило ссылается на правило документа (§8).
    reverse_fail = sorted(full["rules_set"] - referenced_names)
    note(
        not reverse_fail,
        "полный профиль: каждое включённое правило ссылается на правило стандарта"
        + ("" if not reverse_fail else " (нет маппинга: {})".format(", ".join(reverse_fail))),
    )

    # Имена из комментариев секций ссылаются на существующие ID.
    for path, cfg in [(full_path, full), (base_path, base)]:
        label = config_label(path)
        unknown_refs = []
        for section, refs in sorted(cfg["comment_refs"].items()):
            for ref in sorted(refs):
                if ref not in set(doc_ids):
                    unknown_refs.append(
                        "[{section}] ссылается на несуществующий {ref}".format(
                            section=section, ref=ref
                        )
                    )
        note(
            not unknown_refs,
            "{label}: все ID из комментариев существуют в документе".format(label=label)
            + ("" if not unknown_refs else "\n  - " + "\n  - ".join(unknown_refs)),
        )

        # Каждая секция [sqlfluff:rules:*] — с комментарием-маппингом и
        # включена в `rules`.
        untraced = []
        for rule_name, refs in sorted(cfg["rule_sections"].items()):
            if not refs:
                untraced.append(
                    "[sqlfluff:rules:{name}] без комментария-маппинга".format(name=rule_name)
                )
            if rule_name not in cfg["rules_set"]:
                untraced.append(
                    "[sqlfluff:rules:{name}] не включено в `rules`".format(name=rule_name)
                )
        note(
            not untraced,
            "{label}: каждая секция `[sqlfluff:rules:*]` имеет маппинг и включена".format(
                label=label
            )
            + ("" if not untraced else "\n  - " + "\n  - ".join(untraced)),
        )

    # 5) Согласованность профилей.
    should_checkable = [r for r in doc_rules if r["lint"] and r["level"] == "SHOULD"]
    should_names = set()
    for rule in should_checkable:
        row = table_by_id.get(rule["id"])
        should_names |= dotted_names(row["cell"]) if row else set()

    note(
        base["rules_set"] == full["rules_set"],
        "профили: список `rules` в базовом и полном профилях совпадает",
    )
    note(
        not base["warnings_set"],
        "профили: в базовом профиле нет `warnings` (только `error`)",
    )
    note(
        full["warnings_set"] == should_names,
        "профили: `warnings` полного профиля = SHOULD-проверяемые правила"
        + (
            ""
            if full["warnings_set"] == should_names
            else " (warnings={}, SHOULD={})".format(
                sorted(full["warnings_set"]), sorted(should_names)
            )
        ),
    )
    note(
        base["exclude_set"] == should_names,
        "профили: `exclude_rules` базового профиля = SHOULD-проверяемые правила"
        + (
            ""
            if base["exclude_set"] == should_names
            else " (exclude={}, SHOULD={})".format(
                sorted(base["exclude_set"]), sorted(should_names)
            )
        ),
    )

    # 5b) Паритет секций: кроме rules/warnings/exclude_rules профили совпадают.
    full_rest = profile_sections(full["options"])
    base_rest = profile_sections(base["options"])
    parity_diff = []
    for section in sorted(set(full_rest) | set(base_rest)):
        if full_rest.get(section) != base_rest.get(section):
            parity_diff.append(
                "[{section}]: полный={f}, базовый={b}".format(
                    section=section,
                    f=full_rest.get(section),
                    b=base_rest.get(section),
                )
            )
    note(
        not parity_diff,
        "профили: все секции, кроме `rules`/`warnings`/`exclude_rules`, идентичны"
        + ("" if not parity_diff else "\n  - " + "\n  - ".join(parity_diff)),
    )

    # 6) Корпус фикстур: инвариант «правило ↔ examples/<id>-{good,bad}.sql».
    examples_dir = os.path.join(root, "examples")
    fixture_by_rule = {}
    off_pattern = []
    for name in sorted(os.listdir(examples_dir)):
        if not name.endswith(".sql"):
            continue
        match = re.match(r"^((?:fmt|nam|syn)-\d{3})-(good|bad)\.sql$", name)
        if not match:
            off_pattern.append(name)
            continue
        fixture_by_rule.setdefault(match.group(1), set()).add(match.group(2))

    fixture_fail = []
    for rule in doc_rules:
        rid = rule["id"].lower()
        kinds = fixture_by_rule.get(rid, set())
        if rule["lint"]:
            for kind in ("good", "bad"):
                if kind not in kinds:
                    fixture_fail.append(
                        "{id}: «проверяется линтером: да», но нет examples/{rid}-{kind}.sql".format(
                            id=rule["id"], rid=rid, kind=kind
                        )
                    )
        elif kinds:
            fixture_fail.append(
                "{id}: «проверяется линтером: нет», но есть фикстуры ({kinds})".format(
                    id=rule["id"], kinds=", ".join(sorted(kinds))
                )
            )
    note(
        not fixture_fail,
        "корпус: у каждого правила «да» есть пара good/bad, у «нет» фикстур нет"
        + ("" if not fixture_fail else "\n  - " + "\n  - ".join(fixture_fail)),
    )
    note(
        not off_pattern,
        "корпус: все файлы examples/*.sql названы по шаблону <ID>-good|bad.sql"
        + ("" if not off_pattern else " (мимо шаблона: {})".format(", ".join(off_pattern))),
    )

    # 6b) Число фикстур, зашитое в README как ожидаемый результат, — фактическое.
    fixture_count = sum(
        1 for name in os.listdir(examples_dir) if name.endswith(".sql")
    )
    listed_match = FIXTURE_COUNT_RE.search(readme_text)
    listed_count = int(listed_match.group(1)) if listed_match else None
    note(
        listed_count == fixture_count,
        "README: ожидаемое число фикстур совпадает с корпусом"
        + (
            ""
            if listed_count == fixture_count
            else " (README={!r}, examples={})".format(listed_count, fixture_count)
        ),
    )

    # 7) Отсылки к файлам в прозе `*.md` (пути из известных корней).
    broken_refs = find_broken_refs(root)
    note(
        not broken_refs,
        "ссылки: все пути `docs/`/`.scratch/`/`examples/`/`scripts/` из прозы *.md существуют"
        + ("" if not broken_refs else "\n  - " + "\n  - ".join(broken_refs)),
    )

    # Итог.
    print()
    if failures:
        print("ИТОГ: {n} ошибок".format(n=len(failures)), file=sys.stderr)
        return 1
    print("ИТОГ: согласованность документа и конфига подтверждена ({} проверок)".format(checks_run))
    return 0


if __name__ == "__main__":
    sys.exit(main())
