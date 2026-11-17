// CQ7: Чи є транзитний електричний зв'язок між підстанціями та який найкоротший топологічний маршрут?
// Конструкції: shortestPath(), MATCH, length(), nodes()
MATCH (s1:Substation {id: 'Substation_Zakhidnoukrainska_750kV'}), (s2:Substation {id: 'Substation_Donbaska_750kV'})
MATCH p = shortestPath((s1)-[:CONNECTED_TO*..10]-(s2))
RETURN length(p) AS shortestTransitHops,
       [n IN nodes(p) | n.name] AS transitSubstations,
       [r IN relationships(p) | r.source] AS dataSources;
