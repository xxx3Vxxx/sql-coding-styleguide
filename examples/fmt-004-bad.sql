-- expected: LT14
select id from customer where id = 1 order by id limit 5;

insert into customer (id, name) values (1, 'Alice');
