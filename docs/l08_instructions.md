# Лабораторна робота 8: Інструкція із запуску та перевірки з нуля

Цей документ описує покроковий процес розгортання оточення, завантаження графа знань до триплстора Apache Jena Fuseki, валідації через pySHACL, виконання SPARQL-запитів та тестування конвеєра Text-to-SPARQL.

---

## 1. Системні вимоги та залежності

- **ОС:** Linux (x86_64)
- **Контейнеризація:** Docker / Rancher Desktop (moby runtime)
- **Середовище Python:** Python `>= 3.12`, пакетний менеджер `uv`
- **Залежності:** `rdflib>=7.6.0`, `pyshacl>=0.40.1`, `requests>=2.34.2`, `pytest>=9.1.1`

Встановлення та синхронізація залежностей:
```bash
uv sync
```

---

## 2. Розгортання триплстора Apache Jena Fuseki

Запуск Docker-контейнера Fuseki з використанням хостової мережі (для підтримки викликів федеративних сервісів `SERVICE`):

1. Запуск контейнера
```bash
docker run -d --name fuseki --network host -e ADMIN_PASSWORD=admin stain/jena-fuseki
```
2. Очікування ініціалізації сервісу (3-5 секунд)
3. Створення in-memory датасету /energy
```bash
curl -u admin:admin -s -X POST --data "dbName=energy&dbType=mem" http://localhost:3030/$/datasets
```

Перевірка статусу сервера:
```bash
curl -s -i http://localhost:3030/$/ping
```

---

## 3. Завантаження даних та семантичних зв'язків

Завантаження графа знань онтології (`data/kb.ttl`) та відкритих семантичних зв'язків LOD (`data/links.ttl`) через HTTP Graph Store Protocol:

```bash
# Завантаження основного графа (565 триплетів)
curl -u admin:admin -s -X POST --header "Content-Type: text/turtle; charset=utf-8" \
  --data-binary @data/kb.ttl http://localhost:3030/energy/data

# Завантаження LOD-зв'язків (17 триплетів)
curl -u admin:admin -s -X POST --header "Content-Type: text/turtle; charset=utf-8" \
  --data-binary @data/links.ttl http://localhost:3030/energy/data
```

Підтвердження завантаження запитом `COUNT`:
```bash
curl -s -X POST --data "query=SELECT (COUNT(*) AS ?totalTriples) WHERE { ?s ?p ?o }" http://localhost:3030/energy/sparql
```
*Очікуваний результат:* `582` триплети (565 онтологія + 17 лінки).

---

## 4. Виконання SPARQL-запитів до CQ

Всі запити стандарту SPARQL 1.1 знаходяться в каталозі `queries/`. Та використовують таку схему:

```bash
# KQ1: Електростанції та накопичувачі на ПС Вінницька
curl -s -X POST --data-urlencode "query@queries/<query name>.rq" http://localhost:3030/energy/sparql
```

---

## 5. Валідація SHACL-формами через pySHACL

Форми обмежень описані в `shapes/shapes.ttl` (5 форм, 10 обмежень).

```bash
# Перевірка валідного графа (повинно повернути Conforms: True)
uv run pyshacl -s shapes/shapes.ttl -i rdfs data/kb.ttl

# Перевірка дефектного набору даних (повинно виявити 5 порушень)
uv run pyshacl -s shapes/shapes.ttl -i rdfs data/defective_kb.ttl
```

---

## 6. Запуск оцінки конвеєра Text-to-SPARQL

Скрипт `tests/eval_t2s.py` проводить повний цикл перевірки (парсер синтаксису, валідація за схемою онтології, виконання з `LIMIT` у Fuseki та зіставлення результату з еталоном `tests/t2s.jsonl`):

```bash
uv run python tests/eval_t2s.py
```

*Очікувані метрики:*
- **V1 (Baseline):** Syntax: 100%, Schema: 66.7%, Execution: 60.0%
- **V2 (Refined):** Syntax: 100%, Schema: 100%, Execution: 100%

---

## 7. Управління твердженнями через CLI

Статистика та статус тверджень у `claims/claims.csv`:
```bash
./claim.bash list
./claim.bash stats
```
