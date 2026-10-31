-- expected: LT02
with x as (
select id
from users
where active
)
select x.id
from x;
