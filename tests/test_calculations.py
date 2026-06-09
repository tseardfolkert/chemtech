"""
tests/test_calculations.py — Unit tests voor de ChemTech Calculator Toolbox.
Uitvoeren met: pytest tests/
"""

import pytest
import sys
import os

# Voeg de hoofdmap toe aan het pad zodat calculations.py gevonden wordt
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from calculations import (
    calc_conversion,
    calc_density,
    calc_dilution,
    calc_heat_exchanger,
    calc_mass_balance,
    calc_moles,
    calc_neutralization,
    calc_reactor,
    calc_residence_time,
    calc_yield,
)


# =============================================================================
# Warmtewisselaar
# =============================================================================

class TestHeatExchanger:
    def test_basic(self):
        r = calc_heat_exchanger(3600, 4.18, 20, 80, 8, 0.25)
        # massastroom 3600 kg/h, ΔT = 60 K → Q = 3600 × 4.18 × 60 / 3600 = 250.8 kW
        assert abs(r["power_kw"] - 250.8) < 0.01
        assert r["delta_t"] == 60

    def test_energy_and_cost(self):
        r = calc_heat_exchanger(3600, 4.18, 20, 80, 8, 0.25)
        # 250.8 kW × 8 h = 2006.4 kWh/dag
        assert abs(r["energy_per_day"] - 2006.4) < 0.1
        assert abs(r["cost_per_day"] - 501.6) < 0.01

    def test_zero_mass_flow_raises(self):
        with pytest.raises(ValueError):
            calc_heat_exchanger(0, 4.18, 20, 80, 8, 0.25)

    def test_negative_cp_raises(self):
        with pytest.raises(ValueError):
            calc_heat_exchanger(100, -1, 20, 80, 8, 0.25)

    def test_equal_temperatures_raises(self):
        with pytest.raises(ValueError):
            calc_heat_exchanger(100, 4.18, 50, 50, 8, 0.25)

    def test_hours_out_of_range_raises(self):
        with pytest.raises(ValueError):
            calc_heat_exchanger(100, 4.18, 20, 80, 25, 0.25)

    def test_negative_price_raises(self):
        with pytest.raises(ValueError):
            calc_heat_exchanger(100, 4.18, 20, 80, 8, -0.10)


# =============================================================================
# Massabalans
# =============================================================================

class TestMassBalance:
    def test_balanced(self):
        r = calc_mass_balance(1000, 1000)
        assert r["difference"] == 0.0
        assert r["balanced"] is True

    def test_small_difference_balanced(self):
        r = calc_mass_balance(1000, 999.5)
        # 0.05% verschil → kleiner dan 0.1% → klopt
        assert r["balanced"] is True

    def test_unbalanced(self):
        r = calc_mass_balance(1000, 900)
        assert r["difference"] == 100
        assert abs(r["pct_difference"] - 10.0) < 0.001
        assert r["balanced"] is False

    def test_zero_mass_in_raises(self):
        with pytest.raises(ValueError):
            calc_mass_balance(0, 500)

    def test_negative_mass_out_raises(self):
        with pytest.raises(ValueError):
            calc_mass_balance(1000, -10)


# =============================================================================
# Rendement
# =============================================================================

class TestYield:
    def test_perfect_yield(self):
        r = calc_yield(500, 500)
        assert r["yield_pct"] == 100.0

    def test_normal_yield(self):
        r = calc_yield(500, 400)
        assert abs(r["yield_pct"] - 80.0) < 0.001

    def test_zero_yield(self):
        r = calc_yield(500, 0)
        assert r["yield_pct"] == 0.0

    def test_theoretical_zero_raises(self):
        with pytest.raises(ValueError):
            calc_yield(0, 100)

    def test_actual_greater_than_theoretical_raises(self):
        with pytest.raises(ValueError):
            calc_yield(100, 150)

    def test_negative_actual_raises(self):
        with pytest.raises(ValueError):
            calc_yield(100, -10)


# =============================================================================
# Conversie
# =============================================================================

class TestConversion:
    def test_full_conversion(self):
        r = calc_conversion(2.0, 0.0)
        assert r["conversion_pct"] == 100.0
        assert r["converted"] == 2.0

    def test_partial_conversion(self):
        r = calc_conversion(2.0, 0.4)
        assert abs(r["conversion_pct"] - 80.0) < 0.001
        assert abs(r["converted"] - 1.6) < 0.0001

    def test_no_conversion(self):
        r = calc_conversion(2.0, 2.0)
        assert r["conversion_pct"] == 0.0

    def test_initial_zero_raises(self):
        with pytest.raises(ValueError):
            calc_conversion(0, 0)

    def test_final_greater_raises(self):
        with pytest.raises(ValueError):
            calc_conversion(1.0, 1.5)


# =============================================================================
# Verblijftijd
# =============================================================================

class TestResidenceTime:
    def test_basic(self):
        r = calc_residence_time(200, 50)
        assert r["residence_time"] == 4.0

    def test_volume_zero_raises(self):
        with pytest.raises(ValueError):
            calc_residence_time(0, 50)

    def test_flow_zero_raises(self):
        with pytest.raises(ValueError):
            calc_residence_time(200, 0)


