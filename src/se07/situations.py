"""Situation templates modeling and ontological class binding for SE07."""

from __future__ import annotations

from typing import List, Tuple

import rdflib

from src.se07.analyzer import OntologyAnalyzer
from src.se07.models import SituationTemplate

# 5 Domain Situation Templates for Power System Grid Management
SITUATION_TEMPLATES: List[SituationTemplate] = [
    SituationTemplate(
        id="SIT-01",
        title="Аварійне коротке замикання на магістральній ПЛ 750 кВ та дія захисту",
        initial_state_class="NormalOperationState",
        event_class="ShortCircuitFault",
        condition_expr=":hasFaultCurrentKA > 20.0 [струм КЗ перевищує уставку струмової відсічки]",
        new_state_class="EmergencyState",
        action_class="RelayProtectionAction",
        iec_cim_mapping="cim:Fault -> cim:ProtectionRelay -> cim:Breaker",
        operational_narrative=(
            "При нормальній передачі базової потужності виникає міжфазне КЗ на ПЛ 750 кВ; "
            "струм короткого замикання сягає 24.5 кА (> 20.0 кА), що миттєво переводить мережу "
            "в аварійний стан EmergencyState. Мікропроцесорний релейний захист за 65 мс подає команду "
            "на розмикання силових контактів вимикача CircuitBreakerTripAction, локалізуючи пошкодження."
        ),
    ),
    SituationTemplate(
        id="SIT-02",
        title="Аварійний дефіцит генерації та активація первинного регулювання частоти FCR",
        initial_state_class="NormalOperationState",
        event_class="FrequencyDeviation",
        condition_expr=":hasGridFrequencyHz < 49.80 [глибоке просідання частоти нижче меж нормального діапазону]",
        new_state_class="AlertState",
        action_class="PrimaryFrequencyControl",
        iec_cim_mapping="cim:OperationalLimitViolation -> cim:GeneratingUnit -> cim:HydroPump",
        operational_narrative=(
            "Раптова аварійна зупинка енергоблока 1000 МВт порушує баланс потужності в ОЕС України; "
            "частота падає до 49.78 Гц (< 49.80 Гц). Енергосистема входить у тривожний режим AlertState. "
            "Турбінні регулятори маневрених ГЕС та Дністровської ГАЕС (PumpedStorageHydro) протягом "
            "2–15 секунд активують обертовий резерв FCR, зупиняючи динамічний спад частоти."
        ),
    ),
    SituationTemplate(
        id="SIT-03",
        title="Режимне струмове перевантаження автотрансформатора зв'язку при N-1 аварії",
        initial_state_class="AlertState",
        event_class="LineOverload",
        condition_expr=":hasRatedActivePowerMW > 1000.0 [завантаження трансформатора перевищує 115% номіналу]",
        new_state_class="EmergencyState",
        action_class="RedispatchProcess",
        iec_cim_mapping="cim:OperationalLimitViolation -> cim:PowerTransformer -> cim:RemedialActionScheme",
        operational_narrative=(
            "Після аварійного відключення паралельної гілки мережі потік потужності перерозподіляється "
            "на автотрансформатор 750/330 кВ, спричиняючи тривале струмове перевантаження понад допустимий ліміт. "
            "Система переходить з режиму Alert у стан EmergencyState. Диспетчер ОСП НЕК Укренерго "
            "ініціює процедуру RedispatchProcess: розвантаження базової генерації та екстрену видачу "
            "потужності акумуляторними комплексами BatteryStorageBESS для ліквідації перевантаження."
        ),
    ),
    SituationTemplate(
        id="SIT-04",
        title="Термічна деструкція ізоляції та газовиділення в баку трансформатора за DGA",
        initial_state_class="NormalOperationState",
        event_class="InsulationDegradation",
        condition_expr=":hasAcetyleneConcentrationPPM > 5.0 && :hasHydrogenConcentrationPPM > 100.0",
        new_state_class="AlertState",
        action_class="DissolvedGasAnalysis",
        iec_cim_mapping="cim:ConditionAssessment -> cim:EquipmentDefect -> cim:PowerTransformer",
        operational_narrative=(
            "В умовах тривалої експлуатації під високовольтним навантаженням розвивається локальний "
            "дефект твердої целюлозної ізоляції з утворенням мікродугових розрядів. Хроматографічний аналіз "
            "фіксує стрибок ацетилену до 12.4 ppm (> 5.0) та водню до 145 ppm (> 100.0), що переводить "
            "актив у тривожний режим AlertState. Автоматизована діагностика призначає позачергове обстеження, "
            "дегазацію масла та ревізію контактної групи перемикача РПН."
        ),
    ),
    SituationTemplate(
        id="SIT-05",
        title="Локальний профіцит генерації ВДЕ, підвищення напруги та акумулювання енергії",
        initial_state_class="NormalOperationState",
        event_class="VoltageDeviation",
        condition_expr=":hasVoltageLevelKV > 360.0 [перевищення гранично допустимої напруги в мережі 330 кВ]",
        new_state_class="AlertState",
        action_class="SecondaryFrequencyRestoration",
        iec_cim_mapping="cim:SolarGeneratingUnit -> cim:BatteryUnit -> cim:ControlArea",
        operational_narrative=(
            "Під час полуденного максимуму генерації сонячних електростанцій (SolarPowerPlant) у південному регіоні "
            "виникає локальний профіцит потужності, що призводить до зростання напруги у вузлах 330 кВ понад 360 кВ. "
            "Енергорайон переходить у стан AlertState. Автоматика ОСП та вторинне регулювання запускають "
            "команду на поглинання надлишку активної енергії акумуляторними накопичувачами BatteryStorageBESS "
            "і регулювання реактивної потужності інверторів ВДЕ."
        ),
    ),
]


def validate_situation_bindings(analyzer: OntologyAnalyzer) -> List[Tuple[str, bool, str]]:
    """Validate that all class references inside situation templates strictly exist in the ontology."""
    named_classes = {analyzer._local_name(c) for c in analyzer.get_named_classes()}
    results = []

    for sit in SITUATION_TEMPLATES:
        missing = []
        for role, cls_name in [
            ("initial_state", sit.initial_state_class),
            ("event", sit.event_class),
            ("new_state", sit.new_state_class),
            ("action", sit.action_class),
        ]:
            if cls_name not in named_classes:
                missing.append(f"{role}:{cls_name}")

        if missing:
            results.append((sit.id, False, f"Missing classes in ontology: {', '.join(missing)}"))
        else:
            results.append((sit.id, True, "All situation classes successfully verified in ontology graph."))

    return results
