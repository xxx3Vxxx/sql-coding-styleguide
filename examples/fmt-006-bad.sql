-- expected: CP01, CP03
SELECT
    COUNT(*) AS total
FROM users
WHERE id > 0;
