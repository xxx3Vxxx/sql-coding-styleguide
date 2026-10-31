-- expected: ST05
select x.id
from (select id from users where active) as x;