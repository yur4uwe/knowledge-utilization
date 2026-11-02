# Звіт про виконання та оптимізацію SPARQL-запитів до CQ

## 1. Загальний огляд
Усі 8 контрольних компетентнісних запитань (KQ1–KQ8) з предметної області «Управління енергетичними системами» були формалізовані у вигляді SPARQL-запитів і виконані над датасетом `/energy` у триплсторі Apache Jena Fuseki. Запити покривають повний спектр синтаксичних конструкцій стандарту SPARQL 1.1: `SELECT`, `ASK`, `CONSTRUCT`, агрегації (`GROUP BY`, `HAVING`, `COUNT`, `SUM`, `AVG`), `OPTIONAL`, `FILTER`, property paths (`+`, `*`, `/`, `^`), а також федеративні запити (`SERVICE`).

---

## 2. Специфікація запитів, результати та інтерпретація (C1, C2)

### Запит 1 (KQ1). Генерація та накопичувачі на ПС 750 кВ «Вінницька»
- **Файл:** `queries/q01_kq1_generation_by_substation.rq`
- **Конструкції:** `SELECT`, `OPTIONAL`, `ORDER BY`
- **Компетентнісне питання:** Які електростанції та накопичувачі підключені до підстанції і скільки МВт вони видають?
- **Текст запиту:**
```sparql
PREFIX : <http://www.semanticweb.org/ontologies/2026/energy-system#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?asset ?label ?powerMW ?operatingStatus
WHERE {
    ?asset :suppliesPowerTo :Substation_Vinnytska_750kV .
    ?asset rdfs:label ?label .
    ?asset :hasRatedActivePowerMW ?powerMW .
    OPTIONAL {
        ?asset :hasOperatingStatus ?operatingStatus .
    }
}
ORDER BY DESC(?powerMW)
```
- **Результат виконання:**
| Активи (?asset) | Назва (?label) | Потужність (?powerMW) | Експлуатаційний стан (?operatingStatus) |
| :--- | :--- | :--- | :--- |
| `:Dniester_PSPS_Unit` | Дністровська ГАЕС, Гідроагрегат №1 | 324.0 МВт | `STANDBY_SPINNING_RESERVE` |
| `:Pokrovska_Solar_SES` | Покровська СЕС | 240.0 МВт | `IN_SERVICE_VARIABLE` |
| `:Kakhovka_Solar_SES` | Каховська СЕС | 120.0 МВт | `IN_SERVICE_VARIABLE` |
| `:Zaporizhia_Wind_WPP` | Запорізька ВЕС | 98.0 МВт | `IN_SERVICE_VARIABLE` |
| `:Dnipro_HPP_Unit1` | Дніпровська ГЕС, Гідроагрегат №1 | 75.0 МВт | `IN_SERVICE_LOAD_FOLLOWING` |
- **Інтерпретація:** До підстанції підключено 5 об'єктів генерації та зберігання різних типів (ГАЕС, СЕС, ВЕС, ГЕС). Найпотужнішим маневровим джерелом у вузлі є Дністровська ГАЕС (324 МВт), яка перебуває в гарячому обертовому резерві.

---

