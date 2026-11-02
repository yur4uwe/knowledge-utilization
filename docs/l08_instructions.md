# Лабораторна робота 8: Інструкція із запуску та перевірки з нуля

Покроковий регламент розгортання оточення, завантаження графа знань у триплстор Apache Jena Fuseki, валідації pySHACL, виконання SPARQL-запитів та оцінки конвеєра Text-to-SPARQL.

---

## 1. Системні вимоги та залежності

- **Контейнеризація:** Docker / Rancher Desktop (moby runtime)
- **Середовище Python:** Python `>= 3.12`, менеджер пакетів `uv`
- **Залежності:** `rdflib>=7.6.0`, `pyshacl>=0.40.1`, `requests>=2.34.2`, `pytest>=9.1.1`
- **Платформа:** Linux x86_64

Встановлення та синхронізація залежностей:
```bash
uv sync
```

---

## 2. Розгортання триплстора Apache Jena Fuseki

Запуск Docker-контейнера Fuseki в режимі мережі хоста для підтримки федеративних запитів (`SERVICE`):

1. Запуск контейнера:
   ```bash
   docker run -d --name fuseki --network host -e ADMIN_PASSWORD=admin stain/jena-fuseki
   ```

2. Створення in-memory датасету `/energy`:
   ```bash
   curl -u admin:admin -s -X POST \
     --data "dbName=energy&dbType=mem" \
     http://localhost:3030/$/datasets
   ```

3. Перевірка працездатності:
   ```bash
   curl -s -i http://localhost:3030/$/ping
   ```

---

## 3. Завантаження даних та семантичних зв'язків

Завантаження графа онтології (`data/kb.ttl`) та відкритих семантичних зв'язків LOD (`data/links.ttl`) через HTTP Graph Store Protocol:

1. Завантаження основного графа (565 триплетів):
   ```bash
   curl -u admin:admin -s -X POST \
     --header "Content-Type: text/turtle; charset=utf-8" \
     --data-binary @data/kb.ttl \
     http://localhost:3030/energy/data
   ```

2. Завантаження LOD-зв'язків (17 триплетів):
   ```bash
   curl -u admin:admin -s -X POST \
     --header "Content-Type: text/turtle; charset=utf-8" \
     --data-binary @data/links.ttl \
     http://localhost:3030/energy/data
   ```

3. Перевірка підсумкової кількості триплетів запитом `COUNT`:
   ```bash
   curl -s -X POST \
     --data "query=SELECT (COUNT(*) AS ?totalTriples) WHERE { ?s ?p ?o }" \
     http://localhost:3030/energy/sparql
   ```
   Очікуваний результат: `582` триплети (565 онтологія + 17 зв'язки).

---

## 4. Виконання SPARQL-запитів до CQ

Запити стандарту SPARQL 1.1 розміщено в каталозі `queries/`. Виконання довільного запиту:

```bash
curl -s -X POST --data-urlencode "query@queries/<query_file>.rq" http://localhost:3030/energy/sparql
```

Приклад виконання запиту генерації за підстанцією (KQ1):
```bash
curl -s -X POST --data-urlencode "query@queries/q01_kq1_generation_by_substation.rq" http://localhost:3030/energy/sparql
```

---

## 5. Валідація SHACL-формами через pySHACL

Форми обмежень містяться у `shapes/shapes.ttl` (5 форм, 10 обмежень).

- Перевірка валідного графа (очікувано: `Conforms: True`):
  ```bash
  uv run pyshacl -s shapes/shapes.ttl -i rdfs data/kb.ttl
  ```

- Перевірка дефектного графа (очікувано: `Conforms: False`, 5 порушень):
  ```bash
  uv run pyshacl -s shapes/shapes.ttl -i rdfs data/defective_kb.ttl
  ```

---

## 6. Оцінка конвеєра Text-to-SPARQL

Запуск повного циклу оцінки (парсер синтаксису, валідація за схемою онтології, виконання з `LIMIT` у Fuseki та зіставлення результату з еталоном `tests/t2s.jsonl`):

```bash
uv run python tests/eval_t2s.py
```

Очікувані показники:
- **V1 (Baseline):** Syntax: 100%, Schema: 66.7%, Execution: 60.0%
- **V2 (Refined):** Syntax: 100%, Schema: 100%, Execution: 100%

---

## 7. Управління твердженнями через CLI

Перевірка статусу тверджень у `claims/claims.csv`:
```bash
./claim.bash list
./claim.bash stats
```
