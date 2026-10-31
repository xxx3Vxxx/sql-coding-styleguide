-- expected: ST05
select x.id
from (
    select id
    from customer
    where active
) as x;
