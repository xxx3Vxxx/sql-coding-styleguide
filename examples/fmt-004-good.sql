-- expected: none
select id
from users
where id = 1
order by id
limit 5;
