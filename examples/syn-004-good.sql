-- expected: none
select id
from users
where deleted_at is null;
