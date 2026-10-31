#!/usr/bin/env python3
"""Проверка корпуса примеров на соответствие правилам стандарта.

Для каждого файла `examples/*.sql` первая строка-комментарий вида
`-- expected: <codes>` (или `-- expected: none`) задаёт ожидаемый набор
сработавших правил линтера. Скрипт прогоняет `sqlfluff lint` по каталогу
`examples/` и сверяет фактически сработавшие коды с ожидаемыми.

Набор кодов должен совпадать точно (порядок не важен):
- на «хорошем» примере (`none`) линтер молчит;
- на «плохом» срабатывают ровно перечисленные правила.

Выход: 0 — всё совпало; 1 — есть расхождения.
"""
import glob
import json
import os
import re
import shutil
import subprocess
import sys

EXPECTED_RE = re.compile(r"^\s*--\s*expected:\s*(.+?)\s*$")


def repo_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resolve_sqlfluff():
    env = os.environ.get("SQLFLUFF")
    if env:
        return env
    candidates = [
        os.path.join(repo_root(), ".venv", "bin", "sqlfluff"),
        "sqlfluff",
    ]
    for candidate in candidates:
        if shutil.which(candidate):
            return candidate
    return None


def read_expected(path):
    """Коды из заголовка `-- expected:` или None, если заголовок не найден."""
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            match = EXPECTED_RE.match(line)
            if match:
                raw = match.group(1).strip()
                if raw.lower() == "none":
                    return set()
                return {code.strip() for code in raw.split(",") if code.strip()}
            if line.strip() and not line.startswith("--"):
                break  # заголовок обязан идти до первого SQL-выражения
    return None


def main():
    sqlfluff = resolve_sqlfluff()
    if not sqlfluff:
        print("ERROR: sqlfluff не найден. Укажите SQLFLUFF или установите линтер.",
              file=sys.stderr)
        return 1

    examples_dir = os.path.join(repo_root(), "examples")
    fixtures = sorted(glob.glob(os.path.join(examples_dir, "*.sql")))
    if not fixtures:
        print("ERROR: нет .sql-фикстур в", examples_dir, file=sys.stderr)
        return 1

    expected = {}
    missing = []
    for path in fixtures:
        codes = read_expected(path)
        if codes is None:
            missing.append(path)
        else:
            expected[os.path.realpath(path)] = codes
    if missing:
        for path in missing:
            print("FAIL {rel}: нет заголовка `-- expected:`".format(
                rel=os.path.relpath(path, repo_root())))
        return 1

    proc = subprocess.run(
        [sqlfluff, "lint", "--format", "json", examples_dir],
        capture_output=True,
        text=True,
    )
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        print("ERROR: не удалось разобрать вывод sqlfluff:", file=sys.stderr)
        print(proc.stdout[:2000], file=sys.stderr)
        return 1

    actual = {}
    for entry in payload:
        codes = {violation["code"] for violation in entry.get("violations", [])}
        actual[os.path.realpath(entry["filepath"])] = codes

    mismatches = 0
    for path in fixtures:
        key = os.path.realpath(path)
        exp = expected.get(key, set())
        act = actual.get(key, set())
        rel = os.path.relpath(path, repo_root())
        if exp == act:
            shown = sorted(act) if act else "clean"
            print("ok   {rel}: {shown}".format(rel=rel, shown=shown))
        else:
            mismatches += 1
            print("FAIL {rel}: expected={e} actual={a}".format(
                rel=rel, e=sorted(exp), a=sorted(act)))

    if mismatches:
        print("{n} фикстур не совпали".format(n=mismatches), file=sys.stderr)
        return 1
    print("OK: {n} фикстур совпали".format(n=len(fixtures)))
    return 0


if __name__ == "__main__":
    sys.exit(main())