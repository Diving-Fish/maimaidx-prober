template = """SELECT
    'count' AS grade,
    COUNT(*) AS count
FROM
    newrecord
WHERE
    chart_id = -
UNION
SELECT
    'avg' AS grade,
    avg(achievements) AS count
FROM
    newrecord
WHERE
    chart_id = -
UNION
SELECT
    'avg_dx_score' AS grade,
    avg(dxScore) AS count
FROM
    newrecord
WHERE
    chart_id = -
UNION
SELECT
    'd' AS grade,
    COUNT(*) AS count
FROM
    newrecord
WHERE
    achievements >= 0 AND achievements < 50 AND chart_id = -
UNION
SELECT
    'c' AS grade,
    COUNT(*) AS count
FROM
    newrecord
WHERE
    achievements >= 50 AND achievements < 60 AND chart_id = -
UNION
SELECT
    'b' AS grade,
    COUNT(*) AS count
FROM
    newrecord
WHERE
    achievements >= 60 AND achievements < 70 AND chart_id = -
UNION
SELECT
    'bb' AS grade,
    COUNT(*) AS count
FROM
    newrecord
WHERE
    achievements >= 70 AND achievements < 75 AND chart_id = -
UNION
SELECT
    'bbb' AS grade,
    COUNT(*) AS count
FROM
    newrecord
WHERE
    achievements >= 75 AND achievements < 80 AND chart_id = -
UNION
SELECT
    'a' AS grade,
    COUNT(*) AS count
FROM
    newrecord
WHERE
    achievements >= 80 AND achievements < 90 AND chart_id = -
UNION
SELECT
    'aa' AS grade,
    COUNT(*) AS count
FROM
    newrecord
WHERE
    achievements >= 90 AND achievements < 94 AND chart_id = -
UNION
SELECT
    'aaa' AS grade,
    COUNT(*) AS count
FROM
    newrecord
WHERE
    achievements >= 94 AND achievements < 97 AND chart_id = -
UNION
SELECT
    's' AS grade,
    COUNT(*) AS count
FROM
    newrecord
WHERE
    achievements >= 97 AND achievements < 98 AND chart_id = -
UNION
SELECT
    'sp' AS grade,
    COUNT(*) AS count
FROM
    newrecord
WHERE
    achievements >= 98 AND achievements < 99 AND chart_id = -
UNION
SELECT
    'ss' AS grade,
    COUNT(*) AS count
FROM
    newrecord
WHERE
    achievements >= 99 AND achievements < 99.5 AND chart_id = -
UNION
SELECT
    'ssp' AS grade,
    COUNT(*) AS count
FROM
    newrecord
WHERE
    achievements >= 99.5 AND achievements < 100 AND chart_id = -
UNION
SELECT
    'sss' AS grade,
    COUNT(*) AS count
FROM
    newrecord
WHERE
    achievements >= 100 AND achievements < 100.5 AND chart_id = -
UNION
SELECT
    'sssp' AS grade,
    COUNT(*) AS count
FROM
    newrecord
WHERE
    achievements >= 100.5 AND achievements <= 101 AND chart_id = -
UNION
SELECT
    'fc' AS grade,
    COUNT(*) AS count
FROM
    newrecord
WHERE
    fc='fc' AND chart_id = -
UNION
SELECT
    'fcp' AS grade,
    COUNT(*) AS count
FROM
    newrecord
WHERE
    fc='fcp' AND chart_id = -
UNION
SELECT
    'ap' AS grade,
    COUNT(*) AS count
FROM
    newrecord
WHERE
    fc='ap' AND chart_id = -
UNION
SELECT
    'app' AS grade,
    COUNT(*) AS count
FROM
    newrecord
WHERE
    fc='app' AND chart_id = -;"""


def return_template(chart_id):
    return template.replace('-', str(chart_id))
