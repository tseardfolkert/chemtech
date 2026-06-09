"""
calculations.py — Alle berekenfuncties voor de ChemTech Calculator Toolbox.
Elke functie geeft een dict terug met de resultaten of gooit een ValueError
bij ongeldige invoer.
"""


def calc_heat_exchanger(mass_flow, cp, t_in, t_out, hours_per_day, energy_price):
    """
    Warmtewisselaar energiecalculator.
    Q = m · Cp · ΔT
    mass_flow: kg/h | cp: kJ/(kg·K) | temps: °C | hours_per_day: h | price: €/kWh
    """
    if mass_flow <= 0:
        raise ValueError("Massastroom moet groter zijn dan 0 kg/h.")
    if cp <= 0:
        raise ValueError("Soortelijke warmte Cp moet groter zijn dan 0 kJ/kg·K.")
    if hours_per_day <= 0 or hours_per_day > 24:
        raise ValueError("Bedrijfsuren per dag moeten tussen 0 en 24 liggen.")
    if energy_price < 0:
        raise ValueError("Energieprijs kan niet negatief zijn.")
    if t_in == t_out:
        raise ValueError("Begin- en eindtemperatuur zijn gelijk — er is geen warmteoverdracht.")

    delta_t = abs(t_out - t_in)
    # Q in kJ/h → omrekenen naar kW: delen door 3600 s/h × 1000 J/kJ = / 3.6
    power_kw = (mass_flow * cp * delta_t) / 3600  # kW
    energy_per_day = power_kw * hours_per_day       # kWh/dag
    cost_per_day = energy_per_day * energy_price    # €/dag

    return {
        "delta_t": round(delta_t, 2),
        "power_kw": round(power_kw, 3),
        "energy_per_day": round(energy_per_day, 3),
        "cost_per_day": round(cost_per_day, 4),
    }


def calc_reactor(batch_or_continuous, production_level, mixing_needed,
                 conversion_level, volume, flow_rate):
    """
    Reactor keuzehulp.
    Geeft een aanbeveling (Batchreactor / CSTR / PFR) + uitleg + verblijftijd.
    """
    if volume <= 0:
        raise ValueError("Reactorvolume moet groter zijn dan 0 L.")
    if flow_rate <= 0:
        raise ValueError("Debiet moet groter zijn dan 0 L/h.")

    residence_time = volume / flow_rate  # uur

    # Eenvoudige beslislogica
    if batch_or_continuous == "batch":
        reactor_type = "Batchreactor"
        explanation = (
            "Een batchreactor past goed bij een batchproces. Je laadt de reactor, "
            "laat de reactie verlopen en leegt hem daarna. Geschikt voor kleine producties "
            "of als je flexibiliteit nodig hebt."
        )
    else:
        if conversion_level == "hoog":
            reactor_type = "PFR (Plugstroomreactor)"
            explanation = (
                "Een PFR behaalt hoge conversie efficiënt omdat er geen terugmenging is. "
                "De concentratie daalt geleidelijk langs de lengte van de reactor. "
                "Geschikt voor continue processen met hoge conversie-eisen."
            )
        elif mixing_needed == "ja":
            reactor_type = "CSTR (Continue Geroerde Tank)"
            explanation = (
                "Als menging nodig is, is een CSTR de logische keuze. "
                "De inhoud is homogeen door intensief roeren. "
                "Eenvoudig te regelen, maar de conversie per volume is lager dan bij een PFR."
            )
        else:
            if production_level == "hoog":
                reactor_type = "PFR (Plugstroomreactor)"
                explanation = (
                    "Voor hoge productie in een continu proces biedt de PFR een goede "
                    "volume-efficiëntie zonder dat menging vereist is."
                )
            else:
                reactor_type = "CSTR (Continue Geroerde Tank)"
                explanation = (
                    "Voor een continu proces met lage of middelhoge productie is een CSTR "
                    "eenvoudig te ontwerpen en te bedrijven."
                )

    return {
        "reactor_type": reactor_type,
        "explanation": explanation,
        "residence_time": round(residence_time, 4),
    }


def calc_mass_balance(mass_in, mass_out):
    """
    Massabalans: verschil en procentueel verschil.
    """
    if mass_in <= 0:
        raise ValueError("Massa in moet groter zijn dan 0.")
    if mass_out < 0:
        raise ValueError("Massa uit kan niet negatief zijn.")

    difference = mass_in - mass_out
    pct_difference = (difference / mass_in) * 100
    balanced = abs(pct_difference) < 0.1  # kleiner dan 0,1% → klopt

    return {
        "difference": round(difference, 4),
        "pct_difference": round(pct_difference, 4),
        "balanced": balanced,
    }


