-- expected: none
select c.id
from customer as c
inner join purchase as p on p.customer_id = c.id;
