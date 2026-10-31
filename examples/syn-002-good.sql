-- expected: none
with x as (
    select id
    from users
    where active
)
select x.id
from x;