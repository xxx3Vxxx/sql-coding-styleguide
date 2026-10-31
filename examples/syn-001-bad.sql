-- expected: AM05
select c.id
from customer as c
join purchase as p on p.customer_id = c.id;
