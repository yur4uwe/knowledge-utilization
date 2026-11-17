// ==========================================
// Завантаження вузлів графа (MERGE для ідемпотентності)
// ==========================================

// 1. Підстанції (:Substation)
LOAD CSV WITH HEADERS FROM 'file:///nodes.csv' AS row
WITH row WHERE row.label = 'Substation'
MERGE (s:Substation {id: row.id})
ON CREATE SET
    s.name = row.name,
    s.type = row.type,
    s.voltageKV = toFloat(row.voltageKV),
    s.status = row.status
ON MATCH SET
    s.name = row.name,
    s.voltageKV = toFloat(row.voltageKV),
    s.status = row.status;

// 2. Генеруючі блоки (:GeneratingUnit)
LOAD CSV WITH HEADERS FROM 'file:///nodes.csv' AS row
WITH row WHERE row.label = 'GeneratingUnit'
MERGE (g:GeneratingUnit {id: row.id})
ON CREATE SET
    g.name = row.name,
    g.type = row.type,
    g.voltageKV = toFloat(row.voltageKV),
    g.capacityMW = toFloat(row.capacityMW),
    g.status = row.status,
    g.dispatchable = (row.dispatchable = 'true')
ON MATCH SET
    g.name = row.name,
    g.capacityMW = toFloat(row.capacityMW),
    g.dispatchable = (row.dispatchable = 'true');

// 3. Накопичувачі енергії (:EnergyStorage)
LOAD CSV WITH HEADERS FROM 'file:///nodes.csv' AS row
WITH row WHERE row.label = 'EnergyStorage'
MERGE (st:EnergyStorage {id: row.id})
ON CREATE SET
    st.name = row.name,
    st.type = row.type,
    st.voltageKV = toFloat(row.voltageKV),
    st.capacityMW = toFloat(row.capacityMW),
    st.status = row.status
ON MATCH SET
    st.name = row.name,
    st.capacityMW = toFloat(row.capacityMW),
    st.status = row.status;

// 4. Лінії передачі (:TransmissionLine)
LOAD CSV WITH HEADERS FROM 'file:///nodes.csv' AS row
WITH row WHERE row.label = 'TransmissionLine'
MERGE (l:TransmissionLine {id: row.id})
ON CREATE SET
    l.name = row.name,
    l.type = row.type,
    l.voltageKV = toFloat(row.voltageKV),
    l.status = row.status
ON MATCH SET
    l.name = row.name,
    l.voltageKV = toFloat(row.voltageKV);

// 5. Трансформатори (:Transformer)
LOAD CSV WITH HEADERS FROM 'file:///nodes.csv' AS row
WITH row WHERE row.label = 'Transformer'
MERGE (t:Transformer {id: row.id})
ON CREATE SET
    t.name = row.name,
    t.type = row.type,
    t.voltageKV = toFloat(row.voltageKV),
    t.dgaH2Ppm = toFloat(row.dgaH2Ppm),
    t.dgaC2H2Ppm = toFloat(row.dgaC2H2Ppm),
    t.status = row.status
ON MATCH SET
    t.name = row.name,
    t.dgaH2Ppm = toFloat(row.dgaH2Ppm),
    t.dgaC2H2Ppm = toFloat(row.dgaC2H2Ppm),
    t.status = row.status;

// 6. Пристрої РЗА (:ProtectionDevice)
LOAD CSV WITH HEADERS FROM 'file:///nodes.csv' AS row
WITH row WHERE row.label = 'ProtectionDevice'
MERGE (p:ProtectionDevice {id: row.id})
ON CREATE SET
    p.name = row.name,
    p.protectionType = row.type,
    p.tripTimeMS = toInteger(toFloat(row.dgaH2Ppm)),
    p.status = row.status
ON MATCH SET
    p.name = row.name,
    p.tripTimeMS = toInteger(toFloat(row.dgaH2Ppm));

// 7. Аварійні події (:FaultEvent)
LOAD CSV WITH HEADERS FROM 'file:///nodes.csv' AS row
WITH row WHERE row.label = 'FaultEvent'
MERGE (f:FaultEvent {id: row.id})
ON CREATE SET
    f.name = row.name,
    f.eventType = row.type,
    f.faultCurrentKA = toFloat(row.faultCurrentKA),
    f.gridFrequencyHz = toFloat(row.gridFrequencyHz),
    f.status = row.status
ON MATCH SET
    f.name = row.name,
    f.gridFrequencyHz = toFloat(row.gridFrequencyHz);

// 8. Споживачі потужності (:PowerConsumer)
LOAD CSV WITH HEADERS FROM 'file:///nodes.csv' AS row
WITH row WHERE row.label = 'PowerConsumer'
MERGE (c:PowerConsumer {id: row.id})
ON CREATE SET
    c.name = row.name,
    c.type = row.type,
    c.voltageKV = toFloat(row.voltageKV),
    c.demandMW = toFloat(row.demandMW),
    c.status = row.status
ON MATCH SET
    c.name = row.name,
    c.demandMW = toFloat(row.demandMW);
