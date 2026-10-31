-- expected: CV05
select id
from users
where deleted_at = null;
