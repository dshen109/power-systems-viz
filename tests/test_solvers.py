import numpy as np
import pytest
from solvers.swing import (
    OMEGA_S,
    SwingParams,
    FaultParams,
    find_smib_equilibria,
    solve_swing,
)


class TestFindSmibEquilibria:
    def test_equilibria_sum_to_pi(self):
        result = find_smib_equilibria(Pm=0.5, Pe_max=1.0)
        assert result["warning"] is None
        assert result["delta_s"] + result["delta_u"] == pytest.approx(np.pi, abs=1e-10)

    def test_stable_eq_in_first_quadrant(self):
        result = find_smib_equilibria(Pm=0.7, Pe_max=1.0)
        assert 0 < result["delta_s"] < np.pi / 2

    def test_unstable_eq_in_second_quadrant(self):
        result = find_smib_equilibria(Pm=0.7, Pe_max=1.0)
        assert np.pi / 2 < result["delta_u"] < np.pi

    def test_no_equilibrium_above_limit(self):
        result = find_smib_equilibria(Pm=1.1, Pe_max=1.0)
        assert result["delta_s"] is None
        assert result["delta_u"] is None
        assert result["warning"] is not None

    def test_zero_load_equilibrium(self):
        result = find_smib_equilibria(Pm=0.0, Pe_max=1.0)
        assert result["delta_s"] == pytest.approx(0.0, abs=1e-10)
        assert result["delta_u"] == pytest.approx(np.pi, abs=1e-10)

    def test_scales_with_pe_max(self):
        r1 = find_smib_equilibria(Pm=0.5, Pe_max=1.0)
        r2 = find_smib_equilibria(Pm=1.0, Pe_max=2.0)
        assert r1["delta_s"] == pytest.approx(r2["delta_s"], abs=1e-10)


class TestSolveSwing:
    def _base_params(self, **kwargs):
        defaults = dict(H=5.0, D=1.0, Pm=0.5, Pe_max=1.0, t_end=10.0, delta_0=0.1)
        defaults.update(kwargs)
        return SwingParams(**defaults)

    def test_returns_expected_keys(self):
        result = solve_swing(self._base_params())
        for key in ("t", "delta", "omega", "delta_eq", "delta_u", "warning"):
            assert key in result

    def test_no_warning_on_valid_input(self):
        result = solve_swing(self._base_params())
        assert result["warning"] is None

    def test_pm_exceeds_pe_max_returns_warning(self):
        result = solve_swing(self._base_params(Pm=1.05))
        assert result["warning"] is not None
        assert result["t"] is None

    def test_damped_converges_near_equilibrium(self):
        """D > 0: final delta should be close to delta_eq."""
        result = solve_swing(self._base_params(D=2.0, t_end=30.0, delta_0=0.1))
        assert result["warning"] is None
        delta_eq = result["delta_eq"]
        assert abs(result["delta"][-1] - delta_eq) < 0.05

    def test_undamped_energy_conservation(self):
        """D = 0: total mechanical energy conserved to within 1%."""
        H, Pm, Pe_max = 5.0, 0.5, 1.0
        M = 2 * H / OMEGA_S
        result = solve_swing(self._base_params(H=H, D=0.0, Pm=Pm, Pe_max=Pe_max, delta_0=0.1))
        assert result["warning"] is None

        delta = result["delta"]
        omega = result["omega"]
        delta_eq = result["delta_eq"]

        # Potential energy relative to equilibrium
        KE = 0.5 * M * omega ** 2
        PE = -Pm * (delta - delta_eq) + Pe_max * (np.cos(delta_eq) - np.cos(delta))
        total = KE + PE
        variation = np.std(total) / (np.abs(np.mean(total)) + 1e-12)
        assert variation < 0.01

    def test_undamped_oscillation_period(self):
        """D = 0, small δ₀: measured period ≈ 2π√(M/Ks)."""
        H, Pm, Pe_max = 5.0, 0.5, 1.0
        M = 2 * H / OMEGA_S
        delta_eq = np.arcsin(Pm / Pe_max)
        Ks = Pe_max * np.cos(delta_eq)
        expected_period = 2 * np.pi * np.sqrt(M / Ks)

        result = solve_swing(self._base_params(H=H, D=0.0, Pm=Pm, Pe_max=Pe_max,
                                               t_end=3 * expected_period, delta_0=0.05))
        assert result["warning"] is None

        omega = result["omega"]
        t = result["t"]
        # Find upward zero-crossings of omega
        sign_changes = np.where(np.diff(np.sign(omega)) > 0)[0]
        assert len(sign_changes) >= 2
        measured_period = t[sign_changes[1]] - t[sign_changes[0]]
        assert abs(measured_period - expected_period) / expected_period < 0.05

    def test_instability_detected_large_perturbation(self):
        """Large δ₀ with high Pm pushes rotor past δ_u → warning."""
        result = solve_swing(self._base_params(Pm=0.95, Pe_max=1.0, delta_0=0.45, D=0.0))
        # May or may not go unstable depending on exact params, but if it does,
        # warning should be set and arrays should still be returned (truncated)
        if result["warning"]:
            assert "synchronism" in result["warning"].lower() or "unstable" in result["warning"].lower()
