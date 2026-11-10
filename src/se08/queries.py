"""Domain queries for Self-Education 8: SPARQL queries to Wikidata.

Loads standalone .sparql files from src/se08/queries/.
Domain: Power System Management and Electric Infrastructure (IEC CIM aligned).
"""

from pathlib import Path

QUERIES_DIR = Path(__file__).resolve().parent / "queries"
LLM_DIR = QUERIES_DIR / "llm"


def read_query(filename: str) -> str:
    """Read a SPARQL query file."""
    path = QUERIES_DIR / filename
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def read_llm_query(filename: str) -> str:
    """Read an LLM SPARQL query file."""
    path = LLM_DIR / filename
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


QUERIES = {
    "CQ1": {
        "file": "cq01_npp.sparql",
        "title": "Атомні електростанції України (потужність, координати, оператор)",
        "cq": "Які атомні електростанції (АЕС) функціонують в Україні, яка їхня встановлена потужність (МВт), координати та оператор?",
        "constructs": ["SELECT", "SERVICE", "OPTIONAL", "ORDER BY", "Property Path"],
        "sparql": read_query("cq01_npp.sparql"),
    },
    "CQ2": {
        "file": "cq02_pspp_ask.sparql",
        "title": "Наявність гідроакумулюючих станцій (ГАЕС) в Україні",
        "cq": "Чи є в базі знань Wikidata підтвердження наявності гідроакумулюючих електростанцій (ГАЕС) на території України?",
        "constructs": ["ASK", "Property Path"],
        "sparql": read_query("cq02_pspp_ask.sparql"),
    },
    "CQ3": {
        "file": "cq03_nuclear_by_country.sparql",
        "title": "Кількість ядерних станцій у країнах Європи з фільтрацією",
        "cq": "Яка кількість ядерних електростанцій зафіксована в країнах Європи (для країн із >= 2 об'єктами)?",
        "constructs": ["SELECT", "VALUES", "COUNT", "GROUP BY", "HAVING", "SERVICE", "Property Path"],
        "sparql": read_query("cq03_nuclear_by_country.sparql"),
    },
    "CQ4": {
        "file": "cq04_taxonomy_closure.sparql",
        "title": "Таксономічне замикання підкласів електростанцій",
        "cq": "Які підкласи концепту 'електростанція' (wd:Q159719) існують у глобальній онтології Wikidata за транзитивним шляхом?",
        "constructs": ["SELECT", "DISTINCT", "Property Path (+)", "SERVICE", "LIMIT"],
        "sparql": read_query("cq04_taxonomy_closure.sparql"),
    },
    "CQ5": {
        "file": "cq05_hydro_stats.sparql",
        "title": "Сумарна та середня потужність гідроелектростанцій України",
        "cq": "Яка сумарна та середня встановлена потужність (МВт) гідроелектростанцій в Україні за наявними числовими показниками?",
        "constructs": ["SELECT", "COUNT", "SUM", "AVG", "Property Path"],
        "sparql": read_query("cq05_hydro_stats.sparql"),
    },
    "CQ6": {
        "file": "cq06_top_ukraine_power.sparql",
        "title": "Топ найпотужніших електростанцій України",
        "cq": "Які електростанції України мають встановлену потужність >= 2000 МВт із зазначенням типу генерації?",
        "constructs": ["SELECT", "DISTINCT", "FILTER", "ORDER BY", "LIMIT", "SERVICE", "Property Path"],
        "sparql": read_query("cq06_top_ukraine_power.sparql"),
    },
    "CQ7": {
        "file": "cq07_dnipro_hydro_cascade.sparql",
        "title": "Гідроелектростанції Дніпровського каскаду (річка Дніпро)",
        "cq": "Які гідроелектростанції та гідроакумулюючі станції розташовані на річці Дніпро (wd:Q40855) в Україні?",
        "constructs": ["SELECT", "OPTIONAL", "ORDER BY", "SERVICE", "Property Path"],
        "sparql": read_query("cq07_dnipro_hydro_cascade.sparql"),
    },
    "CQ8": {
        "file": "cq08_tso_operators.sparql",
        "title": "Оператори систем передачі (TSO) в країнах Європи",
        "cq": "Які системні оператори передачі електроенергії (TSO, wd:Q112046) діють в Україні та європейських державах?",
        "constructs": ["SELECT", "VALUES", "OPTIONAL", "SERVICE"],
        "sparql": read_query("cq08_tso_operators.sparql"),
    },
}

