-- expected: CV05
select id
from customer
where deleted_at = null;
