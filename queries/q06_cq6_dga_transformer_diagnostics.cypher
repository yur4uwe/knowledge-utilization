// CQ6: У яких трансформаторів аналіз масла (DGA) показує проблеми або перегрів?
// Конструкції: MATCH, WHERE (комплексні логічні предикати), RETURN, ORDER BY
MATCH (t:Transformer)-[r:INSTALLED_AT]->(s:Substation)
WHERE t.dgaH2Ppm > 100.0 OR t.dgaC2H2Ppm > 5.0 OR t.status IN ['ALARM', 'WARNING']
RETURN t.id AS transformerId,
       t.name AS transformerName,
       s.name AS substationLocation,
       t.voltageKV AS ratedPrimaryKV,
       t.dgaH2Ppm AS hydrogenConcentrationPPM,
       t.dgaC2H2Ppm AS acetyleneConcentrationPPM,
       t.status AS diagnosisStatus
ORDER BY t.dgaC2H2Ppm DESC, t.dgaH2Ppm DESC;
