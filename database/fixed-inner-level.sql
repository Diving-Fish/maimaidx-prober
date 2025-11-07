# noinspection SqlWithoutWhereForFile

delete from record_avg_table;
delete from record_stddev_table;
delete from recordanalysis;

delete from newrecord where chart_id not in (select id from chart);

insert into record_avg_table
select
    chart_id as c,
    avg(achievements) as a
from newrecord
where
    achievements > 0
group by chart_id;

insert into record_stddev_table
select
    chart_id as c,
    stddev(achievements) as std_dev
from newrecord
where
    abs(achievements - (select a from record_avg_table where c = chart_id)) < 10
group by chart_id;

insert into recordanalysis
SELECT
    chart_id,
    SUM(achievements) AS sum_achievements,
    SUM(dxScore) AS sum_dx_score,
    SUM(IF(achievements >= 0 AND achievements < 50, 1, 0))       AS d,
    SUM(IF(achievements >= 50 AND achievements < 60, 1, 0))      AS c,
    SUM(IF(achievements >= 60 AND achievements < 70, 1, 0))      AS b,
    SUM(IF(achievements >= 70 AND achievements < 75, 1, 0))      AS bb,
    SUM(IF(achievements >= 75 AND achievements < 80, 1, 0))      AS bbb,
    SUM(IF(achievements >= 80 AND achievements < 90, 1, 0))      AS a,
    SUM(IF(achievements >= 90 AND achievements < 94, 1, 0))      AS aa,
    SUM(IF(achievements >= 94 AND achievements < 97, 1, 0))      AS aaa,
    SUM(IF(achievements >= 97 AND achievements < 98, 1, 0))      AS s,
    SUM(IF(achievements >= 98 AND achievements < 99, 1, 0))      AS sp,
    SUM(IF(achievements >= 99 AND achievements < 99.5, 1, 0))    AS ss,
    SUM(IF(achievements >= 99.5 AND achievements < 100, 1, 0))   AS ssp,
    SUM(IF(achievements >= 100 AND achievements < 100.5, 1, 0))  AS sss,
    SUM(IF(achievements >= 100.5 AND achievements <= 101, 1, 0)) AS sssp,
    SUM(IF(fc = 'fc', 1, 0)) AS fc,
    SUM(IF(fc = 'fcp', 1, 0)) AS fcp,
    SUM(IF(fc = 'ap', 1, 0)) AS ap,
    SUM(IF(fc = 'app', 1, 0)) AS app,
    COUNT(achievements) AS cnt
FROM
    newrecord
where
    achievements > 0
GROUP BY
    chart_id;


select c.difficulty,
    SUM(recordanalysis.sum_achievements) / SUM(recordanalysis.cnt) as ach,
    SUM(recordanalysis.d) / SUM(recordanalysis.cnt) as d,
    SUM(recordanalysis.c) / SUM(recordanalysis.cnt) as c,
    SUM(recordanalysis.b) / SUM(recordanalysis.cnt) as b,
    SUM(recordanalysis.bb) / SUM(recordanalysis.cnt) as bb,
    SUM(recordanalysis.bbb) / SUM(recordanalysis.cnt) as bbb,
    SUM(recordanalysis.a) / SUM(recordanalysis.cnt) as a,
    SUM(recordanalysis.aa) / SUM(recordanalysis.cnt) as aa,
    SUM(recordanalysis.aaa) / SUM(recordanalysis.cnt) as aaa,
    SUM(recordanalysis.s) / SUM(recordanalysis.cnt) as s,
    SUM(recordanalysis.sp) / SUM(recordanalysis.cnt) as sp,
    SUM(recordanalysis.ss) / SUM(recordanalysis.cnt) as ss,
    SUM(recordanalysis.ssp) / SUM(recordanalysis.cnt) as ssp,
    SUM(recordanalysis.sss) / SUM(recordanalysis.cnt) as sss,
    SUM(recordanalysis.sssp) / SUM(recordanalysis.cnt) as sssp,
    SUM(recordanalysis.fc) / SUM(recordanalysis.cnt) as fc,
    SUM(recordanalysis.fcp) / SUM(recordanalysis.cnt) as fcp,
    SUM(recordanalysis.ap) / SUM(recordanalysis.cnt) as ap,
    SUM(recordanalysis.app) / SUM(recordanalysis.cnt) as app
from recordanalysis join chart c on recordanalysis.chart_id = c.id group by c.difficulty;

