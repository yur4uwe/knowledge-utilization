// ==========================================
// Завантаження зв'язків графа (MERGE для ідемпотентності)
// ==========================================

// 1. CONNECTED_TO
LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
WITH row WHERE row.type = 'CONNECTED_TO'
MATCH (a {id: row.start_id})
MATCH (b {id: row.end_id})
MERGE (a)-[r:CONNECTED_TO]->(b)
ON CREATE SET
    r.source = row.source,
    r.confidence = toFloat(row.confidence),
    r.validFrom = row.validFrom
ON MATCH SET
    r.confidence = toFloat(row.confidence);

// 2. SUPPLIES_POWER_TO
LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
WITH row WHERE row.type = 'SUPPLIES_POWER_TO'
MATCH (a {id: row.start_id})
MATCH (b {id: row.end_id})
MERGE (a)-[r:SUPPLIES_POWER_TO]->(b)
ON CREATE SET
    r.source = row.source,
    r.confidence = toFloat(row.confidence),
    r.validFrom = row.validFrom
ON MATCH SET
    r.confidence = toFloat(row.confidence);

// 3. INSTALLED_AT
LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
WITH row WHERE row.type = 'INSTALLED_AT'
MATCH (a {id: row.start_id})
MATCH (b {id: row.end_id})
MERGE (a)-[r:INSTALLED_AT]->(b)
ON CREATE SET
    r.source = row.source,
    r.confidence = toFloat(row.confidence),
    r.validFrom = row.validFrom
ON MATCH SET
    r.confidence = toFloat(row.confidence);

// 4. STEPS_VOLTAGE
LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
WITH row WHERE row.type = 'STEPS_VOLTAGE'
MATCH (a {id: row.start_id})
MATCH (b {id: row.end_id})
MERGE (a)-[r:STEPS_VOLTAGE]->(b)
ON CREATE SET
    r.source = row.source,
    r.confidence = toFloat(row.confidence),
    r.validFrom = row.validFrom
ON MATCH SET
    r.confidence = toFloat(row.confidence);

// 5. PROTECTS
LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
WITH row WHERE row.type = 'PROTECTS'
MATCH (a {id: row.start_id})
MATCH (b {id: row.end_id})
MERGE (a)-[r:PROTECTS]->(b)
ON CREATE SET
    r.source = row.source,
    r.confidence = toFloat(row.confidence),
    r.validFrom = row.validFrom
ON MATCH SET
    r.confidence = toFloat(row.confidence);

// 6. AFFECTS_ASSET
LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
WITH row WHERE row.type = 'AFFECTS_ASSET'
MATCH (a {id: row.start_id})
MATCH (b {id: row.end_id})
MERGE (a)-[r:AFFECTS_ASSET]->(b)
ON CREATE SET
    r.source = row.source,
    r.confidence = toFloat(row.confidence),
    r.validFrom = row.validFrom
ON MATCH SET
    r.confidence = toFloat(row.confidence);

// 7. TRIGGERS_ACTION
LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
WITH row WHERE row.type = 'TRIGGERS_ACTION'
MATCH (a {id: row.start_id})
MATCH (b {id: row.end_id})
MERGE (a)-[r:TRIGGERS_ACTION]->(b)
ON CREATE SET
    r.source = row.source,
    r.confidence = toFloat(row.confidence),
    r.validFrom = row.validFrom
ON MATCH SET
    r.confidence = toFloat(row.confidence);

// 8. ACTIVATES_STORAGE
LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
WITH row WHERE row.type = 'ACTIVATES_STORAGE'
MATCH (a {id: row.start_id})
MATCH (b {id: row.end_id})
MERGE (a)-[r:ACTIVATES_STORAGE]->(b)
ON CREATE SET
    r.source = row.source,
    r.confidence = toFloat(row.confidence),
    r.validFrom = row.validFrom
ON MATCH SET
    r.confidence = toFloat(row.confidence);

// 9. FEEDS_LOAD
LOAD CSV WITH HEADERS FROM 'file:///relationships.csv' AS row
WITH row WHERE row.type = 'FEEDS_LOAD'
MATCH (a {id: row.start_id})
MATCH (b {id: row.end_id})
MERGE (a)-[r:FEEDS_LOAD]->(b)
ON CREATE SET
    r.source = row.source,
    r.confidence = toFloat(row.confidence),
    r.validFrom = row.validFrom
ON MATCH SET
    r.confidence = toFloat(row.confidence);
