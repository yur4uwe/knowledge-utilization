# Звіт: Порівняння SPARQL та Cypher і конвеєр Text-to-Cypher

## 1. Порівняльне виконання 5 контрольних питань (C1)

Відібрано 5 репрезентативних запитань із ЛР 8 (SPARQL у триплсторі Apache Jena Fuseki) та ЛР 9 (Cypher у СУБД Neo4j 5.x). Результати зіставлено за повнотою, синтаксисом та семантичною еквівалентністю.

---

### Питання 1 (CQ1). Генерація та накопичувачі на ПС 750 кВ «Вінницька»
* **SPARQL (ЛР 8):**
```sparql
PREFIX : <http://www.semanticweb.org/ontologies/2026/energy-system#>
SELECT ?asset ?label ?powerMW ?operatingStatus
WHERE {
    ?asset :suppliesPowerTo :Substation_Vinnytska_750kV .
    ?asset rdfs:label ?label .
    ?asset :hasRatedActivePowerMW ?powerMW .
    OPTIONAL { ?asset :hasOperatingStatus ?operatingStatus . }
}
ORDER BY DESC(?powerMW)
```
* **Cypher (ЛР 9):**
```cypher
MATCH (source)-[r:SUPPLIES_POWER_TO]->(s:Substation {id: 'SS_Vinnytska_750'})
RETURN source.name AS assetName, source.capacityMW AS powerMW, source.status AS operatingStatus
ORDER BY powerMW DESC;
```
* **Зіставлення результатів:** В обох випадках ідентифіковано повний перелік підключеної генерації та акумулювання (Дністровська ГАЕС, Ладижинська ТЕС, СЕС/ВЕС). У Cypher відсутня потреба у багаторазових префіксах просторів імен URI, а зв'язок є прямим типізованим ребром.

---

### Питання 2 (CQ2). Статистичний аналіз потужності за класами напруги
* **SPARQL (ЛР 8):**
```sparql
PREFIX : <http://www.semanticweb.org/ontologies/2026/energy-system#>
SELECT ?voltageKV (COUNT(?asset) AS ?unitCount) (SUM(?powerMW) AS ?totalPowerMW) (AVG(?powerMW) AS ?avgPowerMW)
WHERE {
    ?asset :hasVoltageLevelKV ?voltageKV .
    ?asset :hasRatedActivePowerMW ?powerMW .
}
GROUP BY ?voltageKV
HAVING (COUNT(?asset) >= 1)
ORDER BY DESC(?voltageKV)
```
* **Cypher (ЛР 9):**
```cypher
MATCH (g:GeneratingUnit)
WHERE g.voltageKV > 0
WITH g.voltageKV AS voltageClassKV, count(g) AS unitCount, sum(g.capacityMW) AS totalCapacityMW, avg(g.capacityMW) AS avgCapacityMW
RETURN voltageClassKV, unitCount, round(totalCapacityMW, 2) AS totalPowerMW, round(avgCapacityMW, 2) AS avgPowerMW
ORDER BY voltageClassKV DESC;
```
* **Зіставлення результатів:** Результати групування повністю збігаються (класи 750 кВ, 330 кВ, 150 кВ, 110 кВ). У Cypher проекція `WITH` забезпечує більш гнучкий проміжний конвеєр обчислень перед фільтрацією та сортуванням.

---

### Питання 3 (CQ3). Аварійне замикання та спрацювання релейного захисту
* **SPARQL (ЛР 8):**
```sparql
PREFIX : <http://www.semanticweb.org/ontologies/2026/energy-system#>
CONSTRUCT {
    ?fault :incidentAffectsAsset ?protectedAsset ;
           :recordedFaultCurrentKA ?faultCurrent ;
           :clearedByAction ?action ;
           :protectionTripTimeMS ?tripTime .
}
WHERE {
    ?fault a :ShortCircuitFault ; :hasFaultCurrentKA ?faultCurrent ; :triggers ?action .
    ?action a :RelayProtectionAction ; :protects ?protectedAsset ; :hasTripTimeMS ?tripTime .
}
```
* **Cypher (ЛР 9):**
```cypher
MATCH (fault:FaultEvent)-[:AFFECTS_ASSET]->(asset),
      (fault)-[:TRIGGERS_ACTION]->(prot:ProtectionDevice)
WHERE fault.eventType = 'ShortCircuit'
RETURN fault.id, fault.faultCurrentKA, asset.name, prot.name, prot.tripTimeMS;
```
* **Зіставлення результатів:** У SPARQL використано `CONSTRUCT` для формування нових триплетів на льоту, тоді як Cypher повертає табличний проекційний граф або самі сутності з властивостями ребер без необхідності розгортання RDF-серіалізації.

