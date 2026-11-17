// CQ4: Які накопичувачі енергії запускаються при відхиленні частоти?
// Конструкції: MATCH path traversal, WHERE, RETURN
MATCH (event:FaultEvent {eventType: 'FrequencyDeviation'})
MATCH (event)-[:TRIGGERS_ACTION]->(prot:ProtectionDevice)
MATCH (prot)-[:ACTIVATES_STORAGE]->(storage:EnergyStorage)
RETURN event.id AS eventId,
       event.gridFrequencyHz AS recordedFrequencyHz,
       prot.name AS triggeringAutomation,
       storage.id AS storageId,
       storage.name AS storageName,
       storage.type AS storageType,
       storage.capacityMW AS primaryReserveMW,
       storage.status AS operatingStatus;
