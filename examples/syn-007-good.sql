-- expected: none
select
    u.id,
    o.amount
from users as u
inner join orders as o on o.user_id = u.id;