### Запит 2 (KQ2). Статистичний аналіз потужності за класами напруги
- **Файл:** `queries/q02_kq2_high_voltage_summary.rq`
- **Конструкції:** `SELECT`, `GROUP BY`, `COUNT`, `SUM`, `AVG`, `HAVING`
- **Компетентнісне питання:** Яка сумарна та середня потужність обладнання різних класів напруги?
- **Текст запиту:**
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
- **Результат виконання:**
| Клас напруги (?voltageKV) | К-ть одиниць (?unitCount) | Сумарна потужність (?totalPowerMW) | Середня потужність (?avgPowerMW) |
| :--- | :--- | :--- | :--- |
| 750.0 кВ | 3 | 3000.0 МВт | 1000.0 МВт |
| 330.0 кВ | 4 | 1239.0 МВт | 309.75 МВт |
| 150.0 кВ | 2 | 218.0 МВт | 109.0 МВт |
| 110.0 кВ | 2 | 430.0 МВт | 215.0 МВт |
- **Інтерпретація:** Магістральна мережа 750 кВ зосереджує найбільшу одиничну та сумарну потужність (Хмельницька АЕС, автотрансформатори зв'язку), тоді як розподільчі мережі 330–110 кВ інтегрують маневрову та відновлювану генерацію меншої потужності.

---

### Запит 3 (KQ7). Перевірка транзитного зв'язку між підстанціями (ASK)
- **Файл:** `queries/q03_kq7_substation_connectivity_ask.rq`
- **Конструкції:** `ASK`, Property Path `((:connectedTo|^:connectedTo)+)`
- **Компетентнісне питання:** Чи є прямий або транзитний електричний зв'язок між підстанціями «Західноукраїнська» та «Київська»?
- **Текст запиту:**
```sparql
PREFIX : <http://www.semanticweb.org/ontologies/2026/energy-system#>

ASK {
    :Substation_Zakhidnoukrainska_750kV (:connectedTo|^:connectedTo)+ :Kyivska_Substation_750kV .
}
```
- **Результат виконання:** `true`.
- **Інтерпретація:** Топологічний шлях існує через транзит: `ПС Західноукраїнська 750` -> `ПЛ 750 кВ Західна-Вінницька` -> `ПС Вінницька 750` -> `ПЛ 750 кВ Вінницька-Київська` -> `ПС Київська 750`.

---

### Запит 4 (KQ3). Граф аварійних інцидентів та спрацювання захисту (CONSTRUCT)
- **Файл:** `queries/q04_kq3_fault_protection_construct.rq`
- **Конструкції:** `CONSTRUCT`
- **Компетентнісне питання:** Де саме сталося коротке замикання і який захист після цього спрацював?
- **Текст запиту:**
```sparql
PREFIX : <http://www.semanticweb.org/ontologies/2026/energy-system#>

CONSTRUCT {
    ?fault :incidentAffectsAsset ?protectedAsset ;
           :recordedFaultCurrentKA ?faultCurrent ;
           :clearedByAction ?action ;
           :protectionTripTimeMS ?tripTime .
}
WHERE {
    ?fault a :ShortCircuitFault ;
           :hasFaultCurrentKA ?faultCurrent ;
           :triggers ?action .
    ?action a :RelayProtectionAction ;
            :protects ?protectedAsset ;
            :hasTripTimeMS ?tripTime .
}
```
- **Результат виконання:** Згенеровано новий граф зв'язків:
```turtle
:ShortCircuit_Fault_Line750
    :incidentAffectsAsset   :OverheadLine_Zakhidna_Vinnytska_750kV ;
    :recordedFaultCurrentKA "24.5"^^xsd:double ;
    :clearedByAction        :RelayProtection_Trip_Line750 ;
    :protectionTripTimeMS   65 .
```
- **Інтерпретація:** Прямий синтез нової структури знань зв'язує зафіксовану аварію безпосередньо з пошкодженою ділянкою лінії та часом локалізації релейним захистом (65 мс).

---

### Запит 5 (KQ6). Діагностика трансформаторів за розчиненими газами (FILTER)
- **Файл:** `queries/q05_kq6_dga_gas_analysis_filter.rq`
- **Конструкції:** `SELECT`, `FILTER`
- **Компетентнісне питання:** У яких трансформаторів аналіз масла показує проблеми або перегрів?
- **Текст запиту:**
```sparql
PREFIX : <http://www.semanticweb.org/ontologies/2026/energy-system#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?transformer ?label ?h2Ppm ?c2h2Ppm ?status
WHERE {
    ?diag a :DissolvedGasAnalysis ;
          :protects ?transformer ;
          :hasHydrogenConcentrationPPM ?h2Ppm ;
          :hasAcetyleneConcentrationPPM ?c2h2Ppm .
    ?transformer rdfs:label ?label ;
                 :hasOperatingStatus ?status .
    FILTER (?h2Ppm > 100.0 || ?c2h2Ppm > 5.0)
}
```
- **Результат виконання:**
| Трансформатор | Назва | H2 (ppm) | C2H2 (ppm) | Стан |
| :--- | :--- | :--- | :--- | :--- |
| `:Autotransformer_AT1_Zakhidna` | Автотрансформатор АТ-1 750/330 кВ | 145.0 | 12.4 | `IN_SERVICE_LOADED` |
- **Інтерпретація:** Виявлено критичне перевищення концентрації ацетилену (12.4 ppm при нормі < 5 ppm) та водню (145 ppm при нормі < 100 ppm), що свідчить про наявність дугового розряду високої енергії в баку автотрансформатора АТ-1.

---

### Запит 6 (KQ4). Пошук резервів частоти за ланцюжком ініціації (Property Path Sequence)
- **Файл:** `queries/q06_kq4_frequency_storage_path.rq`
- **Конструкції:** `SELECT`, Property Path `(:triggers/:activates)`
- **Компетентнісне питання:** Які накопичувачі енергії запускаються при відхиленні частоти?
- **Текст запиту:**
```sparql
PREFIX : <http://www.semanticweb.org/ontologies/2026/energy-system#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?event ?freqHz ?storage ?storageLabel ?powerMW
WHERE {
    ?event a :FrequencyDeviation ;
           :hasGridFrequencyHz ?freqHz ;
           (:triggers/:activates) ?storage .
    ?storage rdfs:label ?storageLabel ;
             :hasRatedActivePowerMW ?powerMW .
}
```
- **Результат виконання:**
| Подія (?event) | Частота (?freqHz) | Накопичувач (?storage) | Назва (?storageLabel) | Потужність (?powerMW) |
| :--- | :--- | :--- | :--- | :--- |
| `:Frequency_Drop_Event_50Hz` | 49.88 Гц | `:Dniester_PSPS_Unit` | Дністровська ГАЕС, Гідроагрегат №1 | 324.0 МВт |
- **Інтерпретація:** При падінні частоти до 49.88 Гц алгоритм FCR через скорочений предикатний шлях ініціює запуск гідроагрегату Дністровської ГАЕС на 324 МВт.

---

### Запит 7 (KQ8). Оптимізація запиту передиспатчеризації (C3)
- **Файли:** `queries/q07_kq8_redispatch_unoptimized.rq` та `queries/q07_kq8_redispatch_optimized.rq`
- **Компетентнісне питання:** Яким енергоблокам необхідно скоригувати генерацію при перевантаженні магістральної мережі?

**Порівняння планів виконання та структури запиту:**
1. **Неоптимізований запит:**
   - Використовує вільні змінні шаблону `?gen ?p1 ?o1` та `?substation ?p2 ?o2`, спричиняючи декартовий перетин множин і сканування повного графа triples.
   - Пізній фільтр через рядковий `REGEX(STR(?substation), "750kV", "i")`.
2. **Оптимізований запит:**
   - Задає жорстку типізацію класу `:Substation` та ранній push-down фільтр за типізованим предикатом `:hasVoltageLevelKV 750.0`.
   - Обмежує простір пошуку виключно індексованими твердженнями зв'язку `:suppliesPowerTo`.

**Результати бенчмаркінгу (30 ітерацій на Apache Jena Fuseki):**
| Метрика | Неоптимізований | Оптимізований | Покращення |
| :--- | :--- | :--- | :--- |
| **Середній час виконання** | **333.68 мс** | **9.54 мс** | **34.97x (прискорення на 97.1%)** |

---

### Запит 8. Федеративний запит до DBpedia (C1, Результат 5)
- **Файл:** `queries/q08_federated_external_query.rq`
- **Конструкції:** `SELECT`, `VALUES`, `SERVICE <https://dbpedia.org/sparql>`, `OPTIONAL`, `FILTER`
- **Призначення:** Збагачення локальних сутностей (АЕС, ГЕС, ТЕС) географічними координатами та встановленою потужністю з глобального графа DBpedia.
- **Результат виконання:**
| Локальний актив | Локальна потужність | Зовнішній ресурс DBpedia | Широта (lat) | Довгота (long) | Зовнішня потужність (W) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `:KhmelnytskyiNPP_Unit1` | 1000.0 МВт | `dbr:Khmelnytskyi_Nuclear_Power_Plant` | 50.3014 | 26.6497 | 2 000 000 000 Вт |
| `:Dnipro_HPP_Unit1` | 75.0 МВт | `dbr:Dnieper_Hydroelectric_Station` | 47.8692 | 35.0869 | — |
| `:Trypilska_ThermalPowerPlant` | 600.0 МВт | `dbr:Trypilska_thermal_power_plant` | 50.1351 | 30.7481 | — |

---

## 3. Ручна перевірка коректності запитів (C4)
Щонайменше 3 запити верифіковані вручну проти еталонного очікування онтології:
1. **Запит 1 (KQ1):** Очікувався перелік усіх активів, що видають струм на ПС «Вінницька» (5 об'єктів). Фактичний результат точно збігся: Дністровська ГАЕС, Покровська СЕС, Каховська СЕС, Запорізька ВЕС, Дніпровська ГЕС.
2. **Запит 3 (KQ7):** Очікувався булевий результат `true` наявності транзитного коридору 750 кВ між Львовом/Заходом та Києвом через Вінницю. Отримано `true`.
3. **Запит 5 (KQ6):** Очікувалося виявлення саме автотрансформатора АТ-1 на ПС «Західноукраїнська», для якого в онтології змодельовано перевищення порогів водню та ацетилену. Отримано саме `:Autotransformer_AT1_Zakhidna`.
