// CQ8: Яким диспетчеризованим енергоблокам необхідно скоригувати генерацію при відключенні магістральної лінії (передиспатчеризація)?
// Конструкції: MATCH, WHERE, WITH, collect(), sum(), ORDER BY
MATCH (fault:FaultEvent {id: 'ShortCircuit_Fault_Line750'})-[:AFFECTS_ASSET]->(line:TransmissionLine)
MATCH (line)<-[:CONNECTED_TO]-(sub:Substation)
MATCH (gen:GeneratingUnit)-[:SUPPLIES_POWER_TO]->(sub)
WHERE gen.dispatchable = true
WITH line, sub, gen
RETURN line.name AS trippedLine,
       sub.name AS connectedSubstation,
       gen.id AS generatorId,
       gen.name AS generatorName,
       gen.type AS generationType,
       gen.capacityMW AS currentOutputMW
ORDER BY currentOutputMW DESC;
