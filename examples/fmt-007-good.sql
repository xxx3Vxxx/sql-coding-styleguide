-- expected: none
select
    id,
    name
from users
where id = 10 and id in (1, 2);