def calc_yield(theoretical, actual):
    """
    Rendement = (werkelijk / theoretisch) × 100 %
    """
    if theoretical <= 0:
        raise ValueError("Theoretische opbrengst moet groter zijn dan 0.")
    if actual < 0:
        raise ValueError("Werkelijke opbrengst kan niet negatief zijn.")
    if actual > theoretical:
        raise ValueError("Werkelijke opbrengst kan niet groter zijn dan de theoretische opbrengst.")

    yield_pct = (actual / theoretical) * 100

    return {"yield_pct": round(yield_pct, 4)}


def calc_conversion(initial, final):
    """
    Conversie = (begin − eind) / begin × 100 %
    """
    if initial <= 0:
        raise ValueError("Beginhoeveelheid reactant moet groter zijn dan 0.")
    if final < 0:
        raise ValueError("Eindhoeveelheid reactant kan niet negatief zijn.")
    if final > initial:
        raise ValueError("Eindhoeveelheid kan niet groter zijn dan de beginhoeveelheid.")

    converted = initial - final
    conversion_pct = (converted / initial) * 100

    return {
        "converted": round(converted, 6),
        "conversion_pct": round(conversion_pct, 4),
    }


def calc_residence_time(volume, flow_rate):
    """
    Verblijftijd τ = V / Q
    """
    if volume <= 0:
        raise ValueError("Reactorvolume moet groter zijn dan 0.")
    if flow_rate <= 0:
        raise ValueError("Debiet moet groter zijn dan 0.")

    tau = volume / flow_rate

    return {"residence_time": round(tau, 6)}


def calc_dilution(c1, v1, c2):
    """
    Verdunning: C1·V1 = C2·V2  →  V2 = (C1·V1) / C2
    """
    if c1 <= 0:
        raise ValueError("Beginconcentratie C1 moet groter zijn dan 0.")
    if v1 <= 0:
        raise ValueError("Beginvolume V1 moet groter zijn dan 0.")
    if c2 <= 0:
        raise ValueError("Eindconcentratie C2 moet groter zijn dan 0.")
    if c2 > c1:
        raise ValueError("Eindconcentratie C2 mag niet groter zijn dan beginconcentratie C1 — dit is geen verdunning.")

    v2 = (c1 * v1) / c2
    solvent_to_add = v2 - v1

    return {
        "v2": round(v2, 6),
        "solvent_to_add": round(solvent_to_add, 6),
    }


def calc_neutralization(v_acid, c_acid, n_acid, c_base, n_base):
    """
    pH-neutralisatie voor sterke zuren/basen.
    mol zuur = c_acid × v_acid (v in liter)
    mol H+ = mol_acid × n_acid
    benodigd mol OH- = mol H+
    V_base = mol_H+ / (c_base × n_base)
    """
    if v_acid <= 0:
        raise ValueError("Volume zuur moet groter zijn dan 0 L.")
    if c_acid <= 0:
        raise ValueError("Concentratie zuur moet groter zijn dan 0 mol/L.")
    if c_base <= 0:
        raise ValueError("Concentratie base moet groter zijn dan 0 mol/L.")
    if n_acid not in (1, 2, 3):
        raise ValueError("Zuur-factor moet 1, 2 of 3 zijn.")
    if n_base not in (1, 2):
        raise ValueError("Base-factor moet 1 of 2 zijn.")

    mol_acid = c_acid * v_acid
    mol_h_plus = mol_acid * n_acid
    v_base = mol_h_plus / (c_base * n_base)

    return {
        "mol_acid": round(mol_acid, 6),
        "mol_h_plus": round(mol_h_plus, 6),
        "v_base": round(v_base, 6),
    }


def calc_moles(direction, value, molar_mass):
    """
    Molmassa / mol calculator.
    direction: 'mass_to_mol' of 'mol_to_mass'
    n = m / M  of  m = n × M
    """
    if value <= 0:
        raise ValueError("De ingevoerde waarde moet groter zijn dan 0.")
    if molar_mass <= 0:
        raise ValueError("Molmassa moet groter zijn dan 0 g/mol.")

    if direction == "mass_to_mol":
        result = value / molar_mass
        result_label = "Aantal mol (mol)"
    elif direction == "mol_to_mass":
        result = value * molar_mass
        result_label = "Massa (g)"
    else:
        raise ValueError("Ongeldige richting. Kies 'mass_to_mol' of 'mol_to_mass'.")

    return {
        "result": round(result, 6),
        "result_label": result_label,
    }


def calc_density(mass, volume):
    """
    Dichtheid ρ = m / V
    """
    if mass <= 0:
        raise ValueError("Massa moet groter zijn dan 0.")
    if volume <= 0:
        raise ValueError("Volume moet groter zijn dan 0.")

    density = mass / volume

    return {"density": round(density, 6)}