---

### Питання 4 (CQ6). Діагностика трансформаторів за розчиненими газами (DGA)
* **SPARQL (ЛР 8):**
```sparql
PREFIX : <http://www.semanticweb.org/ontologies/2026/energy-system#>
SELECT ?transformer ?h2Ppm ?c2h2Ppm ?status
WHERE {
    ?diag a :DissolvedGasAnalysis ;
          :protects ?transformer ;
          :hasHydrogenConcentrationPPM ?h2Ppm ;
          :hasAcetyleneConcentrationPPM ?c2h2Ppm .
    ?transformer :hasOperatingStatus ?status .
    FILTER (?h2Ppm > 100.0 || ?c2h2Ppm > 5.0)
}
```
* **Cypher (ЛР 9):**
```cypher
MATCH (t:Transformer)-[:INSTALLED_AT]->(s:Substation)
WHERE t.dgaH2Ppm > 100.0 OR t.dgaC2H2Ppm > 5.0 OR t.status IN ['ALARM', 'WARNING']
RETURN t.name, s.name, t.dgaH2Ppm, t.dgaC2H2Ppm, t.status;
```
* **Зіставлення результатів:** Обидва запити безпомилково локалізують АТ-1 Західноукраїнської ПС із високим рівнем ацетилену (12.4 ppm) та водню (145 ppm). У Cypher дані діагностики збережено як властивості самого вузла `:Transformer`, що скорочує кількість з'єднань (JOINS) порівняно з RDF.

---

### Питання 5 (CQ7). Топологічний зв'язок між підстанціями
* **SPARQL (ЛР 8):**
```sparql
PREFIX : <http://www.semanticweb.org/ontologies/2026/energy-system#>
ASK {
    :Substation_Zakhidnoukrainska_750kV (:connectedTo|^:connectedTo)+ :Kyivska_Substation_750kV .
}
```
* **Cypher (ЛР 9):**
```cypher
MATCH (s1:Substation {id: 'SS_Zakhidnoukrainska_750'}), (s2:Substation {id: 'SS_Kyivska_750'})
MATCH p = shortestPath((s1)-[:CONNECTED_TO*..10]-(s2))
RETURN length(p) AS hopCount, [n IN nodes(p) | n.name] AS transitNodes;
```
* **Зіставлення результатів:** SPARQL через `ASK` повертає лише булевий прапорець `true`/`false`, не надаючи інформації про маршрут. Cypher повертає повноцінний граф шляху (`Path`), дозволяючи отримати точний перелік проміжних підстанцій, ліній та кількість переходів (довжина = 2 переходи через Вінницю).

---

## 2. Порівняльна таблиця характеристик SPARQL та Cypher (C2, $\ge 5$ критеріїв)

