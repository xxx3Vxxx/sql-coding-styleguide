-- expected: none
select
    count(*) as total
from users
where id > 0;
