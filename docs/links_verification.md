# Верифікація зв'язків з відкритими графами знань (Linked Open Data)

## 1. Специфікація зв'язків із зовнішніми графами (C1, C2)
У файлі `data/links.ttl` визначено семантичні відповідники між сутностями локальної онтології та зовнішніми ресурсами Wikidata й DBpedia. Для кожного зв'язку задано предикат (`skos:exactMatch`, `skos:closeMatch`, `owl:sameAs`), рівень впевненості (0.0–1.0) та технічне обґрунтування.

| Локальна сутність | Зовнішній ресурс (Wikidata / DBpedia) | Тип зв'язку | Рівень впевненості | Обґрунтування відповідності |
| :--- | :--- | :--- | :--- | :--- |
| `:KhmelnytskyiNPP_Unit1` | `wd:Q1037144`<br>`dbr:Khmelnytskyi_Nuclear_Power_Plant` | `skos:closeMatch` | **0.92** | Локальна сутність описує окремий енергоблок №1 ВВЕР-1000, тоді як Wikidata позначає станційний комплекс загалом. Семантично це близький збіг (`skos:closeMatch`), а не повна тотожність одиниці. |
| `:Dniester_PSPS_Unit` | `wd:Q1153545`<br>`dbr:Dniester_Pumped_Storage_Power_Station` | `skos:closeMatch` | **0.90** | Оборотний гідроагрегат №1 належить до гідровузла Дністровської ГАЕС у Чернівецькій області. |
| `:Dnipro_HPP_Unit1` | `wd:Q738619`<br>`dbr:Dnieper_Hydroelectric_Station` | `skos:closeMatch` | **0.90** | Гідроагрегат є структурною частиною станції ДніпроГЕС (м. Запоріжжя). |
| `:Trypilska_ThermalPowerPlant` | `wd:Q12007778`<br>`dbr:Trypilska_thermal_power_plant` | `skos:exactMatch`<br>`owl:sameAs` | **0.99** | Повний збіг на рівні електростанції (м. Українка, Київська обл.) за типом станції, розташуванням і технологією. |
| `:Ukrenergo_National_TSO` | `wd:Q12132842`<br>`dbr:Ukrenergo` | `skos:exactMatch`<br>`owl:sameAs` | **1.00** | Повна організаційна тотожність оператора системи передачі України (НЕК «Укренерго»). |

---

## 2. Аналіз відхиленого зв'язку (C3)

- **Кандидат на зв'язування:**
  - Локальний актив: `:Pokrovska_Solar_SES` (Покровська СЕС, 240 МВт, сонячна фотоелектрична станція, Дніпропетровська обл.).
  - Зовнішній ресурс Wikidata: `wd:Q108882857` (Шахтоуправління «Покровське», Донецька обл.).
- **Рішення експерта:** **REJECTED (Відхилено)**
- **Рівень впевненості:** **0.05**
- **Технічне обґрунтування відхилення:**
  Лексичний пошук за назвою "Покровська / Pokrovska" повернув сутність `wd:Q108882857`. Порівняння атрибутів за рівнем верифікації V1 виявило розбіжності:
  1. *Класифікація:* `wd:Q108882857` є підприємством із видобутку вугілля (`Q828945`), тоді як локальний актив належить до `:SolarPowerPlant`.
  2. *Географічна прив'язка:* Шахтоуправління розташоване у м. Покровськ (Донецька обл.), а СЕС — поблизу м. Покров (Дніпропетровська обл.).
  3. *Енергетичний профіль:* Вугільна шахта є споживачем або видобувником викопного палива, а не сонячною електростанцією потужністю 240 МВт.
  Встановлення еквівалентності призвело б до помилкового логічного виведення.

---

## 3. Працюючий федеративний SPARQL-запит через зв'язки (C4)

Запит зчитує з `data/links.ttl` семантичні відповідники `skos:closeMatch` та `skos:exactMatch`, відбирає ресурси DBpedia та через `SERVICE` отримує географічні координати й англомовні мітки.

### Текст запиту:
```sparql
PREFIX : <http://www.semanticweb.org/ontologies/2026/energy-system#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX geo: <http://www.w3.org/2003/01/geo/wgs84_pos#>

SELECT ?localAsset ?localLabel ?externalEntity ?extLabel ?lat ?long
WHERE {
  ?localAsset (skos:closeMatch|skos:exactMatch) ?externalEntity .
  ?localAsset rdfs:label ?label .
  FILTER(STRSTARTS(STR(?externalEntity), "http://dbpedia.org/resource/"))
  SERVICE <https://dbpedia.org/sparql> {
    ?externalEntity rdfs:label ?extLabel .
    OPTIONAL {
      ?externalEntity geo:lat ?lat ;
                      geo:long ?long .
    }
    FILTER(LANG(?extLabel) = "en")
  }
}
```

### Фактичний результат виконання у Fuseki:

| Локальний актив | Назва (uk) | Зовнішній ресурс DBpedia | Англійська назва | Широта (lat) | Довгота (long) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `:KhmelnytskyiNPP_Unit1` | Хмельницька АЕС, Енергоблок №1 | `dbr:Khmelnytskyi_Nuclear_Power_Plant` | Khmelnytskyi Nuclear Power Plant | 50.3014 | 26.6497 |
| `:Dniester_PSPS_Unit` | Дністровська ГАЕС, Гідроагрегат №1 | `dbr:Dniester_Pumped_Storage_Power_Station` | Dniester Pumped Storage Power Station | 48.5133 | 27.4711 |
| `:Dnipro_HPP_Unit1` | Дніпровська ГЕС, Гідроагрегат №1 | `dbr:Dnieper_Hydroelectric_Station` | Dnieper Hydroelectric Station | 47.8692 | 35.0869 |
| `:Trypilska_ThermalPowerPlant` | Трипільська ТЕС | `dbr:Trypilska_thermal_power_plant` | Trypilska thermal power plant | 50.1351 | 30.7481 |
| `:Ukrenergo_National_TSO` | НЕК «Укренерго» | `dbr:Ukrenergo` | Ukrenergo | 50.4372 | 30.5283 |
