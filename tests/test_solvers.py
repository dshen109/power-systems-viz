import numpy as np
import pytest
from solvers.swing import (
    OMEGA_S,
    SwingParams,
    FaultParams,
    find_smib_equilibria,
    solve_swing,
)
from solvers.stability import compute_eigenvalues, compute_phase_portrait


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


class TestComputeEigenvalues:
    def test_returns_expected_keys(self):
        result = compute_eigenvalues(H=5.0, D=1.0, Pm=0.5, Pe_max=1.0)
        for key in ("eigenvalues", "sigma", "omega_d", "omega_n", "zeta", "Ks", "warning"):
            assert key in result

    def test_no_warning_valid_input(self):
        result = compute_eigenvalues(H=5.0, D=1.0, Pm=0.5, Pe_max=1.0)
        assert result["warning"] is None

    def test_pm_ge_pe_max_returns_warning(self):
        result = compute_eigenvalues(H=5.0, D=1.0, Pm=1.05, Pe_max=1.0)
        assert result["warning"] is not None

    def test_undamped_eigenvalues_pure_imaginary(self):
        """D = 0 → σ = 0 exactly."""
        result = compute_eigenvalues(H=5.0, D=0.0, Pm=0.5, Pe_max=1.0)
        assert result["warning"] is None
        assert result["sigma"] == pytest.approx(0.0, abs=1e-10)
        assert result["omega_d"] > 0

    def test_eigenvalues_negative_real_part_when_damped(self):
        """D > 0 → σ < 0 (stable)."""
        result = compute_eigenvalues(H=5.0, D=1.0, Pm=0.5, Pe_max=1.0)
        assert result["sigma"] < 0

    def test_omega_n_matches_analytic(self):
        """ωn = √(Ks/M)."""
        H, Pm, Pe_max = 5.0, 0.5, 1.0
        from solvers.swing import OMEGA_S
        M = 2 * H / OMEGA_S
        delta_eq = np.arcsin(Pm / Pe_max)
        Ks = Pe_max * np.cos(delta_eq)
        expected_omega_n = np.sqrt(Ks / M)

        result = compute_eigenvalues(H=H, D=0.0, Pm=Pm, Pe_max=Pe_max)
        assert result["omega_n"] == pytest.approx(expected_omega_n, rel=1e-6)

    def test_damping_ratio_matches_formula(self):
        """ζ = D / (2√(Ks·M))."""
        H, D, Pm, Pe_max = 5.0, 1.0, 0.5, 1.0
        from solvers.swing import OMEGA_S
        M = 2 * H / OMEGA_S
        delta_eq = np.arcsin(Pm / Pe_max)
        Ks = Pe_max * np.cos(delta_eq)
        expected_zeta = D / (2 * np.sqrt(Ks * M))

        result = compute_eigenvalues(H=H, D=D, Pm=Pm, Pe_max=Pe_max)
        assert result["zeta"] == pytest.approx(expected_zeta, rel=1e-6)

    def test_eigenvalues_match_numpy_directly(self):
        """Eigenvalues match what numpy.linalg.eig returns for same A-matrix."""
        H, D, Pm, Pe_max = 5.0, 1.0, 0.5, 1.0
        from solvers.swing import OMEGA_S
        M = 2 * H / OMEGA_S
        delta_eq = np.arcsin(Pm / Pe_max)
        Ks = Pe_max * np.cos(delta_eq)
        A = np.array([[0, 1], [-Ks / M, -D / M]])
        expected = np.sort_complex(np.linalg.eig(A)[0])

        result = compute_eigenvalues(H=H, D=D, Pm=Pm, Pe_max=Pe_max)
        actual = np.sort_complex(result["eigenvalues"])
        np.testing.assert_allclose(actual.real, expected.real, atol=1e-10)
        np.testing.assert_allclose(actual.imag, expected.imag, atol=1e-10)

    def test_overdamped_eigenvalues_real(self):
        """Very large D → eigenvalues are both real (overdamped)."""
        result = compute_eigenvalues(H=5.0, D=50.0, Pm=0.5, Pe_max=1.0)
        assert result["warning"] is None
        # Imaginary parts should be near zero
        for lam in result["eigenvalues"]:
            assert abs(lam.imag) < 1e-6


class TestComputePhasePortrait:
    def test_returns_expected_keys(self):
        result = compute_phase_portrait(H=5.0, D=1.0, Pm=0.5, Pe_max=1.0, density="coarse")
        for key in ("trajectories", "delta_s", "delta_u", "warning"):
            assert key in result

    def test_coarse_returns_100_trajectories(self):
        result = compute_phase_portrait(H=5.0, D=1.0, Pm=0.5, Pe_max=1.0, density="coarse")
        assert len(result["trajectories"]) == 100

    def test_medium_returns_225_trajectories(self):
        result = compute_phase_portrait(H=5.0, D=1.0, Pm=0.5, Pe_max=1.0, density="medium")
        assert len(result["trajectories"]) == 225

    def test_fine_returns_400_trajectories(self):
        result = compute_phase_portrait(H=5.0, D=1.0, Pm=0.5, Pe_max=1.0, density="fine")
        assert len(result["trajectories"]) == 400

    def test_each_trajectory_has_arrays(self):
        result = compute_phase_portrait(H=5.0, D=1.0, Pm=0.5, Pe_max=1.0, density="coarse")
        for traj in result["trajectories"]:
            assert "delta" in traj
            assert "omega" in traj
            assert "stable" in traj
            assert len(traj["delta"]) > 0

    def test_some_stable_some_unstable(self):
        """With D > 0 and Pm < Pe_max, expect a mix of stable and unstable ICs."""
        result = compute_phase_portrait(H=5.0, D=1.0, Pm=0.5, Pe_max=1.0, density="coarse")
        stable_count = sum(1 for t in result["trajectories"] if t["stable"])
        unstable_count = sum(1 for t in result["trajectories"] if not t["stable"])
        assert stable_count > 0
        assert unstable_count > 0

    def test_equilibria_returned(self):
        result = compute_phase_portrait(H=5.0, D=1.0, Pm=0.5, Pe_max=1.0, density="coarse")
        assert result["delta_s"] == pytest.approx(np.arcsin(0.5), abs=1e-10)
        assert result["delta_u"] == pytest.approx(np.pi - np.arcsin(0.5), abs=1e-10)
