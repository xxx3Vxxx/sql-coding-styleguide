-- expected: CP01, CP03
SELECT COUNT(*) AS total
FROM customer
WHERE id > 0;
