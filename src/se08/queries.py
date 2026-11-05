"""Domain queries for Self-Education 8: SPARQL queries to Wikidata.

Domain: Power System Management and Electric Infrastructure (IEC CIM aligned).
"""

QUERIES = {
    "CQ1": {
        "title": "Атомні електростанції України (потужність, координати)",
        "cq": "Які атомні електростанції (АЕС) функціонують в Україні, яка їхня встановлена потужність та координати?",
        "constructs": ["SELECT", "SERVICE", "OPTIONAL", "ORDER BY", "Property Path"],
        "sparql": """PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX bd: <http://www.bigdata.com/rdf#>

SELECT ?plant ?plantLabel ?capacity ?coords WHERE {
  ?plant wdt:P31/wdt:P279* wd:Q134447 ;
         wdt:P17 wd:Q212 .
  OPTIONAL { ?plant wdt:P2100 ?capacity . }
  OPTIONAL { ?plant wdt:P625 ?coords . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "uk,en". }
}
ORDER BY DESC(?capacity)
""",
    },
    "CQ2": {
        "title": "Наявність гідроакумулюючих станцій (ГАЕС) в Україні",
        "cq": "Чи є в базі знань Wikidata підтвердження наявності гідроакумулюючих електростанцій (ГАЕС) на території України?",
        "constructs": ["ASK", "Property Path"],
        "sparql": """PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>

ASK {
  ?plant wdt:P31/wdt:P279* wd:Q200297 ;
         wdt:P17 wd:Q212 .
}
""",
    },
    "CQ3": {
        "title": "Розподіл СЕС за областями України з фільтрацією",
        "cq": "Яка кількість об'єктів сонячної генерації (СЕС) зареєстрована в розрізі регіонів України (з кількістю >= 2)?",
        "constructs": ["SELECT", "COUNT", "GROUP BY", "HAVING", "SERVICE", "Property Path"],
        "sparql": """PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX bd: <http://www.bigdata.com/rdf#>

SELECT ?region ?regionLabel (COUNT(?plant) AS ?solarPlantCount) WHERE {
  ?plant wdt:P31/wdt:P279* wd:Q1002842 ;
         wdt:P17 wd:Q212 ;
         wdt:P131 ?region .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "uk,en". }
}
GROUP BY ?region ?regionLabel
HAVING (COUNT(?plant) >= 2)
ORDER BY DESC(?solarPlantCount)
""",
    },
    "CQ4": {
        "title": "Таксономічне замикання підкласів електростанцій",
        "cq": "Які підкласи концепту 'електростанція' (wd:Q159719) існують у глобальній онтології Wikidata за транзитивним шляхом?",
        "constructs": ["SELECT", "DISTINCT", "Property Path (+)", "SERVICE", "LIMIT"],
        "sparql": """PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX bd: <http://www.bigdata.com/rdf#>

SELECT DISTINCT ?subClass ?subClassLabel WHERE {
  ?subClass wdt:P279+ wd:Q159719 .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "uk,en". }
}
ORDER BY ?subClassLabel
LIMIT 30
""",
    },
    "CQ5": {
        "title": "Сумарна та середня потужність гідроелектростанцій України",
        "cq": "Яка сумарна та середня встановлена потужність (МВт) гідроелектростанцій в Україні за наявними числовими показниками?",
        "constructs": ["SELECT", "COUNT", "SUM", "AVG", "Property Path"],
        "sparql": """PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>

SELECT (COUNT(?plant) AS ?plantCount) 
       (SUM(?capacity) AS ?totalCapacityMW) 
       (AVG(?capacity) AS ?avgCapacityMW) WHERE {
  ?plant wdt:P31/wdt:P279* wd:Q159190 ;
         wdt:P17 wd:Q212 ;
         wdt:P2100 ?capacity .
}
""",
    },
    "CQ6": {
        "title": "Топ-10 найпотужніших вітрових електростанцій світу",
        "cq": "Які 10 найпотужніших вітроелектростанцій світу зафіксовані в базі із зазначенням країни, оператора та потужності?",
        "constructs": ["SELECT", "FILTER", "OPTIONAL", "ORDER BY", "LIMIT", "SERVICE", "Property Path"],
        "sparql": """PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX bd: <http://www.bigdata.com/rdf#>

SELECT ?plant ?plantLabel ?countryLabel ?operatorLabel ?capacity WHERE {
  ?plant wdt:P31/wdt:P279* wd:Q29171 ;
         wdt:P17 ?country ;
         wdt:P2100 ?capacity .
  OPTIONAL { ?plant wdt:P137 ?operator . }
  FILTER (?capacity > 300)
  SERVICE wikibase:label { bd:serviceParam wikibase:language "uk,en". }
}
ORDER BY DESC(?capacity)
LIMIT 10
""",
    },
    "CQ7": {
        "title": "Просторова ієрархія: електростанції Львівської області",
        "cq": "Які електростанції розташовані на території Львівської області з урахуванням вкладеності районів та громад (wdt:P131*)?",
        "constructs": ["SELECT", "DISTINCT", "Property Path (*)", "OPTIONAL", "SERVICE"],
        "sparql": """PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX bd: <http://www.bigdata.com/rdf#>

SELECT DISTINCT ?plant ?plantLabel ?typeLabel ?capacity WHERE {
  ?plant wdt:P31/wdt:P279* wd:Q159719 ;
         wdt:P131* wd:Q1180 ;
         wdt:P31 ?type .
  OPTIONAL { ?plant wdt:P2100 ?capacity . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "uk,en". }
}
ORDER BY ?plantLabel
""",
    },
    "CQ8": {
        "title": "Оператори системи передачі (TSO) та дистрибуції електроенергії",
        "cq": "Які суб'єкти виконують функції операторів системи передачі або розподілу електроенергії в Україні та суміжних країнах?",
        "constructs": ["SELECT", "VALUES", "OPTIONAL", "SERVICE", "Property Path"],
        "sparql": """PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX bd: <http://www.bigdata.com/rdf#>

SELECT ?company ?companyLabel ?countryLabel ?inception WHERE {
  VALUES ?operatorType { wd:Q1572973 wd:Q1758788 }
  VALUES ?country { wd:Q212 wd:Q36 wd:Q28 wd:Q218 wd:Q211 }
  ?company wdt:P31/wdt:P279* ?operatorType ;
           wdt:P17 ?country .
  OPTIONAL { ?company wdt:P571 ?inception . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "uk,en". }
}
ORDER BY ?countryLabel ?companyLabel
""",
    },
}

