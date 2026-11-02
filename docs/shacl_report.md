# Звіт SHACL-валідації графа знань енергосистеми

## 1. Огляд форм та обмежень (C1)
Для забезпечення цілісності та якості даних розроблено набір SHACL-форм у файлі `shapes/shapes.ttl`. Форми охоплюють 5 ключових класів онтології та 10 обмежень різних категорій (кардинальність, тип даних, клас зв'язаного об'єкта, числові діапазони, регулярні вирази).

| Форма (`sh:NodeShape`) | Цільовий клас (`sh:targetClass`) | Перевірений шлях (`sh:path`) | Тип обмеження | Параметри та повідомлення |
| :--- | :--- | :--- | :--- | :--- |
| `:GeneratingUnitShape` | `:GenerationUnit` | `:hasRatedActivePowerMW` | `sh:minExclusive`, `sh:datatype` | `minExclusive 0.0`, `xsd:double` (потужність повинна бути додатною) |
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

### 2.1. Перевірка валідного набору даних (`data/kb.ttl`)
Команда запуску валідатора:
```bash
uv run pyshacl -s shapes/shapes.ttl -i rdfs data/kb.ttl
```
**Звіт pySHACL:**
```text
Validation Report
Conforms: True
```
**Коментар:** Усі 565 триплетів базового графа відповідають усім вимогам бізнес-логіки та обмеженням форм. Порушень не виявлено.

---

### 2.2. Перевірка дефектного набору даних (`data/defective_kb.ttl`)
До графа було навмисно внесено 4 сутності з критичними дефектами:
1. `:Defective_Solar_Plant` — від'ємна потужність `-45.0` МВт (порушення `minExclusive 0.0`).
2. `:Defective_Substation_Cherkasy` — невалідний формат ідентифікатора `"CHERKASY-SUBSTATION-WRONG"` (порушення регулярного виразу `pattern`).
3. `:Defective_Protection_Action` — неприпустимий час спрацювання `15000` мс (порушення `maxInclusive 5000`) та відсутність цільового об'єкта захисту `:protects` (порушення `minCount 1`).
4. `:Defective_Transformer_T9` — відсутність твердження приналежності `:partOf` до підстанції (порушення `minCount 1`).

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
**Коментар:** pySHACL успішно зафіксував 5 порушень (вимога: ≥ 3 порушення), точно локалізувавши вузли, шляхи властивостей та сформувавши людиночитані повідомлення про помилки.

---

## 3. Чому SHACL, а не OWL, відповідає за ці обмеження (C4)
Мова онтологій OWL базується на концепції відкритого світу (Open World Assumption, OWA) та припущенні про неунікальність імен (Non-Unique Name Assumption, NUNA). Її першочергове математичне призначення — дедуктивне виведення нових знань (інференція), а не валідація коректності наповнення бази даних. Під OWA, якщо у сутності відсутня обов'язкова властивість (наприклад, `:partOf` для трансформатора), OWL-резонер не генерує помилку, а вважає, що зв'язок існує десь у зовнішньому світі, просто ще не був занесений до поточної онтології. Більше того, при спробі обмежити максимальну кількість значень через `owl:maxCardinality 1`, резонер об'єднає два різних ресурси правилом еквівалентності (`owl:sameAs`), замість повідомлення про порушення контракту.

На противагу OWL, мова SHACL функціонує в парадигмі закритого світу (Closed World Assumption, CWA) та заперечення як невдачі (Negation as Failure). Вона створена спеціально для інженерії даних та забезпечення цілісності графів, виступаючи еквівалентом JSON Schema або XML Schema в Semantic Web. SHACL жорстко перевіряє кардинальність, відповідність числовим інтервалам, синтаксичним регулярним виразам (regex pattern) та цільовим типам даних, повертаючи формалізований звіт про помилки (`sh:ValidationReport`) без зміни або спотворення самого графа.
