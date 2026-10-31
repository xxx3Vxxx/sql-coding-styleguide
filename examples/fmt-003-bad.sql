-- expected: LT05
select 'this is an example of an extremely long line of text that pushes the total line length beyond the one hundred and twenty character limit' as note
from users;
