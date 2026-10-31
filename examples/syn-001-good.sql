-- expected: none
select a.id
from users as a
inner join orders as b on b.user_id = a.id;