| Критерій порівняння | SPARQL (W3C Standard) | Cypher (Neo4j / openCypher / GQL) | Висновок для інженерії знань |
| :--- | :--- | :--- | :--- |
| **1. Читабельність та ергономіка** | Вербальний синтаксис на основі трійок суб'єкт-предикат-об'єкт. Обов'язкові довгі префікси просторів імен (`PREFIX : <...>`). | Візуальний ASCII-art синтаксис: `(вузол)-[:ЗВ'ЯЗОК]->(вузол)`. Легко сприймається людиною. | Cypher значно інтуїтивніший для читання та швидкого написання. |
| **2. Лаконічність (довжина коду)** | Більша довжина запиту через потребу декларування префіксів та проміжних змінних для кожного літерала. | На 30–50% коротший текст запитів завдяки збереженню атрибутів безпосередньо у властивостях вузлів/ребер. | Менший обсяг коду та легша підтримка запитів. |
| **3. Пошук шляхів та топологія** | Обмежений виразністю property paths (`/`, `+`, `*`). Не повертає сам об'єкт шляху та проміжні ребра (тільки кінці). | Повноцінна підтримка графових шляхів (`Path`), функцій `shortestPath()`, `allShortestPaths()`, `nodes(path)`. | Cypher на порядок потужніший для мережевих топологічних задач. |
| **4. Швидкість виконання (Latency)** | Apache Jena Fuseki: ~9–330 мс (залежно від структури запиту та декартових добутків). | Neo4j Bolt Driver: ~3–15 мс при використанні індексів схеми та графового рушія без JOINS. | Neo4j перевершує за швидкістю в операціях глибокого обходу графа. |
| **5. Семантика та контроль схеми** | Відкритий світ (OWA), федеративні запити `SERVICE`, глобальні URI, валідація через SHACL. | Закритий світ (CWA), локальні ідентифікатори, вбудовані унікальні обмеження та індекси на рівні СУБД. | RDF кращий для відкритих інтеграцій (Wikidata); Neo4j кращий для локальних транзакційних баз знань. |

---

## 3. Конвеєр Text-to-Cypher та захисні бар'єри (C3)

Реалізовано оцінювальний конвеєр у [tests/eval_t2c.py](tests/eval_t2c.py) для 15 тестових запитань ([tests/t2c.jsonl](tests/t2c.jsonl)).
Конвеєр містить багаторівневі захисні механізми (Guardrails):
1. **Read-only роль:** семантичний фільтр, що автоматично блокує запити, які містять мутаційні оператори `CREATE`, `MERGE`, `SET`, `DELETE`, `REMOVE`, `DROP`, `ALTER`.
2. **Схемна верифікація (Schema Adherence):** перевірка всіх використаних у підказці міток та типів зв'язків за білим списком дозволених сутностей моделі.
3. **Обмеження вибірки (Safety LIMIT):** автоматична перевірка та ін'єкція `LIMIT 50` для запобігання вичерпанню пам'яті клієнта при випадковому формуванні декартового добутку.

---

## 4. Метрики та аналіз помилок генерації (C4)

### 4.1. Зведені результати оцінювання

| Версія конвеєра | Конфігурація підказки | Schema Accuracy | Execution Accuracy |
| :--- | :--- | :---: | :---: |
| **V1 (Baseline)** | Загальна підказка без опису схеми | **73.3%** (11/15) | **73.3%** (11/15) |
| **V2 (Refined)** | Повний опис міток і зв'язків + read-only роль + LIMIT | **100.0%** (15/15) | **100.0%** (15/15) |

### 4.2. Аналіз 3 типових помилок базової моделі (V1)
1. **Помилка 1 (Q02 — Галюцинація неіснуючих міток та зв'язків):**
   * *Згенеровано:* `MATCH (g:PowerPlant)-[:DELIVERS_POWER]->(s:Substation) ...`
   * *Причина:* Модель використала загальномовні назви замість формальної схеми (`:GeneratingUnit` та `:SUPPLIES_POWER_TO`).
   * *Усунення у V2:* Явна подача дозволених пар «мітка–зв'язок» у системному промпті усунула галюцинації.
2. **Помилка 2 (Q03 — Невірне ім'я числової властивості):**
   * *Згенеровано:* `MATCH (s:SolarStation) RETURN sum(s.power)`
   * *Причина:* Використання вигаданої назви поля `power` замість інженерного стандарту моделі `capacityMW`.
   * *Усунення у V2:* Вказівка ключових числових властивостей у промпті (`capacityMW`, `voltageKV`, `demandMW`).
3. **Помилка 3 (Q06 — Пропуск проміжного вузла ланцюжка захисту):**
   * *Згенеровано:* `MATCH (f:FaultEvent)-[:ACTIVATES]->(st:Storage)`
   * *Причина:* Модель пропустила обов'язкову фізичну ланку — пристрій автоматики `:ProtectionDevice`.
   * *Усунення у V2:* Опис причинно-наслідкового ланцюга `(FaultEvent)-[:TRIGGERS_ACTION]->(ProtectionDevice)-[:ACTIVATES_STORAGE]->(EnergyStorage)`.
