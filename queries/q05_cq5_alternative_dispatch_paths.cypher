// CQ5: Як диспетчер може перенаправити транзит потужності між підстанціями при перевантаженні лінії?
// Конструкції: Variable-length path (*1..3), WHERE, WITH, collect(), length()
MATCH path = (s1:Substation {id: 'SS_Zakhidnoukrainska_750'})-[:CONNECTED_TO*1..3]-(s2:Substation {id: 'SS_Kyivska_750'})
WHERE s1 <> s2
WITH path, length(path) AS hopCount, [n IN nodes(path) | n.name] AS routeNodes
RETURN hopCount,
       routeNodes,
       [r IN relationships(path) | type(r)] AS hopTypes
ORDER BY hopCount ASC
LIMIT 5;
