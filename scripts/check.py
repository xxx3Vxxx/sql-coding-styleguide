#!/usr/bin/env python3
"""Проверка корпуса примеров на соответствие правилам стандарта.

Для каждого файла `examples/*.sql` первая строка-комментарий вида
`-- expected: <codes>` (или `-- expected: none`) задаёт ожидаемый набор
сработавших правил линтера. Скрипт прогоняет `sqlfluff lint` по каталогу
`examples/` и сверяет фактически сработавшие коды с ожидаемыми.

Набор кодов должен совпадать точно (порядок не важен):
- на «хорошем» примере (`none`) линтер молчит;
- на «плохом» срабатывают ровно перечисленные правила.

Режимы:
  (без флагов)       корпус по полному профилю `.sqlfluff` (автоподхват);
  --config <файл>    выбрать конфиг (напр. `.sqlfluff.base` для базового);
  --consistency      только сверка согласованности (check_consistency.py);
  --all              корпус + сверка согласованности одним прогоном.

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

USAGE = """\
Использование:
  python3 scripts/check.py [--config <файл>] [--consistency | --all]

  --config <файл>   Конфиг SQLFluff для прогона корпуса (напр. `.sqlfluff.base`).
  --consistency     Только сверка согласованности документа и конфига.
  --all             Корпус + сверка согласованности.
  -h, --help        Эта справка.
"""


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


def run_corpus(config_path=None):
    """Прогон линтера по корпусу `examples/`; возвращает код выхода."""
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

    cmd = [sqlfluff, "lint", "--format", "json"]
    if config_path:
        cmd += ["--config", config_path]
    cmd.append(examples_dir)

    proc = subprocess.run(cmd, capture_output=True, text=True)
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
    profile = config_path or ".sqlfluff (по умолчанию)"
    print("OK: {n} фикстур совпали (конфиг: {profile})".format(
        n=len(fixtures), profile=profile))
    return 0


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if "--help" in args or "-h" in args:
        print(USAGE)
        return 0

    config_path = None
    if "--config" in args:
        idx = args.index("--config")
        if idx + 1 >= len(args):
            print("ERROR: `--config` требует значение", file=sys.stderr)
            print(USAGE, file=sys.stderr)
            return 2
        config_path = args[idx + 1]

    do_consistency = "--consistency" in args or "--all" in args
    do_corpus = ("--all" in args) or ("--consistency" not in args)

    code = 0
    if do_corpus:
        code = max(code, run_corpus(config_path))
    if do_consistency:
        scripts_dir = os.path.dirname(os.path.abspath(__file__))
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        import check_consistency  # noqa: E402 (локальный импорт, тот же каталог)
        code = max(code, check_consistency.main())
    return code


if __name__ == "__main__":
    sys.exit(main())
