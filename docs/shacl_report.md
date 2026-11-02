# Звіт SHACL-валідації графа знань енергосистеми

## 1. Специфікація форм та обмежень цілісності (C1)
Форми валідації визначено у файлі `shapes/shapes.ttl`. Набір охоплює 5 класів онтології та 10 обмежень різних типів: числові діапазони, кардинальність, цільовий клас, типи даних та регулярні вирази.

| Форма (`sh:NodeShape`) | Цільовий клас (`sh:targetClass`) | Перевірений шлях (`sh:path`) | Тип обмеження | Параметри обмеження |
| :--- | :--- | :--- | :--- | :--- |
| `:GeneratingUnitShape` | `:GenerationUnit` | `:hasRatedActivePowerMW` | `sh:minExclusive`, `sh:datatype` | `minExclusive 0.0`, `xsd:double` (строго додатна потужність) |
| `:GeneratingUnitShape` | `:GenerationUnit` | `:suppliesPowerTo` | `sh:minCount`, `sh:class` | `minCount 1`, `sh:class :Substation` (обов'язкове підключення до ПС) |
| `:SubstationShape` | `:Substation` | `:hasVoltageLevelKV` | `sh:minInclusive`, `sh:maxInclusive` | `35.0 <= U <= 1150.0` кВ, `xsd:double` |
| `:SubstationShape` | `:Substation` | `:hasAssetIdentifier` | `sh:pattern`, `sh:minCount` | `^UA-SUBST-[A-Z0-9]+-[0-9]+$` (формат CIM mRID) |
| `:PowerTransformerShape` | `:PowerTransformer` | `:partOf` | `sh:minCount`, `sh:class` | `minCount 1`, `sh:class :Substation` (приналежність до ПС) |
| `:PowerTransformerShape` | `:PowerTransformer` | `:hasVoltageLevelKV` | `sh:minCount`, `sh:datatype` | `minCount 1`, `xsd:double` |
| `:RelayProtectionShape` | `:RelayProtectionAction` | `:hasTripTimeMS` | `sh:minInclusive`, `sh:maxInclusive` | `10 <= t <= 5000` мс, `xsd:integer` |
| `:RelayProtectionShape` | `:RelayProtectionAction` | `:protects` | `sh:minCount`, `sh:class` | `minCount 1`, `sh:class :NetworkInfra` |
| `:DGAAnalysisShape` | `:DissolvedGasAnalysis` | `:hasHydrogenConcentrationPPM` | `sh:minInclusive`, `sh:datatype` | `minInclusive 0.0`, `xsd:double` |
| `:DGAAnalysisShape` | `:DissolvedGasAnalysis` | `:protects` | `sh:minCount`, `sh:class` | `minCount 1`, `sh:class :PowerTransformer` |

---

## 2. Результати перевірки pySHACL (C2, C3)

### 2.1. Валідний граф (`data/kb.ttl`)
Команда запуску валідатора:
```bash
uv run pyshacl -s shapes/shapes.ttl -i rdfs data/kb.ttl
```
**Звіт pySHACL:**
```text
Validation Report
Conforms: True
```
Базовий граф містить 565 триплетів і повністю задовольняє всі обмеження цілісності.

---

### 2.2. Дефектний граф (`data/defective_kb.ttl`)
У дефектний граф внесено 4 сутності з порушеннями:
1. `:Defective_Solar_Plant` — від'ємна потужність `-45.0` МВт (порушення `minExclusive 0.0`).
2. `:Defective_Substation_Cherkasy` — невалідний формат ідентифікатора `"CHERKASY-SUBSTATION-WRONG"` (порушення регулярного виразу `pattern`).
3. `:Defective_Protection_Action` — час спрацювання `15000` мс (порушення `maxInclusive 5000`) та відсутність цільового об'єкта захисту `:protects` (порушення `minCount 1`).
4. `:Defective_Transformer_T9` — відсутність твердження `:partOf` (порушення `minCount 1`).

Команда запуску валідатора:
```bash
uv run pyshacl -s shapes/shapes.ttl -i rdfs data/defective_kb.ttl
```
**Звіт pySHACL:**
```text
Validation Report
Conforms: False
Results (5):
Constraint Violation in MaxInclusiveConstraintComponent (http://www.w3.org/ns/shacl#MaxInclusiveConstraintComponent):
	Severity: sh:Violation
	Focus Node: :Defective_Protection_Action
	Value Node: Literal("15000", datatype=xsd:integer)
	Result Path: :hasTripTimeMS
	Message: Час спрацювання релейного захисту повинен бути в межах від 10 до 5000 мс.

Constraint Violation in MinCountConstraintComponent (http://www.w3.org/ns/shacl#MinCountConstraintComponent):
	Severity: sh:Violation
	Focus Node: :Defective_Protection_Action
	Result Path: :protects
	Message: Релейний захист повинен захищати об'єкт мережевої інфраструктури (:NetworkInfra).

Constraint Violation in MinCountConstraintComponent (http://www.w3.org/ns/shacl#MinCountConstraintComponent):
	Severity: sh:Violation
	Focus Node: :Defective_Transformer_T9
	Result Path: :partOf
	Message: Силовий трансформатор обов'язково повинен бути частиною конкретної підстанції (:Substation).

Constraint Violation in MinExclusiveConstraintComponent (http://www.w3.org/ns/shacl#MinExclusiveConstraintComponent):
	Severity: sh:Violation
	Focus Node: :Defective_Solar_Plant
	Value Node: Literal("-45.0", datatype=xsd:double)
	Result Path: :hasRatedActivePowerMW
	Message: Генеруюча одиниця повинна мати додатну номінальну потужність (> 0 МВт).

Constraint Violation in PatternConstraintComponent (http://www.w3.org/ns/shacl#PatternConstraintComponent):
	Severity: sh:Violation
	Focus Node: :Defective_Substation_Cherkasy
	Value Node: Literal("CHERKASY-SUBSTATION-WRONG")
	Result Path: :hasAssetIdentifier
	Message: Ідентифікатор підстанції повинен відповідати формату UA-SUBST-<NAME>-<VOLTAGE>.
```
Валідатор зафіксував 5 порушень, вказавши фокусні вузли, шляхи властивостей та відповідні повідомлення.

---

## 3. Семантична різниця між SHACL та OWL у валідації даних (C4)
OWL базується на припущенні відкритого світу (Open World Assumption, OWA) та припущенні про неунікальність імен (Non-Unique Name Assumption, NUNA). Його призначення — дедуктивне виведення нових фактів (інференція), а не контроль повноти чи коректності збережених даних. Якщо в екземплярі OWL відсутнє обов'язкове поле (наприклад, `:partOf`), резонер не фіксує помилку, а припускає, що зв'язок існує в зовнішньому середовищі, але ще не доданий до бази. Аналогічно, при перевищенні ліміту `owl:maxCardinality 1` резонер об'єднає два різні ресурси в один через `owl:sameAs`, замість сигналізування про порушення структури.

SHACL працює за парадигмою закритого світу (Closed World Assumption, CWA) та семантики заперечення як неуспіху (Negation as Failure). Мова розроблена спеціально для валідації графів знань і діє аналогічно до схеми реляційної бази даних чи JSON Schema. SHACL детерміновано перевіряє кардинальність, числові діапазони, формати рядків і типи даних у межах поточного графа, генеруючи формальний звіт про порушення (`sh:ValidationReport`) без зміни цільових даних чи додавання неявних зв'язків.
