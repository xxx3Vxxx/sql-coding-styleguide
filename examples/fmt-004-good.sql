-- expected: none
select id
from customer
where id = 1
order by id
limit 5;
