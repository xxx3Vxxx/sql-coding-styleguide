-- expected: ST05
select active_customer.id
from (
    select id
    from customer
    where is_active
) as active_customer;
