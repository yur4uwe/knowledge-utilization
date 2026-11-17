// CQ2: Яка сумарна та середня потужність обладнання за класами напруги?
// Конструкції: MATCH, WITH, aggregations (count, sum, avg), WHERE, ORDER BY
MATCH (g:GeneratingUnit)
WHERE g.voltageKV > 0
WITH g.voltageKV AS voltageClassKV,
     count(g) AS unitCount,
     sum(g.capacityMW) AS totalCapacityMW,
     avg(g.capacityMW) AS avgCapacityMW
WHERE unitCount >= 1
RETURN voltageClassKV,
       unitCount,
       round(totalCapacityMW, 2) AS totalCapacityMW,
       round(avgCapacityMW, 2) AS avgCapacityMW
ORDER BY voltageClassKV DESC;
