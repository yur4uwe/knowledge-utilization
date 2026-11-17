// CQ1: Які електростанції та накопичувачі підключені до підстанції і скільки МВт вони видають?
// Конструкції: MATCH, OPTIONAL MATCH, WHERE, ORDER BY
MATCH (source)-[r:SUPPLIES_POWER_TO]->(s:Substation {id: 'SS_Vinnytska_750'})
OPTIONAL MATCH (source)-[:INSTALLED_AT]->(loc:Substation)
RETURN source.id AS assetId,
       source.name AS assetName,
       labels(source)[0] AS assetCategory,
       source.type AS technologyType,
       source.capacityMW AS capacityMW,
       source.status AS status,
       r.source AS telemetrySource
ORDER BY capacityMW DESC;
