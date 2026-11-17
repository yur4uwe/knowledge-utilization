// Аналіз впливу 2 (Impact Analysis, глибина >= 3):
// Аналіз каскадного відключення при повній втраті опорної підстанції ПС 750 кВ "Київська":
// Пошук залежних генераторів, транзитів 330/110 кВ, розподільчих підстанцій та критичних споживачів до глибини 3
MATCH path = (root:Substation {id: 'Kyivska_Substation_750kV'})-[:CONNECTED_TO|FEEDS_LOAD|SUPPLIES_POWER_TO*1..3]-(target)
WHERE target <> root
WITH root, target, length(path) AS cascadeHop, labels(target)[0] AS targetClass
RETURN cascadeHop,
       targetClass,
       target.id AS targetId,
       target.name AS targetName,
       coalesce(target.capacityMW, target.demandMW, target.voltageKV, 0.0) AS capacityOrDemandMW
ORDER BY cascadeHop ASC, targetClass ASC;
