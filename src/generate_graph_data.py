"""
Generate LPG nodes.csv and relationships.csv from IEC CIM energy system ontology.
Guarantees >= 100 nodes and >= 200 relationships with provenance.
"""
import csv
from pathlib import Path
import rdflib

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

def build_dataset():
    g = rdflib.Graph()
    kb_path = DATA_DIR / "kb.ttl"
    if kb_path.exists():
        g.parse(str(kb_path), format="turtle")

    nodes = []
    node_ids = set()

    def add_node(node_id, label, name, ntype="", voltage_kv=0.0, capacity_mw=0.0,
                 status="OPERATIONAL", dga_h2=0.0, dga_c2h2=0.0, freq=50.0,
                 fault_ka=0.0, demand_mw=0.0, dispatchable=True):
        if node_id in node_ids:
            return
        node_ids.add(node_id)
        nodes.append({
            "id": node_id,
            "label": label,
            "name": name,
            "type": ntype,
            "voltageKV": float(voltage_kv),
            "capacityMW": float(capacity_mw),
            "status": status,
            "dgaH2Ppm": float(dga_h2),
            "dgaC2H2Ppm": float(dga_c2h2),
            "gridFrequencyHz": float(freq),
            "faultCurrentKA": float(fault_ka),
            "demandMW": float(demand_mw),
            "dispatchable": str(dispatchable).lower()
        })

    relationships = []
    rel_set = set()

    def add_rel(start_id, end_id, rel_type, source="SCADA_EMS", confidence=1.0, valid_from="2026-01-01T00:00:00Z"):
        key = (start_id, end_id, rel_type)
        if key in rel_set:
            return
        rel_set.add(key)
        relationships.append({
            "start_id": start_id,
            "end_id": end_id,
            "type": rel_type,
            "source": source,
            "confidence": float(confidence),
            "validFrom": valid_from
        })

    # 1. Primary Substations (750 kV, 330 kV, 110 kV)
    substations = [
        ("SS_Zakhidnoukrainska_750", "ПС 750 кВ Західноукраїнська", 750.0, "Western"),
        ("SS_Vinnytska_750", "ПС 750 кВ Вінницька", 750.0, "Central"),
        ("SS_Kyivska_750", "ПС 750 кВ Київська", 750.0, "Northern"),
        ("SS_Pivdennoukrainska_750", "ПС 750 кВ Південноукраїнська", 750.0, "Southern"),
        ("SS_Dniprovska_750", "ПС 750 кВ Дніпровська", 750.0, "Dnipro"),
        ("SS_Zaporizka_750", "ПС 750 кВ Запорізька", 750.0, "Dnipro"),
        ("SS_Donbaska_750", "ПС 750 кВ Донбаська", 750.0, "Eastern"),
        ("SS_Khmelnytska_330", "ПС 330 кВ Хмельницька", 330.0, "Western"),
        ("SS_Rivnenska_330", "ПС 330 кВ Рівненська", 330.0, "Western"),
        ("SS_Lvivska_330", "ПС 330 кВ Львівська", 330.0, "Western"),
        ("SS_IvanoFrankivska_330", "ПС 330 кВ Івано-Франківська", 330.0, "Western"),
        ("SS_Ternopilska_330", "ПС 330 кВ Тернопільська", 330.0, "Western"),
        ("SS_Chernivecka_330", "ПС 330 кВ Чернівецька", 330.0, "Western"),
        ("SS_Zhytomyrska_330", "ПС 330 кВ Житомирська", 330.0, "Northern"),
        ("SS_Cherkaska_330", "ПС 330 кВ Черкаська", 330.0, "Central"),
        ("SS_Poltavska_330", "ПС 330 кВ Полтавська", 330.0, "Central"),
        ("SS_Kharkivska_330", "ПС 330 кВ Харківська", 330.0, "Eastern"),
        ("SS_Kremenchutska_330", "ПС 330 кВ Кременчуцька", 330.0, "Central"),
        ("SS_Kryvorizka_330", "ПС 330 кВ Криворізька", 330.0, "Dnipro"),
        ("SS_Mykolaivska_330", "ПС 330 кВ Миколаївська", 330.0, "Southern"),
        ("SS_Odeska_330", "ПС 330 кВ Одеська", 330.0, "Southern"),
        ("SS_Khersonska_330", "ПС 330 кВ Херсонська", 330.0, "Southern"),
        ("SS_Brovarska_110", "ПС 110 кВ Броварська", 110.0, "Northern"),
        ("SS_Fastivska_110", "ПС 110 кВ Фастівська", 110.0, "Northern"),
        ("SS_Stryiska_110", "ПС 110 кВ Стрийська", 110.0, "Western"),
        ("SS_Drohobytska_110", "ПС 110 кВ Дрогобицька", 110.0, "Western"),
        ("SS_Koziatyn_110", "ПС 110 кВ Козятинська", 110.0, "Central"),
        ("SS_Uman_110", "ПС 110 кВ Уманська", 110.0, "Central"),
        ("SS_Nikopol_110", "ПС 110 кВ Нікопольська", 110.0, "Dnipro"),
        ("SS_Pavlohrad_110", "ПС 110 кВ Павлоградська", 110.0, "Dnipro"),
    ]
    for sid, sname, skv, sreg in substations:
        add_node(sid, "Substation", sname, ntype="TransmissionSubstation", voltage_kv=skv, status="IN_SERVICE")

    # 2. Generating Units
    generators = [
        ("GEN_Khmelnytskyi_NPP1", "Хмельницька АЕС, Блок 1", "Nuclear", 750.0, 1000.0, True, "SS_Khmelnytska_330"),
        ("GEN_Khmelnytskyi_NPP2", "Хмельницька АЕС, Блок 2", "Nuclear", 750.0, 1000.0, True, "SS_Vinnytska_750"),
        ("GEN_Rivne_NPP1", "Рівненська АЕС, Блок 1", "Nuclear", 330.0, 420.0, True, "SS_Rivnenska_330"),
        ("GEN_Rivne_NPP2", "Рівненська АЕС, Блок 2", "Nuclear", 330.0, 420.0, True, "SS_Rivnenska_330"),
        ("GEN_Rivne_NPP3", "Рівненська АЕС, Блок 3", "Nuclear", 750.0, 1000.0, True, "SS_Zakhidnoukrainska_750"),
        ("GEN_SouthUkraine_NPP1", "Південноукраїнська АЕС, Блок 1", "Nuclear", 750.0, 1000.0, True, "SS_Pivdennoukrainska_750"),
        ("GEN_SouthUkraine_NPP2", "Південноукраїнська АЕС, Блок 2", "Nuclear", 750.0, 1000.0, True, "SS_Pivdennoukrainska_750"),
        ("GEN_Trypilska_TPP_U1", "Трипільська ТЕС, Блок 1", "Thermal", 330.0, 300.0, True, "SS_Kyivska_750"),
        ("GEN_Trypilska_TPP_U2", "Трипільська ТЕС, Блок 2", "Thermal", 330.0, 300.0, True, "SS_Kyivska_750"),
        ("GEN_Burshtyn_TPP_U1", "Бурштинська ТЕС, Блок 1", "Thermal", 330.0, 200.0, True, "SS_IvanoFrankivska_330"),
        ("GEN_Burshtyn_TPP_U2", "Бурштинська ТЕС, Блок 2", "Thermal", 330.0, 200.0, True, "SS_Zakhidnoukrainska_750"),
        ("GEN_Ladyzhyn_TPP_U1", "Ладижинська ТЕС, Блок 1", "Thermal", 330.0, 300.0, True, "SS_Vinnytska_750"),
        ("GEN_Ladyzhyn_TPP_U2", "Ладижинська ТЕС, Блок 2", "Thermal", 330.0, 300.0, True, "SS_Vinnytska_750"),
        ("GEN_Kryvorizka_TPP_U1", "Криворізька ТЕС, Блок 1", "Thermal", 330.0, 280.0, True, "SS_Kryvorizka_330"),
        ("GEN_Dnipro_HPP_U1", "Дніпровська ГЕС, Блок 1", "Hydro", 150.0, 75.0, True, "SS_Dniprovska_750"),
        ("GEN_Dnipro_HPP_U2", "Дніпровська ГЕС, Блок 2", "Hydro", 150.0, 75.0, True, "SS_Dniprovska_750"),
        ("GEN_Dniester_HPP_U1", "Дністровська ГЕС, Блок 1", "Hydro", 330.0, 117.0, True, "SS_Chernivecka_330"),
        ("GEN_Kakhovka_HPP_U1", "Каховська ГЕС (відн.), Блок 1", "Hydro", 150.0, 68.0, True, "SS_Khersonska_330"),
        ("GEN_Kremenchuk_HPP_U1", "Кременчуцька ГЕС, Блок 1", "Hydro", 330.0, 70.0, True, "SS_Kremenchutska_330"),
        ("GEN_Pokrovska_SES", "Покровська СЕС", "Solar", 150.0, 240.0, False, "SS_Vinnytska_750"),
        ("GEN_Kakhovka_SES", "Каховська СЕС", "Solar", 150.0, 120.0, False, "SS_Vinnytska_750"),
        ("GEN_Nikopol_SES", "Нікопольська СЕС", "Solar", 150.0, 200.0, False, "SS_Nikopol_110"),
        ("GEN_Bylbasivka_SES", "Билбасівська СЕС", "Solar", 110.0, 50.0, False, "SS_Donbaska_750"),
        ("GEN_Zaporizhia_WPP", "Запорізька ВЕС", "Wind", 150.0, 98.0, False, "SS_Vinnytska_750"),
        ("GEN_Tiligul_WPP_Ph1", "Тилігульська ВЕС, Фаза 1", "Wind", 330.0, 126.0, False, "SS_Mykolaivska_330"),
        ("GEN_Tiligul_WPP_Ph2", "Тилігульська ВЕС, Фаза 2", "Wind", 330.0, 150.0, False, "SS_Mykolaivska_330"),
        ("GEN_Dnistrovska_WPP", "Дністровська ВЕС", "Wind", 110.0, 60.0, False, "SS_Odeska_330"),
        ("GEN_Oryol_WPP", "Орлівська ВЕС", "Wind", 110.0, 100.0, False, "SS_Zaporizka_750"),
    ]
    for gid, gname, gtype, gkv, gmw, gdisp, gss in generators:
        add_node(gid, "GeneratingUnit", gname, ntype=gtype, voltage_kv=gkv, capacity_mw=gmw, dispatchable=gdisp)
        add_rel(gid, gss, "SUPPLIES_POWER_TO", source="CIM_Topology", confidence=1.0)

    # 3. Energy Storages (PSPS and BESS)
    storages = [
        ("STR_Dniester_PSPS_U1", "Дністровська ГАЕС, Гідроагрегат №1", "PSPS", 330.0, 324.0, 1200.0, "SS_Vinnytska_750"),
        ("STR_Dniester_PSPS_U2", "Дністровська ГАЕС, Гідроагрегат №2", "PSPS", 330.0, 324.0, 1200.0, "SS_Chernivecka_330"),
        ("STR_Kaniv_PSPS_U1", "Канівська ГАЕС, Гідроагрегат №1", "PSPS", 330.0, 250.0, 1000.0, "SS_Cherkaska_330"),
        ("STR_Kyiv_PSPS_U1", "Київська ГАЕС, Блок №1", "PSPS", 110.0, 45.0, 200.0, "SS_Kyivska_750"),
        ("STR_Tashlyk_PSPS_U1", "Ташлицька ГАЕС, Блок №1", "PSPS", 330.0, 150.0, 600.0, "SS_Pivdennoukrainska_750"),
        ("STR_BESS_Vinnytsia_50MW", "СНЕ Вінниця BESS", "BESS", 110.0, 50.0, 100.0, "SS_Vinnytska_750"),
        ("STR_BESS_Kyiv_100MW", "СНЕ Київ BESS", "BESS", 110.0, 100.0, 200.0, "SS_Kyivska_750"),
        ("STR_BESS_Dnipro_40MW", "СНЕ Дніпро BESS", "BESS", 110.0, 40.0, 80.0, "SS_Dniprovska_750"),
    ]
    for stid, stname, sttype, stkv, stmw, stmwh, stss in storages:
        add_node(stid, "EnergyStorage", stname, ntype=sttype, voltage_kv=stkv, capacity_mw=stmw, status="READY_FCR")
        add_rel(stid, stss, "SUPPLIES_POWER_TO", source="CIM_Topology", confidence=1.0)

    # 4. Transmission Lines
    lines = [
        ("LINE_750_Zakhidna_Vinnytska", "ПЛ 750 кВ Західноукраїнська - Вінницька", 750.0, "SS_Zakhidnoukrainska_750", "SS_Vinnytska_750"),
        ("LINE_750_Vinnytska_Kyivska", "ПЛ 750 кВ Вінницька - Київська", 750.0, "SS_Vinnytska_750", "SS_Kyivska_750"),
        ("LINE_750_Pivdenna_Vinnytska", "ПЛ 750 кВ Південноукраїнська - Вінницька", 750.0, "SS_Pivdennoukrainska_750", "SS_Vinnytska_750"),
        ("LINE_750_Pivdenna_Dniprovska", "ПЛ 750 кВ Південноукраїнська - Дніпровська", 750.0, "SS_Pivdennoukrainska_750", "SS_Dniprovska_750"),
        ("LINE_750_Dniprovska_Zaporizka", "ПЛ 750 кВ Дніпровська - Запорізька", 750.0, "SS_Dniprovska_750", "SS_Zaporizka_750"),
        ("LINE_750_Zaporizka_Donbaska", "ПЛ 750 кВ Запорізька - Донбаська", 750.0, "SS_Zaporizka_750", "SS_Donbaska_750"),
        ("LINE_750_Kyivska_Khmelnytska", "ПЛ 750 кВ Київська - Хмельницька АЕС", 750.0, "SS_Kyivska_750", "SS_Khmelnytska_330"),
        ("LINE_330_Zakhidna_Lvivska", "ПЛ 330 кВ Західноукраїнська - Львівська", 330.0, "SS_Zakhidnoukrainska_750", "SS_Lvivska_330"),
        ("LINE_330_Zakhidna_IvanoFrankivska", "ПЛ 330 кВ Західноукраїнська - Івано-Франківська", 330.0, "SS_Zakhidnoukrainska_750", "SS_IvanoFrankivska_330"),
        ("LINE_330_Lvivska_Rivnenska", "ПЛ 330 кВ Львівська - Рівненська", 330.0, "SS_Lvivska_330", "SS_Rivnenska_330"),
        ("LINE_330_Rivnenska_Khmelnytska", "ПЛ 330 кВ Рівненська - Хмельницька", 330.0, "SS_Rivnenska_330", "SS_Khmelnytska_330"),
        ("LINE_330_Khmelnytska_Ternopilska", "ПЛ 330 кВ Хмельницька - Тернопільська", 330.0, "SS_Khmelnytska_330", "SS_Ternopilska_330"),
        ("LINE_330_Ternopilska_Chernivecka", "ПЛ 330 кВ Тернопільська - Чернівецька", 330.0, "SS_Ternopilska_330", "SS_Chernivecka_330"),
        ("LINE_330_Chernivecka_Vinnytska", "ПЛ 330 кВ Чернівецька - Вінницька", 330.0, "SS_Chernivecka_330", "SS_Vinnytska_750"),
        ("LINE_330_Vinnytska_Zhytomyrska", "ПЛ 330 кВ Вінницька - Житомирська", 330.0, "SS_Vinnytska_750", "SS_Zhytomyrska_330"),
        ("LINE_330_Zhytomyrska_Kyivska", "ПЛ 330 кВ Житомирська - Київська", 330.0, "SS_Zhytomyrska_330", "SS_Kyivska_750"),
        ("LINE_330_Kyivska_Cherkaska", "ПЛ 330 кВ Київська - Черкаська", 330.0, "SS_Kyivska_750", "SS_Cherkaska_330"),
        ("LINE_330_Cherkaska_Kremenchutska", "ПЛ 330 кВ Черкаська - Кременчуцька", 330.0, "SS_Cherkaska_330", "SS_Kremenchutska_330"),
        ("LINE_330_Kremenchutska_Poltavska", "ПЛ 330 кВ Кременчуцька - Полтавська", 330.0, "SS_Kremenchutska_330", "SS_Poltavska_330"),
        ("LINE_330_Poltavska_Kharkivska", "ПЛ 330 кВ Полтавська - Харківська", 330.0, "SS_Poltavska_330", "SS_Kharkivska_330"),
        ("LINE_330_Kharkivska_Donbaska", "ПЛ 330 кВ Харківська - Донбаська", 330.0, "SS_Kharkivska_330", "SS_Donbaska_750"),
        ("LINE_330_Kremenchutska_Dniprovska", "ПЛ 330 кВ Кременчуцька - Дніпровська", 330.0, "SS_Kremenchutska_330", "SS_Dniprovska_750"),
        ("LINE_330_Dniprovska_Kryvorizka", "ПЛ 330 кВ Дніпровська - Криворізька", 330.0, "SS_Dniprovska_750", "SS_Kryvorizka_330"),
        ("LINE_330_Kryvorizka_Mykolaivska", "ПЛ 330 кВ Криворізька - Миколаївська", 330.0, "SS_Kryvorizka_330", "SS_Mykolaivska_330"),
        ("LINE_330_Mykolaivska_Odeska", "ПЛ 330 кВ Миколаївська - Одеська", 330.0, "SS_Mykolaivska_330", "SS_Odeska_330"),
        ("LINE_330_Mykolaivska_Khersonska", "ПЛ 330 кВ Миколаївська - Херсонська", 330.0, "SS_Mykolaivska_330", "SS_Khersonska_330"),
        ("LINE_330_Khersonska_Zaporizka", "ПЛ 330 кВ Херсонська - Запорізька", 330.0, "SS_Khersonska_330", "SS_Zaporizka_750"),
        ("LINE_110_Kyivska_Brovarska", "ПЛ 110 кВ Київська - Бровари", 110.0, "SS_Kyivska_750", "SS_Brovarska_110"),
        ("LINE_110_Kyivska_Fastivska", "ПЛ 110 кВ Київська - Фастів", 110.0, "SS_Kyivska_750", "SS_Fastivska_110"),
        ("LINE_110_Lvivska_Stryiska", "ПЛ 110 кВ Львівська - Стрий", 110.0, "SS_Lvivska_330", "SS_Stryiska_110"),
        ("LINE_110_Lvivska_Drohobytska", "ПЛ 110 кВ Львівська - Дрогобич", 110.0, "SS_Lvivska_330", "SS_Drohobytska_110"),
        ("LINE_110_Vinnytska_Koziatyn", "ПЛ 110 кВ Вінницька - Козятин", 110.0, "SS_Vinnytska_750", "SS_Koziatyn_110"),
        ("LINE_110_Cherkaska_Uman", "ПЛ 110 кВ Черкаська - Умань", 110.0, "SS_Cherkaska_330", "SS_Uman_110"),
        ("LINE_110_Zaporizka_Nikopol", "ПЛ 110 кВ Запорізька - Нікополь", 110.0, "SS_Zaporizka_750", "SS_Nikopol_110"),
        ("LINE_110_Dniprovska_Pavlohrad", "ПЛ 110 кВ Дніпровська - Павлоград", 110.0, "SS_Dniprovska_750", "SS_Pavlohrad_110"),
    ]
    for lid, lname, lkv, s1, s2 in lines:
        add_node(lid, "TransmissionLine", lname, ntype="OverheadLine", voltage_kv=lkv, status="ENERGIZED")
        add_rel(s1, lid, "CONNECTED_TO", source="EMS_Topology", confidence=1.0)
        add_rel(lid, s2, "CONNECTED_TO", source="EMS_Topology", confidence=1.0)
        # Add reciprocal topological connectivity between substations
        add_rel(s1, s2, "CONNECTED_TO", source="Grid_Topology", confidence=1.0)
        add_rel(s2, s1, "CONNECTED_TO", source="Grid_Topology", confidence=1.0)

    # 5. Power Transformers & Autotransformers
    transformers = [
        ("TR_AT1_Zakhidna", "Автотрансформатор АТ-1 750/330 кВ Західноукраїнська", 750.0, 330.0, 145.0, 12.4, "ALARM", "SS_Zakhidnoukrainska_750"),
        ("TR_AT2_Zakhidna", "Автотрансформатор АТ-2 750/330 кВ Західноукраїнська", 750.0, 330.0, 25.0, 0.4, "NORMAL", "SS_Zakhidnoukrainska_750"),
        ("TR_AT1_Vinnytska", "Автотрансформатор АТ-1 750/330 кВ Вінницька", 750.0, 330.0, 30.0, 0.2, "NORMAL", "SS_Vinnytska_750"),
        ("TR_AT2_Vinnytska", "Автотрансформатор АТ-2 750/330 кВ Вінницька", 750.0, 330.0, 28.0, 0.1, "NORMAL", "SS_Vinnytska_750"),
        ("TR_AT1_Kyivska", "Автотрансформатор АТ-1 750/330 кВ Київська", 750.0, 330.0, 45.0, 0.5, "NORMAL", "SS_Kyivska_750"),
        ("TR_AT2_Kyivska", "Автотрансформатор АТ-2 750/330 кВ Київська", 750.0, 330.0, 110.0, 6.2, "WARNING", "SS_Kyivska_750"),
        ("TR_AT1_Dniprovska", "Автотрансформатор АТ-1 750/330 кВ Дніпровська", 750.0, 330.0, 22.0, 0.1, "NORMAL", "SS_Dniprovska_750"),
        ("TR_AT1_Zaporizka", "Автотрансформатор АТ-1 750/330 кВ Запорізька", 750.0, 330.0, 38.0, 0.3, "NORMAL", "SS_Zaporizka_750"),
        ("TR_AT1_Pivdenna", "Автотрансформатор АТ-1 750/330 кВ Південна", 750.0, 330.0, 18.0, 0.1, "NORMAL", "SS_Pivdennoukrainska_750"),
        ("TR_T1_Khmelnytska", "Трансформатор Т-1 330/110 кВ Хмельницька", 330.0, 110.0, 15.0, 0.1, "NORMAL", "SS_Khmelnytska_330"),
        ("TR_T1_Rivnenska", "Трансформатор Т-1 330/110 кВ Рівненська", 330.0, 110.0, 20.0, 0.2, "NORMAL", "SS_Rivnenska_330"),
        ("TR_T1_Lvivska", "Трансформатор Т-1 330/110 кВ Львівська", 330.0, 110.0, 42.0, 0.4, "NORMAL", "SS_Lvivska_330"),
        ("TR_T1_Cherkaska", "Трансформатор Т-1 330/110 кВ Черкаська", 330.0, 110.0, 33.0, 0.3, "NORMAL", "SS_Cherkaska_330"),
        ("TR_T1_Poltavska", "Трансформатор Т-1 330/110 кВ Полтавська", 330.0, 110.0, 19.0, 0.1, "NORMAL", "SS_Poltavska_330"),
        ("TR_T1_Kharkivska", "Трансформатор Т-1 330/110 кВ Харківська", 330.0, 110.0, 65.0, 0.8, "NORMAL", "SS_Kharkivska_330"),
        ("TR_T1_Kryvorizka", "Трансформатор Т-1 330/110 кВ Криворізька", 330.0, 110.0, 125.0, 7.5, "ALARM", "SS_Kryvorizka_330"),
        ("TR_T1_Mykolaivska", "Трансформатор Т-1 330/110 кВ Миколаївська", 330.0, 110.0, 25.0, 0.2, "NORMAL", "SS_Mykolaivska_330"),
        ("TR_T1_Odeska", "Трансформатор Т-1 330/110 кВ Одеська", 330.0, 110.0, 31.0, 0.2, "NORMAL", "SS_Odeska_330"),
    ]
    for tid, tname, pkv, skv, h2, c2h2, st, tss in transformers:
        add_node(tid, "Transformer", tname, ntype="Autotransformer" if pkv == 750 else "PowerTransformer",
                 voltage_kv=pkv, status=st, dga_h2=h2, dga_c2h2=c2h2)
        add_rel(tid, tss, "INSTALLED_AT", source="Substation_Asset_DB", confidence=1.0)
        add_rel(tid, tss, "STEPS_VOLTAGE", source="Technical_Passport", confidence=1.0)

    # 6. Protection Devices (Relay Protection & Automation)
    protections = [
        ("PROT_Relay_Line750_Zakhidna", "РЗА захисту ПЛ 750 Західна-Вінницька", "DifferentialLine", 45, "LINE_750_Zakhidna_Vinnytska", "SS_Zakhidnoukrainska_750"),
        ("PROT_Relay_Line750_Vinnytska", "РЗА захисту ПЛ 750 Вінницька-Київська", "DifferentialLine", 50, "LINE_750_Vinnytska_Kyivska", "SS_Vinnytska_750"),
        ("PROT_Relay_Line750_Pivdenna", "РЗА захисту ПЛ 750 Південна-Вінницька", "DistanceProtection", 65, "LINE_750_Pivdenna_Vinnytska", "SS_Pivdennoukrainska_750"),
        ("PROT_Relay_Line750_Dniprovska", "РЗА захисту ПЛ 750 Південна-Дніпровська", "DistanceProtection", 55, "LINE_750_Pivdenna_Dniprovska", "SS_Dniprovska_750"),
        ("PROT_Relay_Line750_Zaporizka", "РЗА захисту ПЛ 750 Дніпровська-Запорізька", "DifferentialLine", 40, "LINE_750_Dniprovska_Zaporizka", "SS_Zaporizka_750"),
        ("PROT_Overcurrent_AT1_Zakhidna", "МТЗ автотрансформатора АТ-1 Західна", "Overcurrent", 120, "TR_AT1_Zakhidna", "SS_Zakhidnoukrainska_750"),
        ("PROT_Diff_AT2_Vinnytska", "Диференційний захист АТ-2 Вінницька", "DifferentialTransformer", 35, "TR_AT2_Vinnytska", "SS_Vinnytska_750"),
        ("PROT_GasRelay_AT2_Kyivska", "Газове реле Бухгольца АТ-2 Київська", "GasProtection", 200, "TR_AT2_Kyivska", "SS_Kyivska_750"),
        ("PROT_FCR_Vinnytsia_Auto", "Автоматика ЧРП / FCR Вінницького вузла", "FrequencyProtection", 100, None, "SS_Vinnytska_750"),
        ("PROT_FCR_Kyiv_Auto", "Автоматика ЧРП / FCR Київського вузла", "FrequencyProtection", 90, None, "SS_Kyivska_750"),
        ("PROT_FCR_Dnipro_Auto", "Автоматика ЧРП / FCR Дніпровського вузла", "FrequencyProtection", 95, None, "SS_Dniprovska_750"),
        ("PROT_Relay_Line330_Lviv", "Дистанційний захист ПЛ 330 Західна-Львів", "DistanceProtection", 60, "LINE_330_Zakhidna_Lvivska", "SS_Lvivska_330"),
        ("PROT_Relay_Line330_Rivnenska", "Дистанційний захист ПЛ 330 Львів-Рівне", "DistanceProtection", 60, "LINE_330_Lvivska_Rivnenska", "SS_Rivnenska_330"),
        ("PROT_Relay_Line330_Cherkaska", "Дистанційний захист ПЛ 330 Київ-Черкаси", "DistanceProtection", 65, "LINE_330_Kyivska_Cherkaska", "SS_Cherkaska_330"),
        ("PROT_Relay_Line330_Kharkiv", "Дистанційний захист ПЛ 330 Полтава-Харків", "DistanceProtection", 70, "LINE_330_Poltavska_Kharkivska", "SS_Kharkivska_330"),
    ]
    for pid, pname, ptype, ptime, passet, pss in protections:
        add_node(pid, "ProtectionDevice", pname, ntype=ptype, status="ACTIVE", dga_h2=ptime)
        add_rel(pid, pss, "INSTALLED_AT", source="Protection_Asset_DB", confidence=1.0)
        if passet:
            add_rel(pid, passet, "PROTECTS", source="Relay_Settings", confidence=1.0)

    # Link frequency protection to storage units
    add_rel("PROT_FCR_Vinnytsia_Auto", "STR_Dniester_PSPS_U1", "ACTIVATES_STORAGE", source="Automatic_FCR", confidence=0.98)
    add_rel("PROT_FCR_Vinnytsia_Auto", "STR_BESS_Vinnytsia_50MW", "ACTIVATES_STORAGE", source="Automatic_FCR", confidence=0.99)
    add_rel("PROT_FCR_Kyiv_Auto", "STR_Kyiv_PSPS_U1", "ACTIVATES_STORAGE", source="Automatic_FCR", confidence=0.98)
    add_rel("PROT_FCR_Kyiv_Auto", "STR_BESS_Kyiv_100MW", "ACTIVATES_STORAGE", source="Automatic_FCR", confidence=0.99)
    add_rel("PROT_FCR_Dnipro_Auto", "STR_BESS_Dnipro_40MW", "ACTIVATES_STORAGE", source="Automatic_FCR", confidence=0.99)

    # 7. System Fault Events
    faults = [
        ("FAULT_SC_Line750_Zakhidna", "Міжфазне КЗ на ПЛ 750 Західна-Вінницька", "ShortCircuit", "LINE_750_Zakhidna_Vinnytska", 24.5, 50.0, "PROT_Relay_Line750_Zakhidna"),
        ("FAULT_SC_Line750_Kyivska", "Однофазне КЗ на ПЛ 750 Вінницька-Київська", "ShortCircuit", "LINE_750_Vinnytska_Kyivska", 19.8, 50.0, "PROT_Relay_Line750_Vinnytska"),
        ("FAULT_FreqDrop_4988", "Глибоке відхилення частоти в ОЕС України (49.88 Гц)", "FrequencyDeviation", None, 0.0, 49.88, "PROT_FCR_Vinnytsia_Auto"),
        ("FAULT_FreqDrop_4982", "Аварійне зниження частоти ОЕС (49.82 Гц)", "FrequencyDeviation", None, 0.0, 49.82, "PROT_FCR_Kyiv_Auto"),
        ("FAULT_Overheat_AT1_Zakhidna", "Високотемпературний перегрів АТ-1 Західна", "ThermalOverheat", "TR_AT1_Zakhidna", 0.0, 50.0, "PROT_Overcurrent_AT1_Zakhidna"),
        ("FAULT_GasAlarm_AT2_Kyivska", "Газоутворення та розряди в маслі АТ-2 Київська", "GasAlarm", "TR_AT2_Kyivska", 0.0, 50.0, "PROT_GasRelay_AT2_Kyivska"),
        ("FAULT_SC_Line330_Lviv", "Коротке замикання ПЛ 330 Західна-Львів", "ShortCircuit", "LINE_330_Zakhidna_Lvivska", 14.2, 50.0, "PROT_Relay_Line330_Lviv"),
        ("FAULT_SC_Line330_Kharkiv", "Грозове перекриття ПЛ 330 Полтава-Харків", "ShortCircuit", "LINE_330_Poltavska_Kharkivska", 16.5, 50.0, "PROT_Relay_Line330_Kharkiv"),
    ]
    for fid, fname, ftype, ftarget, fka, fhz, fprot in faults:
        add_node(fid, "FaultEvent", fname, ntype=ftype, fault_ka=fka, freq=fhz, status="CLEARED")
        if ftarget:
            add_rel(fid, ftarget, "AFFECTS_ASSET", source="Fault_Recorder", confidence=0.99)
        if fprot:
            add_rel(fid, fprot, "TRIGGERS_ACTION", source="Protection_Telemetry", confidence=1.0)

    # 8. Industrial Power Consumers (Large Loads)
    consumers = [
        ("LOAD_ArcelorMittal_KryvyiRih", "АрселорМіттал Кривий Ріг", 330.0, 450.0, "SS_Kryvorizka_330"),
        ("LOAD_DniproAzot", "ДніпроАзот, Кам'янське", 330.0, 180.0, "SS_Dniprovska_750"),
        ("LOAD_Zaporizhstal", "Металургійний комбінат Запоріжсталь", 330.0, 280.0, "SS_Zaporizka_750"),
        ("LOAD_Kyiv_Metropolitan", "КП Київський метрополітен та електротранспорт", 110.0, 95.0, "SS_Kyivska_750"),
        ("LOAD_Lviv_Railway_Hub", "Львівський залізничний вузол Укрзалізниці", 110.0, 85.0, "SS_Lvivska_330"),
        ("LOAD_Kharkiv_Industrial", "Харківський промисловий вузол", 330.0, 220.0, "SS_Kharkivska_330"),
        ("LOAD_Odesa_Port_Plant", "Одеський припортовий завод", 330.0, 160.0, "SS_Odeska_330"),
        ("LOAD_Mykolaiv_Shipyard", "Миколаївський промисловий суднобудівний кластер", 110.0, 75.0, "SS_Mykolaivska_330"),
        ("LOAD_Poltava_GOK", "Полтавський гірничо-збагачувальний комбінат", 330.0, 140.0, "SS_Poltavska_330"),
        ("LOAD_Vinnytsia_Cluster", "Вінницький агропромисловий індустріальний парк", 110.0, 65.0, "SS_Vinnytska_750"),
        ("LOAD_Brovary_TechPark", "Броварський логістично-технологічний комплекс", 110.0, 45.0, "SS_Brovarska_110"),
        ("LOAD_Cherkasy_Azot", "ПрАТ Азот Черкаси", 330.0, 210.0, "SS_Cherkaska_330"),
    ]
    for cid, cname, ckv, cdemand, css in consumers:
        add_node(cid, "PowerConsumer", cname, ntype="HeavyIndustrial", voltage_kv=ckv, demand_mw=cdemand, status="CONNECTED")
        add_rel(css, cid, "FEEDS_LOAD", source="Distribution_Meter", confidence=1.0)

    # Save to CSV
    nodes_csv = DATA_DIR / "nodes.csv"
    with open(nodes_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "id", "label", "name", "type", "voltageKV", "capacityMW",
            "status", "dgaH2Ppm", "dgaC2H2Ppm", "gridFrequencyHz",
            "faultCurrentKA", "demandMW", "dispatchable"
        ])
        writer.writeheader()
        writer.writerows(nodes)

    rels_csv = DATA_DIR / "relationships.csv"
    with open(rels_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "start_id", "end_id", "type", "source", "confidence", "validFrom"
        ])
        writer.writeheader()
        writer.writerows(relationships)

    print(f"Generated {len(nodes)} nodes in {nodes_csv}")
    print(f"Generated {len(relationships)} relationships in {rels_csv}")
    assert len(nodes) >= 100, f"Expected >= 100 nodes, got {len(nodes)}"
    assert len(relationships) >= 200, f"Expected >= 200 relationships, got {len(relationships)}"

if __name__ == "__main__":
    build_dataset()
