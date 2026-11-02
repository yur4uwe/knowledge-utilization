# Журнал завантаження RDF-даних у триплстор (Load Log)

## 1. Вхідні параметри завантаження
- **Дата та час завантаження:** 2026-11-02 17:36:15 UTC
- **Триплстор:** Apache Jena Fuseki (`stain/jena-fuseki:latest`, Docker)
- **Датасет:** `/energy`
- **Тип сховища:** In-Memory Dataset (Graph Store Protocol RW)
- **Версія онтології:** 1.0.0 (`owl:versionInfo "1.0.0"`)
- **Вхідний файл:** Turtle (`data/kb.ttl`)
- **Базова онтологія:** розширення графа з ЛР7 до 26 іменованих індивідів (магістральні ПС 750 кВ, ПЛ, генерація різних типів, споживачі, релейний захист)

## 2. Узгоджена система префіксів (C3)
```turtle
@prefix : <http://www.semanticweb.org/ontologies/2026/energy-system#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix xml: <http://www.w3.org/XML/1998/namespace> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix cim: <http://iec.ch/TC57/CIM#> .
```

## 3. Протокол завантаження та валідація (C1, C2)

1. **Валідація синтаксису графа через `rdflib`:**
   - Бібліотека: `rdflib 7.6.0`
   - Результат парсингу: валідний граф, синтаксичні помилки відсутні.
   - Зафіксовано триплетів: **565** (вимога критерію C1: ≥ 300 триплетів).
   - Іменованих індивідів (`owl:NamedIndividual`): **26**.

2. **Завантаження через HTTP Graph Store Protocol:**
   ```bash
   curl -u admin:admin -s -w "\nHTTP Status: %{http_code}\n" \
     -X POST --header "Content-Type: text/turtle; charset=utf-8" \
     --data-binary @data/kb.ttl http://localhost:3030/energy/data
   ```
   **Відповідь Fuseki:**
   ```json
   {
     "count" : 565,
     "tripleCount" : 565,
     "quadCount" : 0
   }
   HTTP Status: 200
   ```

3. **Верифікаційний SPARQL-запит підрахунку триплетів (COUNT):**
   ```sparql
   SELECT (COUNT(*) AS ?totalTriples) WHERE { ?s ?p ?o }
   ```
   **Результат виконання у Fuseki:**
   ```json
   {
     "head": { "vars": [ "totalTriples" ] },
     "results": {
       "bindings": [
         {
           "totalTriples": {
             "type": "literal",
             "datatype": "http://www.w3.org/2001/XMLSchema#integer",
             "value": "565"
           }
         }
       ]
     }
   }
   ```
   Кількість триплетів у датасеті після завантаження: **565**.

## 4. Експорт у формат JSON-LD (C4)
- **Файл артефакту:** `data/kb.jsonld`
- **Розмір:** 78.5 КБ
- **Охоплені сутності:** 26 іменованих індивідів:
  - Генерація: `KhmelnytskyiNPP_Unit1`, `Trypilska_ThermalPowerPlant`, `Dnipro_HPP_Unit1`, `Pokrovska_Solar_SES`, `Kakhovka_Solar_SES`, `Zaporizhia_Wind_WPP`.
  - Накопичувачі: `Dniester_PSPS_Unit`.
  - Підстанції та лінії: `Substation_Zakhidnoukrainska_750kV`, `Substation_Vinnytska_750kV`, `Kyivska_Substation_750kV`, `OverheadLine_Zakhidna_Vinnytska_750kV`, `OverheadLine_Vinnytska_Kyivska_750kV`.
  - Трансформатори: `Autotransformer_AT1_Zakhidna`, `Transformer_T1_Kyivska`.
  - Споживачі: `Lviv_Industrial_Consumer`, `Kyiv_Residential_Consumer`.
  - Суб'єкти управління: `Ukrenergo_National_TSO`, `Dispatcher_Duty_Shift`.
  - Події та процеси: `ShortCircuit_Fault_Line750`, `Line_Overload_Vinnytska_330kV`, `Frequency_Drop_Event_50Hz`, `Insulation_Defect_AT1`, `RelayProtection_Trip_Line750`, `Redispatch_Contingency_Process`, `FCR_Primary_Frequency_Response`, `DGA_Oil_Diagnostic_AT1`.
- **Зворотна верифікація:** Десеріалізація через `rdflib` підтвердила повну відповідність структури та кількості триплетів (565 триплетів).
