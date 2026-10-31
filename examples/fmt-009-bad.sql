-- expected: LT02
with active_customer as (
select id
from customer
where is_active
)
select active_customer.id
from active_customer;