LLM_COMPARISONS = {
    "LLM_CASE_1": {
        "raw_file": "llm/case1_raw.sparql",
        "fixed_file": "llm/case1_fixed.sparql",
        "title": "Запит АЕС України (галюцинація схеми DBpedia та відсутність префіксів)",
        "cq": "CQ1: Які атомні електростанції діють в Україні та яка їх потужність?",
        "llm_prompt": "Напиши SPARQL-запит до Wikidata, щоб отримати всі діючі АЕС України та їхню встановлену потужність.",
        "raw_llm_sparql": read_llm_query("case1_raw.sparql"),
        "defect_type": "Змішування просторів імен (DBpedia замість Wikidata) та відсутність префіксів",
        "defect_description": "Модель використала предикати та класи DBpedia (dbo:NuclearPowerPlant, dbo:location, dbo:capacity) у запиті до ендпойнта Wikidata, де сутності кодуються Q/P числовими ідентифікаторами (wd:Q134447, wdt:P17, wdt:P2109). Також пропущено директиви PREFIX, що викликає QueryParseError.",
        "fixed_sparql": read_llm_query("case1_fixed.sparql"),
    },
    "LLM_CASE_2": {
        "raw_file": "llm/case2_raw.sparql",
        "fixed_file": "llm/case2_fixed.sparql",
        "title": "Запит ГАЕС України (інверсія суб'єкта та об'єкта в ASK)",
        "cq": "CQ2: Чи є в Україні гідроакумулюючі електростанції?",
        "llm_prompt": "Напиши SPARQL ASK запит для Wikidata, щоб перевірити, чи є в Україні гідроакумулюючі електростанції.",
        "raw_llm_sparql": read_llm_query("case2_raw.sparql"),
        "defect_type": "Інверсія ролей суб'єкт-об'єкт (Subject-Object Inversion)",
        "defect_description": "LLM згенерувала твердження 'wd:Q212 wdt:P31 wd:Q339353', що означає 'Україна є екземпляром гідроакумулюючої електростанції'. Запит семантично хибний і детерміновано повертає false. Необхідно шукати станцію (?plant), яка є екземпляром ГАЕС та розташована в Україні (wdt:P17 wd:Q212).",
        "fixed_sparql": read_llm_query("case2_fixed.sparql"),
    },
    "LLM_CASE_3": {
        "raw_file": "llm/case3_raw.sparql",
        "fixed_file": "llm/case3_fixed.sparql",
        "title": "Запит Дніпровського гідрокаскаду (хибний Q-код об'єкта та відсутність транзитивності)",
        "cq": "CQ7: ГЕС Дніпровського каскаду на річці Дніпро",
        "llm_prompt": "Напиши SPARQL-запит до Wikidata для вибірки гідроелектростанцій на річці Дніпро.",
        "raw_llm_sparql": read_llm_query("case3_raw.sparql"),
        "defect_type": "Галюцинація Q-коду сутності (Entity Linking Hallucination) та пропуск Property Path",
        "defect_description": "LLM підставила Q-код wd:Q159190 замість wd:Q15911738 для ГЕС та wd:Q206 замість wd:Q40855 для річки Дніпро. Також статичне wdt:P31 без /wdt:P279* відкидає гідроакумулюючі станції каскаду. У результаті запит повертає 0 результатів. Виправлення встановлює точні ідентифікатори та транзитивний шлях.",
        "fixed_sparql": read_llm_query("case3_fixed.sparql"),
    },
    "LLM_CASE_4": {
        "raw_file": "llm/case4_raw.sparql",
        "fixed_file": "llm/case4_fixed.sparql",
        "title": "Агрегація АЕС за країнами (відсутність сервісу міток та групування за неагрегованими змінними)",
        "cq": "CQ3: Кількість ядерних станцій за країнами Європи",
        "llm_prompt": "Склади SPARQL-запит, який згрупує атомні електростанції за країнами та порахує їх кількість.",
        "raw_llm_sparql": read_llm_query("case4_raw.sparql"),
        "defect_type": "Відсутність розгортання міток (Label Service) та пропуск підкласів",
        "defect_description": "Запит повертає сирі IRI без текстових назв країн. Також 'wdt:P31 wd:Q134447' без транзитивності '/wdt:P279*' відкидає дослідницькі та гібридні реакторні установки. Виправлення додає VALUES для фокусування, підключає SERVICE wikibase:label, групує за ?country ?countryLabel та додає HAVING.",
        "fixed_sparql": read_llm_query("case4_fixed.sparql"),
    },
}
