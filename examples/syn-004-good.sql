-- expected: none
select id
from customer
where deleted_at is null;
