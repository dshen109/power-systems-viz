import numpy as np
from scipy.integrate import solve_ivp, quad

from solvers.swing import OMEGA_S, find_smib_equilibria


def compute_eigenvalues(H: float, D: float, Pm: float, Pe_max: float) -> dict:
    """
    Linearize swing equation around stable equilibrium and compute eigenvalues.

    Returns dict: eigenvalues, sigma, omega_d, omega_n, zeta, Ks, warning.
    """
    eq = find_smib_equilibria(Pm, Pe_max)
    if eq["warning"]:
        return {
            "eigenvalues": None, "sigma": None, "omega_d": None,
            "omega_n": None, "zeta": None, "Ks": None,
            "warning": "No stable operating point. Linearization not valid. Reduce Pm.",
        }

    M = 2.0 * H / OMEGA_S
    delta_s = eq["delta_s"]
    Ks = Pe_max * np.cos(delta_s)  # synchronizing torque coefficient

    A = np.array([[0.0, 1.0], [-Ks / M, -D / M]])
    eigenvalues = np.linalg.eig(A)[0]

    # Pick representative values (conjugate pair has same real part; take first)
    sigma = float(eigenvalues[0].real)
    omega_d = float(abs(eigenvalues[0].imag))
    omega_n = float(np.sqrt(Ks / M))
    alpha = D / (2.0 * M)
    zeta = alpha / omega_n if omega_n > 1e-12 else float("inf")

    return {
        "eigenvalues": eigenvalues,
        "sigma": sigma,
        "omega_d": omega_d,
        "omega_n": omega_n,
        "zeta": zeta,
        "Ks": Ks,
        "warning": None,
    }


_DENSITY_GRID = {"coarse": 10, "medium": 15, "fine": 20}


def compute_phase_portrait(
    H: float, D: float, Pm: float, Pe_max: float, density: str = "medium"
) -> dict:
    """
    Integrate swing equation from a grid of initial conditions.

    Returns dict: trajectories (list of dicts with delta, omega, stable),
    delta_s, delta_u, warning.

    Grid sizes: coarse=100, medium=225, fine=400 (n_side × n_side).
    Trajectories colored by outcome: stable = no terminal event in t_max.
    """
    eq = find_smib_equilibria(Pm, Pe_max)
    if eq["warning"]:
        return {"trajectories": [], "delta_s": None, "delta_u": None, "warning": eq["warning"]}

    delta_s: float = eq["delta_s"]
    delta_u: float = eq["delta_u"]
    M = 2.0 * H / OMEGA_S
    n_side = _DENSITY_GRID.get(density, 15)

    delta_grid = np.linspace(-np.pi, np.pi, n_side)
    omega_grid = np.linspace(-4.0 * np.pi, 4.0 * np.pi, n_side)

    def ode(t, y):
        d, w = y
        return [w, (Pm - Pe_max * np.sin(d) - D * w) / M]

    def event_unstable(t, y):
        return y[0] - delta_u
    event_unstable.terminal = True
    event_unstable.direction = 1

    def event_absolute(t, y):
        return abs(y[0]) - 1.5 * np.pi
    event_absolute.terminal = True

    trajectories = []
    for d0 in delta_grid:
        for w0 in omega_grid:
            try:
                sol = solve_ivp(
                    ode,
                    [0.0, 20.0],
                    [d0, w0],
                    method="RK45",
                    events=[event_unstable, event_absolute],
                    max_step=0.1,
                    rtol=1e-4,
                    atol=1e-6,
                )
                stable = sol.t_events[0].size == 0 and sol.t_events[1].size == 0
                trajectories.append({
                    "delta": sol.y[0],
                    "omega": sol.y[1],
                    "stable": stable,
                })
            except Exception:
                trajectories.append({
                    "delta": np.array([d0]),
                    "omega": np.array([w0]),
                    "stable": False,
                })

    return {
        "trajectories": trajectories,
        "delta_s": delta_s,
        "delta_u": delta_u,
        "warning": None,
    }


def compute_equal_area(
    Pm: float,
    Pe_max_pre: float,
    Pe_max_fault: float,
    Pe_max_post: float,
    delta_c: float,
) -> dict:
    """
    Compute accelerating and decelerating areas for the equal area criterion.

    Returns dict: A_accel, A_decel, stable, delta_0, delta_max, warning.
    """
    if Pm >= Pe_max_post:
        return {
            "A_accel": None, "A_decel": None, "stable": None,
            "delta_0": None, "delta_max": None,
            "warning": (
                "No post-fault equilibrium. Reduce Pm or restore more "
                "post-fault transfer capacity."
            ),
        }

    delta_0 = np.arcsin(np.clip(Pm / Pe_max_pre, -1.0, 1.0))
    delta_max = np.pi - np.arcsin(np.clip(Pm / Pe_max_post, -1.0, 1.0))

    try:
        A_accel, _ = quad(lambda d: Pm - Pe_max_fault * np.sin(d), delta_0, delta_c)
        A_decel, _ = quad(lambda d: Pe_max_post * np.sin(d) - Pm, delta_c, delta_max)
    except Exception:
        return {
            "A_accel": None, "A_decel": None, "stable": None,
            "delta_0": delta_0, "delta_max": delta_max,
            "warning": "Area computation failed. Check that Pe_max_post > Pm.",
        }

    return {
        "A_accel": float(A_accel),
        "A_decel": float(A_decel),
        "stable": A_accel <= A_decel,
        "delta_0": delta_0,
        "delta_max": delta_max,
        "warning": None,
    }


