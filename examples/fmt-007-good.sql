-- expected: none
select
    id,
    name
from customer
where id = 10 and id in (1, 2);
