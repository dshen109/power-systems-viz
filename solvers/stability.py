import numpy as np

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
