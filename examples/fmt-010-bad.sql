-- expected: LT02
select c.id
    from customer as c
    where c.is_active
    order by c.id;
