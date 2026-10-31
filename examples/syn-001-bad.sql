-- expected: AM05
select a.id
from users as a
join orders as b on b.user_id = a.id;
