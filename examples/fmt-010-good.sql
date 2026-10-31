-- expected: none
select c.id
from customer as c
where c.active
order by c.id;
