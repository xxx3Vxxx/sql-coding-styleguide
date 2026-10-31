-- expected: LT02
select u.id
    from users as u
    where u.active
    order by u.id;
