// ==========================================
// 1. Унікальні обмеження цілісності (Uniqueness Constraints, >= 2)
// ==========================================

CREATE CONSTRAINT constraint_substation_id IF NOT EXISTS
FOR (s:Substation) REQUIRE s.id IS UNIQUE;

CREATE CONSTRAINT constraint_genunit_id IF NOT EXISTS
FOR (g:GeneratingUnit) REQUIRE g.id IS UNIQUE;

CREATE CONSTRAINT constraint_line_id IF NOT EXISTS
FOR (l:TransmissionLine) REQUIRE l.id IS UNIQUE;

CREATE CONSTRAINT constraint_transformer_id IF NOT EXISTS
FOR (t:Transformer) REQUIRE t.id IS UNIQUE;

CREATE CONSTRAINT constraint_storage_id IF NOT EXISTS
FOR (st:EnergyStorage) REQUIRE st.id IS UNIQUE;

CREATE CONSTRAINT constraint_protection_id IF NOT EXISTS
FOR (p:ProtectionDevice) REQUIRE p.id IS UNIQUE;

CREATE CONSTRAINT constraint_fault_id IF NOT EXISTS
FOR (f:FaultEvent) REQUIRE f.id IS UNIQUE;

CREATE CONSTRAINT constraint_consumer_id IF NOT EXISTS
FOR (c:PowerConsumer) REQUIRE c.id IS UNIQUE;

// ==========================================
// 2. Індекси пошуку та оптимізації (Indexes, >= 2)
// ==========================================

CREATE INDEX index_substation_voltage IF NOT EXISTS
FOR (s:Substation) ON (s.voltageKV);

CREATE INDEX index_genunit_capacity IF NOT EXISTS
FOR (g:GeneratingUnit) ON (g.capacityMW);

CREATE INDEX index_line_voltage IF NOT EXISTS
FOR (l:TransmissionLine) ON (l.voltageKV);

CREATE INDEX index_transformer_status IF NOT EXISTS
FOR (t:Transformer) ON (t.status);

CREATE INDEX index_fault_type IF NOT EXISTS
FOR (f:FaultEvent) ON (f.eventType);