LLM_COMPARISONS = {
    "LLM_CASE_1": {
        "title": "Запит АЕС України (галюцинація схеми DBpedia та IRI)",
        "cq": "CQ1: Які атомні електростанції діють в Україні та яка їх потужність?",
        "llm_prompt": "Напиши SPARQL-запит до Wikidata, щоб отримати всі діючі АЕС України та їхню встановлену потужність.",
        "raw_llm_sparql": """SELECT ?plant ?capacity WHERE {
  ?plant rdf:type dbo:NuclearPowerPlant .
  ?plant dbo:location dbr:Ukraine .
  ?plant dbo:capacity ?capacity .
}""",
        "defect_type": "Змішування просторів імен (DBpedia замість Wikidata) та відсутність префіксів",
        "defect_description": "Модель використала предикати та класи DBpedia (dbo:NuclearPowerPlant, dbo:location, dbo:capacity) у запиті до ендпойнта Wikidata, де сутності кодуються Q/P числовими ідентифікаторами (wd:Q134447, wdt:P17, wdt:P2100). Також відсутні директиви PREFIX, що викликає QueryParseError.",
        "fixed_sparql": """PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX bd: <http://www.bigdata.com/rdf#>

SELECT ?plant ?plantLabel ?capacity WHERE {
  ?plant wdt:P31/wdt:P279* wd:Q134447 ;
         wdt:P17 wd:Q212 .
  OPTIONAL { ?plant wdt:P2100 ?capacity . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "uk,en". }
}
ORDER BY DESC(?capacity)
""",
    },
    "LLM_CASE_2": {
        "title": "Запит ГАЕС України (інверсія суб'єкта та об'єкта в ASK)",
        "cq": "CQ2: Чи є в Україні гідроакумулюючі електростанції?",
        "llm_prompt": "Напиши SPARQL ASK запит для Wikidata, щоб перевірити, чи є в Україні гідроакумулюючі електростанції.",
        "raw_llm_sparql": """PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>

ASK {
  wd:Q212 wdt:P31 wd:Q200297 .
}""",
        "defect_type": "Інверсія ролей суб'єкт-об'єкт (Subject-Object Inversion)",
        "defect_description": "LLM згенерувала твердження 'wd:Q212 wdt:P31 wd:Q200297', що дослівно означає 'Україна є екземпляром гідроакумулюючої електростанції'. Запит семантично хибний і детерміновано повертає false. Необхідно шукати станцію (?plant), яка є екземпляром ГАЕС та розташована в Україні (wdt:P17 wd:Q212).",
        "fixed_sparql": """PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>

ASK {
  ?plant wdt:P31/wdt:P279* wd:Q200297 ;
         wdt:P17 wd:Q212 .
}
""",
    },
    "LLM_CASE_3": {
        "title": "Запит електростанцій Львівщини (втрата ієрархічної вкладеності wdt:P131*)",
        "cq": "CQ7: Електростанції Львівської області",
        "llm_prompt": "Напиши SPARQL-запит до Wikidata для вибірки всіх електростанцій у Львівській області.",
        "raw_llm_sparql": """PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX bd: <http://www.bigdata.com/rdf#>

SELECT ?plant ?plantLabel WHERE {
  ?plant wdt:P31 wd:Q159719 ;
         wdt:P131 wd:Q1180 .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "uk". }
}""",
        "defect_type": "Пропуск транзитивного шляху вкладеності (Property Path Exclusion) та пряме P31",
        "defect_description": "LLM використала прямий предикат 'wdt:P131 wd:Q1180'. У реальному графі Wikidata електростанції безпосередньо прив'язані до районів (Стрийський, Шептицький/Червоноградський) або територіальних громад, а не до самого вузла області. Також пряме 'wdt:P31 wd:Q159719' пропускає специфічні класи (ТЕС, СЕС, ВЕС), повертаючи порожній або майже порожній результат. Необхідно: 'wdt:P131* wd:Q1180' та 'wdt:P31/wdt:P279* wd:Q159719'.",
        "fixed_sparql": """PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX bd: <http://www.bigdata.com/rdf#>

SELECT DISTINCT ?plant ?plantLabel ?typeLabel ?capacity WHERE {
  ?plant wdt:P31/wdt:P279* wd:Q159719 ;
         wdt:P131* wd:Q1180 ;
         wdt:P31 ?type .
  OPTIONAL { ?plant wdt:P2100 ?capacity . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "uk,en". }
}
ORDER BY ?plantLabel
""",
    },
    "LLM_CASE_4": {
        "title": "Агрегація СЕС за регіонами (відсутність сервісу міток у GROUP BY)",
        "cq": "CQ3: Кількість сонячних станцій за областями України",
        "llm_prompt": "Склади SPARQL-запит, який згрупує сонячні електростанції України за областями та порахує їх кількість.",
        "raw_llm_sparql": """PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>

SELECT ?region (COUNT(?plant) AS ?count) WHERE {
  ?plant wdt:P31 wd:Q1002842 ;
         wdt:P17 wd:Q212 ;
         wdt:P131 ?region .
}
GROUP BY ?region""",
        "defect_type": "Відсутність розгортання міток (Label Service) та пропуск підкласів СЕС",
        "defect_description": "Запит повертає нечитабельні IRI замість назв областей і не має сортування чи фільтрації порожніх/поодиноких значень. Також 'wdt:P31 wd:Q1002842' без транзитивності '/wdt:P279*' відкидає дахові та концентраторні сонячні станції. Виправлення підключає SERVICE wikibase:label, групує за ?region ?regionLabel та додає HAVING.",
        "fixed_sparql": """PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX bd: <http://www.bigdata.com/rdf#>

SELECT ?region ?regionLabel (COUNT(?plant) AS ?solarPlantCount) WHERE {
  ?plant wdt:P31/wdt:P279* wd:Q1002842 ;
         wdt:P17 wd:Q212 ;
         wdt:P131 ?region .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "uk,en". }
}
GROUP BY ?region ?regionLabel
HAVING (COUNT(?plant) >= 2)
ORDER BY DESC(?solarPlantCount)
""",
    },
}
