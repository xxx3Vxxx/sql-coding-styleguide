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
  базовый профиль исключает SHOULD-проверяемые правила (`exclude_rules`).

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
# Имя правила SQLFluff: строчное с точками, напр. layout.indent, ambiguous.join.
RULE_NAME_RE = re.compile(r"[a-z][a-z0-9]*(?:\.[a-z_][a-z0-9_]*)+")


def repo_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read_text(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


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
    }


def dotted_names(text):
    return set(RULE_NAME_RE.findall(text))


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

    # Итог.
    print()
    if failures:
        print("ИТОГ: {n} ошибок".format(n=len(failures)), file=sys.stderr)
        return 1
    print("ИТОГ: согласованность документа и конфига подтверждена ({} проверок)".format(checks_run))
    return 0


if __name__ == "__main__":
    sys.exit(main())
