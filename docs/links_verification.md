# Верифікація зв'язків з відкритими графами знань (Linked Open Data)

## 1. Специфікація зв'язків із зовнішніми графами (C1, C2)
У файлі `data/links.ttl` встановлено зв'язки між сутностями локальної онтології та глобальними базами знань (Wikidata та DBpedia). Для кожного зіставлення визначено тип зв'язку (`skos:exactMatch`, `skos:closeMatch`, `owl:sameAs`), ступінь впевненості (Confidence Score) та детальне технічне обґрунтування.

| Локальна сутність | Зовнішній ресурс (Wikidata / DBpedia) | Тип зв'язку | Рівень впевненості | Обґрунтування відповідності |
| :--- | :--- | :--- | :--- | :--- |
| `:KhmelnytskyiNPP_Unit1` | `wd:Q1037144`<br>`dbr:Khmelnytskyi_Nuclear_Power_Plant` | `skos:closeMatch` | **0.92** | Локальна сутність моделює конкретний реакторний блок №1 ВВЕР-1000, тоді як Wikidata представляє весь інфраструктурний комплекс станції. Семантично це близький збіг (`skos:closeMatch`), а не повна тотожність одиниці. |
| `:Dniester_PSPS_Unit` | `wd:Q1153545`<br>`dbr:Dniester_Pumped_Storage_Power_Station` | `skos:closeMatch` | **0.90** | Оборотний гідроагрегат №1 відноситься до загального майнового комплексу Дністровської ГАЕС у Чернівецькій області. |
| `:Dnipro_HPP_Unit1` | `wd:Q738619`<br>`dbr:Dnieper_Hydroelectric_Station` | `skos:closeMatch` | **0.90** | Локальний гідроагрегат є компонентом історичної гідроелектростанції ДніпроГЕС у м. Запоріжжя. |
| `:Trypilska_ThermalPowerPlant` | `wd:Q12007778`<br>`dbr:Trypilska_thermal_power_plant` | `skos:exactMatch`<br>`owl:sameAs` | **0.99** | Повний ідентичний збіг на рівні електростанції (м. Українка, Київська обл.), збіг за потужністю та типом палива. |
| `:Ukrenergo_National_TSO` | `wd:Q12132842`<br>`dbr:Ukrenergo` | `skos:exactMatch`<br>`owl:sameAs` | **1.00** | Повна юридична та організаційна тотожність оператора системи передачі України (ДП «НЕК «Укренерго»). |

---

## 2. Аналіз відхиленого зв'язку (C3)

- **Кандидат на зв'язування:**
  - Локальна сутність: `:Pokrovska_Solar_SES` (Покровська СЕС, номінальна потужність 240 МВт, сонячна фотоелектрична станція у Дніпропетровській області).
  - Зовнішня сутність у Wikidata: `wd:Q108882857` (*Шахтоуправління «Покровське»*, раніше ВАТ Вугільна компанія «Шахта Красноармійська-Західна № 1»).
- **Рішення експерта:** **REJECTED (Відхилено)**
- **Рівень впевненості:** **0.05**
- **Технічне обґрунтування відхилення:**
  Під час автоматичного лексичного пошуку за лексемою *"Pokrovska / Покровська"* пошуковий сервіс Wikidata запропонував даний об'єкт із високим текстовим схожістю назви. Проте семантична верифікація за рівнем V1 виявила повну несумісність атрибутів:
  1. *Класифікація:* `wd:Q108882857` класифікується як підприємство з видобутку кам'яного вугілля (`Q828945`), тоді як локальний актив належить до класу `:SolarPowerPlant`.
  2. *Географічна локалізація:* Шахтоуправління розташоване у м. Покровськ Донецької області, тоді як Покровська сонячна електростанція побудована біля м. Покров Нікопольського району Дніпропетровської області.
  3. *Енергетичний профіль:* Вугільна шахта є споживачем або первинним видобувником палива, тоді як СЕС — відновлюваним генеруючим активом 240 МВт.
  Встановлення зв'язку `owl:sameAs` або `skos:exactMatch` призвело б до критичного спотворення графа та неправдивих висновків логічного виведення.

---

## 3. Працюючий федеративний SPARQL-запит через зв'язки (C4)

Запит зчитує встановлені в `data/links.ttl` семантичні відповідники `skos:closeMatch` та `skos:exactMatch`, фільтрує зовнішні URI для DBpedia і через директиву `SERVICE` динамічно отримує глобальні геокоординати та англомовні назви.

### Текст запиту:
```sparql
PREFIX : <http://www.semanticweb.org/ontologies/2026/energy-system#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX geo: <http://www.w3.org/2003/01/geo/wgs84_pos#>

SELECT ?localAsset ?localLabel ?externalEntity ?extLabel ?lat ?long
WHERE {
  ?localAsset (skos:closeMatch|skos:exactMatch) ?externalEntity .
  ?localAsset rdfs:label ?localLabel .
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
| `:Dniester_PSPS_Unit` | Дністровська ГАЕС, Гідроагрегат №1 | `dbr:Dniester_Pumped_Storage_Power_Station` | Dniester Pumped Storage Power Station | 48.5136 | 27.4733 |
| `:KhmelnytskyiNPP_Unit1` | Хмельницька АЕС, Енергоблок №1 | `dbr:Khmelnytskyi_Nuclear_Power_Plant` | Khmelnytskyi Nuclear Power Plant | 50.3014 | 26.6497 |
| `:Dnipro_HPP_Unit1` | Дніпровська ГЕС, Гідроагрегат №1 | `dbr:Dnieper_Hydroelectric_Station` | Dnieper Hydroelectric Station | 47.8692 | 35.0869 |
| `:Trypilska_ThermalPowerPlant` | Трипільська ТЕС | `dbr:Trypilska_thermal_power_plant` | Trypilska thermal power plant | 50.1351 | 30.7481 |
| `:Ukrenergo_National_TSO` | НЕК «Укренерго» | `dbr:Ukrenergo` | Ukrenergo | — | — |
