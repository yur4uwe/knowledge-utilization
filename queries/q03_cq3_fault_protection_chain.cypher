// CQ3: Де саме сталося коротке замикання і який захист після цього спрацював?
// Конструкції: MATCH multi-hop, WHERE, RETURN
MATCH (fault:FaultEvent)-[r1:AFFECTS_ASSET]->(asset)
MATCH (fault)-[r2:TRIGGERS_ACTION]->(prot:ProtectionDevice)
WHERE fault.eventType = 'ShortCircuit'
RETURN fault.id AS faultId,
       fault.name AS faultDescription,
       fault.faultCurrentKA AS faultCurrentKA,
       labels(asset)[0] AS affectedAssetType,
       asset.name AS affectedAssetName,
       prot.name AS protectionDeviceName,
       prot.protectionType AS relayType,
       prot.tripTimeMS AS tripTimeMS
ORDER BY faultCurrentKA DESC;
