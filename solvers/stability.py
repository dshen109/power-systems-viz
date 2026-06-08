import numpy as np
from scipy.integrate import solve_ivp

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
