// Аналіз впливу 1 (Impact Analysis, глибина >= 3):
// Оцінка каскадного ризику відключення аварійної ЛЕП 750 кВ:
// Шлях: (FaultEvent) -> (TransmissionLine) -> (Substation) -> (PowerConsumer | Secondary Substation)
MATCH path = (fault:FaultEvent {id: 'ShortCircuit_Fault_Line750'})
             -[:AFFECTS_ASSET]->(line:TransmissionLine)
             <-[:CONNECTED_TO]-(sub:Substation)
             -[:FEEDS_LOAD|CONNECTED_TO*1..3]->(affected)
WHERE affected <> sub AND affected <> line
WITH line, sub, affected, length(path) AS impactDepth, labels(affected)[0] AS affectedType
RETURN line.name AS initialTrippedLine,
       sub.name AS immediateSubstation,
       impactDepth,
       affectedType,
       affected.name AS atRiskEntityName,
       coalesce(affected.demandMW, affected.voltageKV) AS metricValue
ORDER BY impactDepth ASC, affectedType DESC;