def solve_fault_sequence(
    H: float,
    D: float,
    Pm: float,
    Pe_max_pre: float,
    Pe_max_fault: float,
    Pe_max_post: float,
    t_clear: float,
) -> dict:
    """
    Three-phase time-domain simulation: pre-fault steady state → fault-on → post-fault.

    Returns dict: t, delta, fault_period, stable, delta_u_post, warning.
    """
    if Pm >= Pe_max_post:
        return {
            "t": None, "delta": None, "fault_period": (0.0, t_clear),
            "stable": False, "delta_u_post": None,
            "warning": "No post-fault equilibrium. System cannot recover from fault.",
        }

    M = 2.0 * H / OMEGA_S
    delta_0 = np.arcsin(np.clip(Pm / Pe_max_pre, -1.0, 1.0))
    delta_u_post = np.pi - np.arcsin(np.clip(Pm / Pe_max_post, -1.0, 1.0))

    def make_ode(Pe_max_active: float):
        def ode(t, y):
            d, w = y
            return [w, (Pm - Pe_max_active * np.sin(d) - D * w) / M]
        return ode

    def event_unstable(t, y):
        return y[0] - delta_u_post
    event_unstable.terminal = True
    event_unstable.direction = 1

    def event_absolute(t, y):
        return abs(y[0]) - 1.5 * np.pi
    event_absolute.terminal = True

    # Phase 2: fault-on (0 → t_clear)
    y0 = [delta_0, 0.0]
    sol_fault = solve_ivp(
        make_ode(Pe_max_fault),
        [0.0, max(t_clear, 1e-6)],
        y0,
        method="RK45",
        events=[event_unstable, event_absolute],
        max_step=0.005,
        rtol=1e-6, atol=1e-8,
    )

    if sol_fault.t_events[0].size > 0 or sol_fault.t_events[1].size > 0:
        return {
            "t": sol_fault.t,
            "delta": sol_fault.y[0],
            "fault_period": (0.0, t_clear),
            "stable": False,
            "delta_u_post": delta_u_post,
            "warning": (
                "Machine lost synchronism — rotor angle crossed "
                "post-fault unstable equilibrium."
            ),
        }

    # Phase 3: post-fault (t_clear → t_end)
    y_at_clear = [sol_fault.y[0, -1], sol_fault.y[1, -1]]
    t_end_post = t_clear + max(10.0, 5.0)

    sol_post = solve_ivp(
        make_ode(Pe_max_post),
        [t_clear, t_end_post],
        y_at_clear,
        method="RK45",
        events=[event_unstable, event_absolute],
        max_step=0.02,
        rtol=1e-6, atol=1e-8,
    )

    t_all = np.concatenate([sol_fault.t, sol_post.t])
    delta_all = np.concatenate([sol_fault.y[0], sol_post.y[0]])

    stable = sol_post.t_events[0].size == 0 and sol_post.t_events[1].size == 0
    warning = (
        "Machine lost synchronism — rotor angle crossed post-fault unstable equilibrium."
        if not stable
        else None
    )

    return {
        "t": t_all,
        "delta": delta_all,
        "fault_period": (0.0, t_clear),
        "stable": stable,
        "delta_u_post": delta_u_post,
        "warning": warning,
    }


def find_cct(
    H: float,
    D: float,
    Pm: float,
    Pe_max_pre: float,
    Pe_max_fault: float,
    Pe_max_post: float,
    tol: float = 0.01,
    max_iter: int = 20,
) -> dict:
    """
    Bisection search for critical clearing time.

    Returns dict: cct (float seconds), converged (bool), warning (str | None).
    """
    lo, hi = 0.0, 2.0

    # Verify hi is unstable
    r_hi = solve_fault_sequence(H, D, Pm, Pe_max_pre, Pe_max_fault, Pe_max_post, hi)
    if r_hi["stable"]:
        return {
            "cct": None,
            "converged": False,
            "warning": "System stable at t_clear = 2 s. CCT exceeds search range.",
        }

    for _ in range(max_iter):
        mid = (lo + hi) / 2.0
        r_mid = solve_fault_sequence(H, D, Pm, Pe_max_pre, Pe_max_fault, Pe_max_post, mid)
        if r_mid["stable"]:
            lo = mid
        else:
            hi = mid
        if hi - lo < tol:
            break

    converged = (hi - lo) < tol
    cct = (lo + hi) / 2.0
    warning = None if converged else f"CCT estimate ≈ {cct:.2f} s (not fully converged)."

    return {"cct": cct, "converged": converged, "warning": warning}
