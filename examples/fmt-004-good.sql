-- expected: none
select id
from customer
where id = 1
order by id
limit 5;

insert into customer (id, name)
values (1, 'Alice');

update customer
set
    name = 'Alice'
where id = 1;

insert into customer (id, name)
values (1, 'Alice')
on conflict (id) do update
    set
        name = excluded.name
    where customer.id = 1;
