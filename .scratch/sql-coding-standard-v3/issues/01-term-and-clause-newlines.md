# 01: Термин и обязательный перенос `values`/`set`

**What to build:** однострочный `insert into customer (id, name) values (1, 'Alice');`
перестаёт быть валидным — перенос `values` и `set` становится обязательным и
проверяется линтером; термин «Корневое ключевое слово» перестаёт быть
двусмысленным и покрывает DML-клаузы, которые линтер умеет проверять. Плюс в
документе появляется первый DML-пример.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] В `GLOSSARY.md` определение «Корневое ключевое слово» включает `values` и
      `set`, и поясняет, почему `returning` в него не входит (нет узла-клаузулы
      в парсере — перенос не проверяется).
- [ ] В `FMT-004` перечень-пример ключевых слов в скобках дополнен `values` и
      `set`; уровень `MUST` и строка §8.2 не меняются.
- [ ] В `.sqlfluff` и `.sqlfluff.base` добавлены секции
      `[sqlfluff:layout:type:values_clause]` и
      `[sqlfluff:layout:type:set_clause_list]` с `keyword_line_position = leading`
      и комментарием-ссылкой на `FMT-004`; секции идентичны в обоих профилях.
- [ ] Однострочный `insert into customer (id, name) values (1, 'Alice');` даёт
      `LT14`; канонический многострочный DML (в том числе upsert с вложенными
      `set`/`where`) остаётся чистым.
- [ ] `examples/fmt-004-good.sql` содержит DML-пример, остающийся чистым;
      `examples/fmt-004-bad.sql` содержит DML-строку, срабатывающую ровно
      `LT14`; новых файлов в `examples/` не появляется.
- [ ] В блоке «Хорошо» правила `FMT-004` есть DML-пример.
- [ ] `python3 scripts/check.py --all` и
      `python3 scripts/check.py --config .sqlfluff.base` — зелёные.