# =============================================================================
# Verdunning
# =============================================================================

class TestDilution:
    def test_basic(self):
        # C1=5, V1=0.1 → V2 = 5×0.1/0.5 = 1.0 L → toe te voegen = 0.9 L
        r = calc_dilution(5.0, 0.1, 0.5)
        assert abs(r["v2"] - 1.0) < 0.0001
        assert abs(r["solvent_to_add"] - 0.9) < 0.0001

    def test_c2_greater_than_c1_raises(self):
        with pytest.raises(ValueError):
            calc_dilution(1.0, 0.5, 2.0)

    def test_c1_zero_raises(self):
        with pytest.raises(ValueError):
            calc_dilution(0, 0.5, 0.1)

    def test_v1_zero_raises(self):
        with pytest.raises(ValueError):
            calc_dilution(5.0, 0, 0.5)


# =============================================================================
# Neutralisatie
# =============================================================================

class TestNeutralization:
    def test_hcl_naoh(self):
        # 0.5 L HCl 0.1 mol/L (n=1) + NaOH 0.1 mol/L (m=1)
        # mol zuur = 0.05, mol H+ = 0.05, V_base = 0.05/0.1 = 0.5 L
        r = calc_neutralization(0.5, 0.1, 1, 0.1, 1)
        assert abs(r["mol_acid"] - 0.05) < 1e-7
        assert abs(r["mol_h_plus"] - 0.05) < 1e-7
        assert abs(r["v_base"] - 0.5) < 1e-7

    def test_h2so4_naoh(self):
        # 0.1 L H2SO4 0.1 mol/L (n=2) + NaOH 0.2 mol/L (m=1)
        # mol zuur = 0.01, mol H+ = 0.02, V_base = 0.02/0.2 = 0.1 L
        r = calc_neutralization(0.1, 0.1, 2, 0.2, 1)
        assert abs(r["mol_acid"] - 0.01) < 1e-7
        assert abs(r["mol_h_plus"] - 0.02) < 1e-7
        assert abs(r["v_base"] - 0.1) < 1e-7

    def test_invalid_n_acid_raises(self):
        with pytest.raises(ValueError):
            calc_neutralization(0.5, 0.1, 4, 0.1, 1)

    def test_invalid_n_base_raises(self):
        with pytest.raises(ValueError):
            calc_neutralization(0.5, 0.1, 1, 0.1, 3)

    def test_zero_v_acid_raises(self):
        with pytest.raises(ValueError):
            calc_neutralization(0, 0.1, 1, 0.1, 1)


# =============================================================================
# Molmassa / mol
# =============================================================================

class TestMoles:
    def test_mass_to_mol(self):
        # 36 g water (M = 18 g/mol) → 2 mol
        r = calc_moles("mass_to_mol", 36, 18)
        assert abs(r["result"] - 2.0) < 1e-6

    def test_mol_to_mass(self):
        # 2 mol water (M = 18 g/mol) → 36 g
        r = calc_moles("mol_to_mass", 2, 18)
        assert abs(r["result"] - 36.0) < 1e-6

    def test_invalid_direction_raises(self):
        with pytest.raises(ValueError):
            calc_moles("unknown", 10, 18)

    def test_zero_molar_mass_raises(self):
        with pytest.raises(ValueError):
            calc_moles("mass_to_mol", 36, 0)

    def test_negative_value_raises(self):
        with pytest.raises(ValueError):
            calc_moles("mass_to_mol", -10, 18)


# =============================================================================
# Dichtheid
# =============================================================================

class TestDensity:
    def test_water(self):
        # 1 kg water in 1 L → dichtheid = 1.0
        r = calc_density(1.0, 1.0)
        assert r["density"] == 1.0

    def test_basic(self):
        r = calc_density(800, 1.0)
        assert r["density"] == 800.0

    def test_zero_mass_raises(self):
        with pytest.raises(ValueError):
            calc_density(0, 1.0)

    def test_zero_volume_raises(self):
        with pytest.raises(ValueError):
            calc_density(800, 0)


# =============================================================================
# Reactor
# =============================================================================

class TestReactor:
    def test_batch_process(self):
        r = calc_reactor("batch", "laag", "nee", "laag", 100, 20)
        assert "Batch" in r["reactor_type"]
        assert abs(r["residence_time"] - 5.0) < 0.0001

    def test_continuous_high_conversion_pfr(self):
        r = calc_reactor("continu", "hoog", "nee", "hoog", 100, 20)
        assert "PFR" in r["reactor_type"]

    def test_continuous_mixing_cstr(self):
        r = calc_reactor("continu", "middel", "ja", "middel", 100, 20)
        assert "CSTR" in r["reactor_type"]

    def test_zero_volume_raises(self):
        with pytest.raises(ValueError):
            calc_reactor("continu", "hoog", "nee", "hoog", 0, 20)

    def test_zero_flow_raises(self):
        with pytest.raises(ValueError):
            calc_reactor("continu", "hoog", "nee", "hoog", 100, 0)
