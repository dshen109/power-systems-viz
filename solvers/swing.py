from dataclasses import dataclass
import numpy as np
from scipy.integrate import solve_ivp

OMEGA_S: float = 2.0 * np.pi * 60.0  # synchronous speed, 60 Hz system (rad/s)


@dataclass
class SwingParams:
    H: float        # inertia constant (MWs/MVA), 1–10
    D: float        # damping coefficient (pu), 0–5
    Pm: float       # mechanical power (pu)
    Pe_max: float   # maximum electrical power transfer (pu)
    t_end: float    # simulation duration (s)
    delta_0: float  # initial angle perturbation from equilibrium (rad)


@dataclass
class FaultParams:
    Pe_max_pre: float    # pre-fault transfer capacity (pu)
    Pe_max_fault: float  # fault-on transfer capacity (pu); 0 for bolted 3-phase
    Pe_max_post: float   # post-fault transfer capacity (pu)
    Pm: float
    t_clear: float       # fault clearing time (s)


def find_smib_equilibria(Pm: float, Pe_max: float) -> dict:
    """
    Return stable (delta_s) and unstable (delta_u) equilibrium angles.

    Returns dict with keys: delta_s, delta_u, warning.
    delta_s and delta_u are None when Pm > Pe_max.
    """
    if Pm > Pe_max:
        return {
            "delta_s": None,
            "delta_u": None,
            "warning": (
                "No equilibrium exists. Mechanical power exceeds maximum "
                "transfer capacity. Machine cannot synchronize."
            ),
        }
    ratio = np.clip(Pm / Pe_max, -1.0, 1.0)
    delta_s = np.arcsin(ratio)
    delta_u = np.pi - delta_s
    return {"delta_s": delta_s, "delta_u": delta_u, "warning": None}


def solve_swing(params: SwingParams) -> dict:
    """
    Integrate the swing equation for a single machine on an infinite bus.

    Returns dict with keys: t, delta, omega, delta_eq, delta_u, warning.
    t/delta/omega are None on error. warning is a string or None.
    """
    if params.Pm >= params.Pe_max:
        return {
            "t": None, "delta": None, "omega": None,
            "delta_eq": None, "delta_u": None,
            "warning": "Pm exceeds transfer limit. No stable equilibrium exists.",
        }

    M = 2.0 * params.H / OMEGA_S
    eq = find_smib_equilibria(params.Pm, params.Pe_max)
    delta_eq: float = eq["delta_s"]
    delta_u: float = eq["delta_u"]

    def ode(t, y):
        delta, omega_dev = y
        Pe = params.Pe_max * np.sin(delta)
        d_delta = omega_dev
        d_omega = (params.Pm - Pe - params.D * omega_dev) / M
        return [d_delta, d_omega]

    def event_crosses_unstable(t, y):
        return y[0] - delta_u
    event_crosses_unstable.terminal = True
    event_crosses_unstable.direction = 1

    def event_absolute_stop(t, y):
        return abs(y[0]) - 1.5 * np.pi
    event_absolute_stop.terminal = True
    event_absolute_stop.direction = 0

    y0 = [delta_eq + params.delta_0, 0.0]
    sol = solve_ivp(
        ode,
        [0.0, params.t_end],
        y0,
        method="RK45",
        events=[event_crosses_unstable, event_absolute_stop],
        max_step=0.02,
        rtol=1e-6,
        atol=1e-8,
    )

    if not sol.success:
        return {
            "t": None, "delta": None, "omega": None,
            "delta_eq": delta_eq, "delta_u": delta_u,
            "warning": "Numerical solver failed. Try shorter simulation time.",
        }

    instability_triggered = (
        sol.t_events[0].size > 0 or sol.t_events[1].size > 0
    )
    warning = (
        "Rotor crossed unstable equilibrium (δ > δ_u). Machine lost synchronism. "
        "Reduce Pm or increase D."
        if instability_triggered
        else None
    )

    return {
        "t": sol.t,
        "delta": sol.y[0],
        "omega": sol.y[1],
        "delta_eq": delta_eq,
        "delta_u": delta_u,
        "warning": warning,
    }
