-- expected: LT02
with x as (
select id
from customer
where active
)
select x.id
from x;
