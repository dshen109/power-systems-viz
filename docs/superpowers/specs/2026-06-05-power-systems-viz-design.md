---
title: Power Systems Viz — Design Spec (Revised)
date: 2026-06-05
status: approved
---

# Power Systems Viz

Interactive learning website for undergraduate power systems students. Each concept page pairs a pre-rendered Manim explainer video with a live Plotly/Dash interactive widget driven by SciPy solvers. All examples use toy systems, not production-grade studies. Numerical methods are pedagogical, not planning-grade.

---

## Product Plan

The site is organized into two independent teaching modules, built in sequence.

**MVP 1 — Stability Module** builds first. It focuses on rotor-angle and small-signal stability: the swing equation, equilibria, phase portraits, fault analysis, and eigenvalue damping. Six pages. Students learn the physical intuition for machine dynamics before touching network models.

**MVP 2 — Network / OPF Module** builds after MVP 1 is stable. It teaches physical network flow, congestion, and electricity price formation. Six pages. Voltage stability (PV nose curve, QV margin) is an optional extension after MVP 1 ships, included in Spine A but deferred.

---

## Two-Spine Structure

### Spine A — Stability (MVP 1, then voltage extension)

Main teaching spine. Rotor dynamics first, voltage stability later.

| # | Page | MVP |
|---|------|-----|
| A1 | Swing Equation | 1 |
| A2 | SMIB Equilibrium | 1 |
| A3 | Phase Portrait | 1 |
| A4 | Equal Area Criterion | 1 |
| A5 | Critical Clearing Time | 1 |
| A6 | Eigenvalue Damping | 1 |
| A7 | Inter-Area Oscillations | extension |
| A8 | PV Nose Curve | extension |
| A9 | QV Reactive Margin | extension |

### Spine B — Network / OPF (MVP 2)

| # | Page | MVP |
|---|------|-----|
| B1 | DC Power Flow | 2 |
| B2 | Kirchhoff Loop Flows | 2 |
| B3 | Line Congestion | 2 |
| B4 | Economic Dispatch | 2 |
| B5 | DC OPF | 2 |
| B6 | LMPs under Congestion | 2 |

Navigation within each spine is linear (next/back). Spine selector at top level lets students switch modules. Each spine has its own progress bar.

---

## Architecture

### Stack

| Layer | Tool |
|-------|------|
| Web framework | Dash (multi-page, `dash.page_container`) |
| Math / solvers | SciPy, NumPy |
| Interactive plots | Plotly |
| Explainer animations | Manim (pre-rendered `.mp4`, committed to repo) |
| Equation rendering | `dash-katex` |
| Network visualization | NetworkX + Plotly scatter |
| Hosting | Render.com ($7/mo web service) |
| Deploy trigger | Push to `main` → auto-deploy via GitHub |

### Directory Structure

```
power-systems-viz/
├── app.py                        # Dash app init, multi-page setup, server
├── pages/
│   ├── spine_a/
│   │   ├── a1_swing_equation.py
│   │   ├── a2_smib_equilibrium.py
│   │   ├── a3_phase_portrait.py
│   │   ├── a4_equal_area.py
│   │   ├── a5_critical_clearing_time.py
│   │   └── a6_eigenvalue_damping.py
│   └── spine_b/
│       ├── b1_dc_power_flow.py
│       ├── b2_kirchhoff_loop_flows.py
│       ├── b3_line_congestion.py
│       ├── b4_economic_dispatch.py
│       ├── b5_dc_opf.py
│       └── b6_lmp_congestion.py
├── components/
│   ├── nav.py                    # Next/back buttons, progress bar, spine selector
│   ├── equation_panel.py         # KaTeX equation display component
│   ├── notice_box.py             # "What to notice" student prompt box
│   └── assumptions_box.py        # Model assumptions disclosure box
├── content/
│   ├── concepts.yaml             # Ordered concept list, spine assignments, MVP version
│   ├── equations.yaml            # LaTeX strings for all key equations
│   └── page_metadata.yaml        # Route, video filename, prev/next links per page
├── solvers/
│   ├── swing.py                  # Swing equation ODE (solve_ivp), equilibrium finder
│   ├── stability.py              # Eigenvalue solver, phase portrait grid, CCT bisection
│   ├── power_flow.py             # DC power flow (B-matrix), PTDF
│   └── opf.py                    # Economic dispatch LP, DC OPF, shadow prices
├── figures/
│   ├── swing_figures.py          # Plotly figures for A1, A2
│   ├── stability_figures.py      # Plotly figures for A3, A4, A5, A6
│   ├── voltage_figures.py        # Plotly figures for A7, A8, A9 (extension)
│   └── network_figures.py        # Plotly figures for B1–B6
├── assets/
│   ├── videos/                   # Pre-rendered Manim .mp4 files
│   └── styles.css                # Global dark theme
├── manim_scenes/
│   ├── a1_swing_equation.py
│   ├── a2_smib_equilibrium.py
│   └── ...                       # One scene file per page
├── tests/
│   ├── test_solvers.py
│   └── test_callbacks.py
└── requirements.txt
```

### Layer Responsibilities

- **`solvers/`** — pure numerical computation only. Takes typed dataclass inputs, returns NumPy arrays. No Plotly, no Dash.
- **`figures/`** — Plotly figure construction only. Takes solver output arrays, returns `go.Figure`. No Dash callbacks.
- **`pages/`** — Dash layout + callbacks only. Calls solvers and figures. Handles UI state, error display, guardrail messages.
- **`content/`** — concept registry. Single source of truth for page order, routing, video filenames, equation keys, spine assignment.

### Typed Solver Inputs

Each solver module uses Python dataclasses for inputs:

```python
@dataclass
class SwingParams:
    H: float       # inertia constant (MWs/MVA), 1–10
    D: float       # damping coefficient (pu), 0–5
    Pm: float      # mechanical power (pu)
    Pe_max: float  # max electrical power (pu)
    t_end: float   # simulation duration (s)

@dataclass
class FaultParams:
    Pe_max_pre: float    # pre-fault transfer capacity (pu)
    Pe_max_fault: float  # fault-on transfer capacity (pu), 0 for bolted 3-phase
    Pe_max_post: float   # post-fault transfer capacity (pu)
    Pm: float
    t_clear: float       # fault clearing time (s)

@dataclass
class DCPowerFlowParams:
    B: np.ndarray        # susceptance matrix (N×N)
    P_inject: np.ndarray # net injection per bus (pu)
    slack_bus: int
```

### Data Flow

```
User moves slider
  → Dash callback fires (server-side Python)
  → validate inputs → emit guardrail message if invalid
  → call solver (SciPy/NumPy)
  → call figure builder (Plotly)
  → return (figure, warning_message) to browser
  → browser renders figure + any warning banner
```

Latency target: <200 ms per callback. All problems small-scale (≤4 machines, ≤20-bus network). Synchronous callbacks sufficient.

### Concept Registry

`content/concepts.yaml` is the single source of truth for page ordering, routing, and navigation. The nav component reads this file at startup — no hardcoded prev/next links in page files.

```yaml
spines:
  - id: A
    name: Stability
    pages:
      - id: A1
        title: Swing Equation
        route: /stability/swing-equation
        video: a1_swing_equation.mp4
        equation_key: swing_eq
        mvp: 1
      - id: A2
        ...
```

### Manim Workflow

Scenes in `manim_scenes/`. Rendered locally, committed as static assets:

```bash
manim render manim_scenes/a1_swing_equation.py SwingScene -qm
cp media/videos/a1_swing_equation/720p30/SwingScene.mp4 assets/videos/a1_swing_equation.mp4
```

Manim not installed on server. Each clip: 1–3 minutes, text on screen, no narration.

---

## UI / Page Layout

Each concept page follows identical structure:

```
┌──────────────────────────────────────────────────────┐
│  Spine A: Stability    ░░░░░░░░░░░░  2 of 6          │
│  [← SMIB Equilibrium]          [Phase Portrait →]    │
├──────────────────────────────────────────────────────┤
│                                                      │
│   [Manim video — controls on, autoplay off]          │
│   1–3 min. Builds concept from first principles.     │
│                                                      │
├──────────────────────────────────────────────────────┤
│  KEY EQUATION                                        │
│  ┌────────────────────────────────────────────┐      │
│  │   M δ̈ + D δ̇ = Pm − Pe_max sin(δ)          │      │
│  │   where M = 2H / ωs                        │      │
│  └────────────────────────────────────────────┘      │
│  2–3 sentence plain-English gloss.                   │
├──────────────────────────────────────────────────────┤
│  EXPLORE                                             │
│  ┌───────────────────┬──────────────────────────┐   │
│  │  Sliders          │  Plotly figure            │   │
│  │  (dcc.Slider)     │  (dcc.Graph)              │   │
│  │                   │                           │   │
│  │  [warning banner] │                           │   │
│  └───────────────────┴──────────────────────────┘   │
├──────────────────────────────────────────────────────┤
│  WHAT TO NOTICE                                      │
│  • "Increase damping. What happens to oscillations?" │
│  • "Move Pm close to Pe_max. Is margin smaller?"     │
├──────────────────────────────────────────────────────┤
│  ASSUMPTIONS                                         │
│  Single machine, infinite bus. Lossless network.     │
│  Classical machine model (no exciter, no governor).  │
│  Angles in radians. Frequency in rad/s.              │
└──────────────────────────────────────────────────────┘
```

**Visual theme:** Dark background `#1a1a2e`, white text, electric blue accent `#4fc3f7`.

**Rotor clipart:** SVG circle + arrow rendered as Plotly `shapes` and `annotations` within `dcc.Graph`. Rotor angle δ maps to arrow angle via trigonometry. Updated each callback.

**Warning banners:** Red banner below sliders when inputs are physically invalid or solver fails. Suppresses figure update — shows last valid figure with banner overlay.

---

## Spine A — MVP 1 Page Specs

---

### A1 — Swing Equation

**Learning objective:** Understand how mechanical torque, electrical torque, and damping determine rotor motion. Recognize the role of inertia constant H and damping D.

**Key equation:**
```
M δ̈ + D δ̇ = Pm − Pe_max sin(δ)

where  M = 2H / ωs,   ωs = 2π × 60 rad/s (for 60 Hz system)
       H = inertia constant (MWs/MVA)
       D = damping coefficient (pu torque / pu speed)
       Pm = mechanical power input (pu)
       Pe_max sin(δ) = electrical power output
```
H is the machine parameter students specify. M is derived. Both are shown on the page. The distinction is explicit: H is energy stored per MVA rating; M is the effective mass in the swing ODE.

**Manim clip purpose:** Derive swing equation from Newton's second law analogy (rotor = spinning mass). Annotate each term. Show that increasing H slows the oscillation; increasing D damps it.

**Interactive controls:**
- H: inertia constant, 1–10 MWs/MVA
- D: damping coefficient, 0–5 pu
- Pm: mechanical power, 0–0.95 pu (capped below Pe_max = 1 pu)
- δ₀: initial angle perturbation from equilibrium, 0.01–0.5 rad
- Simulation time: 5–30 s

**Solver:** `scipy.integrate.solve_ivp` (RK45). State: `[δ, ω]`. Pe_max fixed at 1 pu on this page. Equilibrium δ_eq = arcsin(Pm) computed analytically; perturbation applied from there.

**Plot:** Two subplots — δ(t) and ω(t). Equilibrium δ_eq shown as dashed horizontal line. Rotor clipart beside plot shows angle live.

**What to notice:**
- "Increase H. Does the oscillation frequency increase or decrease? Why?"
- "Set D = 0. Does the system return to equilibrium?"
- "Increase Pm closer to 1.0. Does the equilibrium shift? Does the system still settle?"

**Numerical guardrails:**
- |δ| > π rad → stop integration, show: "Rotor lost synchronism (|δ| exceeded π rad). Reduce Pm or increase damping."
- D < 0 → blocked in slider, not permitted
- ODE solver failure → show: "Numerical solver failed. Try shorter simulation time."
- Pm ≥ 1.0 → show: "Pm exceeds transfer limit. No stable equilibrium exists."

**Assumptions box:** Single machine, infinite bus. Pe_max = 1 pu fixed. Classical machine model (no AVR, no governor). Angles in radians, frequency in rad/s.

---

### A2 — SMIB Equilibrium

**Learning objective:** Find stable and unstable equilibria of a single machine on an infinite bus. Understand why one equilibrium is stable and the other is not. Recognize the maximum power transfer limit.

**Key equation:**
```
At equilibrium (δ̈ = δ̇ = 0):
  Pm = Pe_max sin(δ)

Two solutions when Pm < Pe_max:
  δ_s = arcsin(Pm / Pe_max)           (stable)
  δ_u = π − arcsin(Pm / Pe_max)       (unstable)

No solution when Pm > Pe_max.
```

**Manim clip purpose:** Draw P-δ curve. Add horizontal Pm line. Show two intersection points. Explain stability intuitively — perturb each equilibrium, show restoring vs diverging force.

**Interactive controls:**
- Pm: mechanical power, 0–Pe_max pu
- Pe_max: transfer capacity, 0.5–2.0 pu

**Solver:** Analytic. No ODE. δ_s and δ_u computed directly from arcsin.

**Plot:** P-δ curve `Pe_max sin(δ)` over δ ∈ [0, π]. Horizontal line at Pm. Stable equilibrium: filled circle. Unstable equilibrium: open circle. Label both with angle in degrees and radians.

**What to notice:**
- "Increase Pm toward Pe_max. What happens to the two equilibria?"
- "At Pm = Pe_max, how many equilibria exist?"
- "Increase Pe_max (stronger line). Does the stable operating angle increase or decrease for the same Pm?"

**Numerical guardrails:**
- Pm > Pe_max → show: "No equilibrium exists. Mechanical power exceeds maximum transfer capacity. Machine cannot synchronize." Hide equilibrium markers.
- Pm = 0 → show equilibrium at δ = 0 (trivially stable), δ = π (unstable). Note this is a no-load case.

**Assumptions box:** Single machine, infinite bus. Lossless network. No saliency (round-rotor model). Pe = Pe_max sin(δ) only.

---

### A3 — Phase Portrait

**Learning objective:** Visualize the full two-dimensional state space of the swing equation. See which initial conditions lead to stable recovery and which to instability. Understand how damping changes trajectory shape.

**Key equation:**
```
As a first-order system:
  δ̇ = Δω
  Δω̇ = [Pm − Pe_max sin(δ)] / M − (D / M) Δω

where Δω = ω − ωs (speed deviation from synchronous)
```

**Manim clip purpose:** Introduce phase plane concept. Show a single trajectory as a curve in (δ, Δω) space. Add more trajectories. Show stable spiral (D > 0) vs closed orbits (D = 0) near stable equilibrium. Mark equilibria.

**Interactive controls:**
- H, D, Pm, Pe_max (same as A1)
- Grid density for IC sweep: coarse/medium/fine (affects number of trajectories shown)

**Solver:** `solve_ivp` with grid of initial conditions over δ ∈ [−π, π], Δω ∈ [−4π, 4π]. Each trajectory integrated until convergence or |δ| > 1.5π. Colored by outcome: blue = converges to stable equilibrium, red = diverges.

**Plot:** Phase portrait. Multiple trajectories. Stable equilibrium: filled circle. Unstable equilibrium (saddle point): X marker. Color boundary between stable (blue) and unstable (red) regions is approximate — label as "approximate stability boundary (based on trajectory outcomes)." Do not call it a separatrix unless the exact separatrix is computed via manifold methods.

**What to notice:**
- "Set D = 0. Are trajectories closed loops or spirals?"
- "Increase D. What changes near the stable equilibrium?"
- "Move Pm closer to Pe_max. What happens to the stable region size?"

**Numerical guardrails:**
- If grid sweep is too slow (fine grid + long sim): warn "Reducing grid for performance." Limit to ≤ 400 trajectories total.
- Trajectories that fail to integrate: skipped silently.
- Note shown on plot: "Boundary is approximate — based on trajectory outcomes, not exact separatrix computation."

**Assumptions box:** Same as A1. Stability boundary shown is approximate.

---

### A4 — Equal Area Criterion

**Learning objective:** Use graphical energy balance to determine whether a machine survives a fault — given a clearing angle — without time-domain simulation. Understand that the equal area criterion yields a critical clearing angle, not a critical clearing time.

**Key equation:**
```
Stability condition:
  A_accel ≤ A_decel

  A_accel = ∫[δ₀ to δc] (Pm − Pf sin(δ)) dδ     (accelerating area, fault-on)
  A_decel = ∫[δc to δ_max] (Pp sin(δ) − Pm) dδ   (decelerating area, post-fault)

where  δc  = clearing angle (set by slider)
       Pf  = fault-on transfer capacity
       Pp  = post-fault transfer capacity
       δ_max = π − arcsin(Pm / Pp)  (maximum angle for deceleration)
```

The clearing angle δc is the control variable on this page. Critical clearing angle is the δc that makes A_accel = A_decel exactly. To find clearing TIME from clearing angle, see page A5.

**Manim clip purpose:** Show three P-δ curves (pre-fault, fault, post-fault). Build up the accelerating area graphically as the rotor swings through the fault. Then show the decelerating area after clearing. Demonstrate stable (green area ≥ red area) vs unstable case.

**Interactive controls:**
- Pm: mechanical power (pu)
- Pe_max_pre: pre-fault transfer capacity (pu)
- Pe_max_fault: fault-on transfer capacity (pu), 0 = bolted 3-phase fault
- Pe_max_post: post-fault transfer capacity (pu)
- δc: clearing angle (rad), slider range [δ₀, π − arcsin(Pm/Pe_max_post)]

**Solver:** `scipy.integrate.quad` for A_accel and A_decel. δ₀ = arcsin(Pm/Pe_max_pre). δ_max = π − arcsin(Pm/Pe_max_post). Stability: A_accel ≤ A_decel.

**Plot:** P-δ diagram. Three sinusoidal curves in different colors (pre/fault/post). Horizontal Pm line. Shaded accelerating area (red). Shaded decelerating area (green). Label: "STABLE" or "UNSTABLE" based on area comparison. Show numerical values A_accel and A_decel.

**What to notice:**
- "Increase clearing angle. At what point does the machine go unstable?"
- "Reduce Pe_max_post (more line damage). How does the decelerating area shrink?"
- "Set Pe_max_fault = 0 (bolted fault). Does this maximize the accelerating area?"
- "This page gives clearing angle. Go to page A5 to find the clearing time."

**Numerical guardrails:**
- δc < δ₀ → blocked (can't clear before fault)
- δc > δ_max → show: "Clearing angle exceeds maximum deceleration angle. Machine is unstable regardless of clearing."
- Pe_max_post < Pm/1 (no equilibrium post-fault) → show: "No post-fault equilibrium. System cannot recover."
- Integration failure → show: "Area computation failed. Check that Pe_max_post > Pm."

**Assumptions box:** Single machine, infinite bus. Equal area criterion is exact for lossless SMIB. Does not account for multi-machine interactions. Clearing angle set directly; clearing time computation on next page.

---

### A5 — Critical Clearing Time

**Learning objective:** Find the critical clearing time (CCT) via time-domain integration of the swing equation through three sequential phases: pre-fault, fault-on, post-fault. Understand the relationship between clearing angle (from equal area) and clearing time.

**Key equation:**
```
Fault sequence:
  Phase 1 (t < 0):       steady state at δ₀ = arcsin(Pm / Pe_max_pre)
  Phase 2 (0 ≤ t < tc):  swing under fault — Pe = Pf sin(δ)
  Phase 3 (t ≥ tc):      swing under post-fault — Pe = Pp sin(δ)

Critical clearing time tc* = time at which δ(tc) = δc* (critical clearing angle)

δc* found from equal area criterion (A4). tc* found by integrating Phase 2
until δ reaches δc*.
```

**Manim clip purpose:** Show timeline of fault sequence. Animate δ(t) for a stable clearing time and an unstable clearing time side by side. Show how CCT relates to the critical clearing angle from A4.

**Interactive controls:**
- H, D, Pm: same as A1
- Pe_max_pre, Pe_max_fault, Pe_max_post: same as A4
- Fault clearing time tc: slider, 0–2 s. Machine labeled STABLE or UNSTABLE based on simulation outcome.

**Solver:** Three-phase `solve_ivp`. Phase transition at t = tc: switch Pe_max from Pe_max_fault to Pe_max_post and restart integration with final state of Phase 2. Stability criterion: |δ| > π rad or dδ/dt > 0 for sustained period after clearing → unstable. CCT reported as bisection result (displayed as informational annotation, not a slider).

**Plot:** δ(t) time series. Fault-on period shaded gray. Vertical line at tc. Annotation: "Clearing time = X s — [STABLE / UNSTABLE]". Rotor clipart beside plot. Secondary annotation: "Estimated CCT ≈ Y s" (from bisection).

**What to notice:**
- "Decrease H. Does CCT increase or decrease? Why?"
- "Increase Pm (heavier loading). How does CCT change?"
- "Set Pe_max_fault = 0 (bolted fault, maximum severity). How short must tc be?"
- "Compare the critical clearing angle from page A4 to where δ is at the CCT here."

**Numerical guardrails:**
- |δ| > π → stop, show: "Machine lost synchronism. Rotor angle exceeded π rad."
- tc = 0 → show: "Fault cleared instantly — system remains at pre-fault equilibrium."
- ODE solver failure → show: "Integration failed. Try reducing simulation duration."
- If bisection for CCT fails to converge in 20 iterations → display "CCT estimate unavailable for these parameters."

**Assumptions box:** Single machine, infinite bus. Classical machine model (constant voltage behind transient reactance). Fault applied at t = 0. Pre-fault assumed steady-state equilibrium.

---

### A6 — Eigenvalue Damping

**Learning objective:** Linearize the swing equation around a stable operating point. Understand small-signal stability in terms of eigenvalues. See how damping coefficient and loading level move eigenvalues in the complex plane.

**Key equation:**
```
Linearized system at operating point δ₀:

  [Δδ̇ ]   [  0       1   ] [Δδ ]
  [Δω̇ ] = [ −Ks/M   −D/M ] [Δω ]

where  Ks = dPe/dδ|δ₀ = Pe_max cos(δ₀)   (synchronizing torque coefficient)
       M = 2H / ωs

Eigenvalues: λ = −D/(2M) ± j√(Ks/M − (D/(2M))²)

Damping ratio:  ζ = D / (2√(Ks M))
Natural frequency: ωn = √(Ks / M)   rad/s
```

This page uses machine + infinite bus only. No AVR, no governor, no exciter dynamics. Adding AVR would require modeling the exciter state equations, which is a separate topic.

**Manim clip purpose:** Show linearization step (Taylor expansion of sin(δ) around δ₀). Build A-matrix. Show eigenvalues appear as complex conjugate pair. Animate how eigenvalues move as D changes from 0 (imaginary axis) to large values (overdamped, real axis).

**Interactive controls:**
- H: inertia constant, 1–10 MWs/MVA
- D: damping coefficient, 0–5 pu
- Pm: mechanical power, 0–0.95 × Pe_max (determines δ₀ and Ks)
- Pe_max: transfer capacity, 0.5–2.0 pu

**Solver:** Analytic A-matrix construction. `numpy.linalg.eig(A)` for eigenvalues. Extract σ (real part), ωd (imaginary part), compute ζ and ωn. No ODE needed.

**Plot:** Complex plane. Imaginary axis shown as vertical dashed line. Two eigenvalue markers (conjugate pair). Annotations: ζ, ωn, σ. Secondary panel: bar showing damping ratio ζ with color scale (red < 0.05, yellow 0.05–0.1, green > 0.1).

**What to notice:**
- "Increase D. Where do the eigenvalues move?"
- "Set D = 0. Where are the eigenvalues? What does this mean for oscillations?"
- "Increase Pm toward Pe_max. Ks decreases. What happens to eigenvalue positions?"
- "At what value of Pm does Ks = 0? What are the eigenvalues then?"

**Numerical guardrails:**
- Pm ≥ Pe_max → show: "No stable operating point. Linearization not valid. Reduce Pm." Block eigenvalue computation.
- D < 0 → blocked in slider.
- If Ks < 0 (should not occur given Pm < Pe_max constraint) → show error.
- Note on page: "This analysis applies only to small perturbations around the operating point. For large disturbances, return to pages A3–A5."

**Assumptions box:** Single machine, infinite bus. Classical machine model — no exciter, no governor, no power system stabilizer. Linearization valid only near the operating point. Results do not generalize to multi-machine systems without further analysis.

---

## Spine B — MVP 2 Page Specs

High-level specs for MVP 2. Detailed per-page treatment written when MVP 1 ships.

### B1 — DC Power Flow

**Learning objective:** Compute power flows in a lossless network using the DC power flow approximation. Understand how injections determine line flows via the B-matrix.

**Controls:** Generator injections and load per bus. **Solver:** B-matrix solve (`numpy.linalg.solve`). **Plot:** Network graph, edges colored by % loading. **Guardrails:** Islanded network (singular B matrix) → error. Kirchhoff check shown as annotation.

### B2 — Kirchhoff Loop Flows

**Learning objective:** Show that power flows by physics (impedance), not by contract path. Loop flows arise from network topology.

**Controls:** Contract path MW, parallel line impedances. **Solver:** DC power flow. **Plot:** Network with actual flows vs contracted path arrows. Loop flow magnitude labeled.

### B3 — Line Congestion

**Learning objective:** Show how a transmission constraint changes dispatch and prices. Understand redispatch.

**Controls:** Load level, line limit slider, toggle: fixed dispatch vs redispatch. **Solver:** DC power flow; if congestion, redispatch via LP. **Plot:** Network graph, congested line red; before/after generation bar chart. **Note:** Page clarifies whether redispatch is active or fixed dispatch mode.

### B4 — Economic Dispatch

**Learning objective:** Dispatch generators in merit order to minimize cost. Find the system lambda (marginal cost).

**Controls:** Demand level, generator cost coefficients (a, b in quadratic cost). **Solver:** Quadratic program or LP approximation (`scipy.optimize.minimize`). **Plot:** Merit order stack, dispatch quantities, system lambda line.

### B5 — DC OPF

**Learning objective:** Combine economic dispatch with network constraints. See how line limits constrain the least-cost dispatch.

**Controls:** Demand, cost coefficients, line flow limits. **Solver:** LP via `scipy.optimize.linprog`. Shadow prices extracted from dual variables. **Plot:** Merit order before/after OPF; network flows; binding constraints highlighted. **Note:** DC OPF model has no losses. Loss component not shown in LMP breakdown. Energy + congestion components only.

### B6 — LMPs under Congestion

**Learning objective:** Show how congestion creates locationally differentiated prices. Decompose LMP into energy and congestion components.

**Controls:** Same as B5. **Solver:** DC OPF duals. **Plot:** Bar chart of LMP per bus; stacked decomposition (energy / congestion). **Note:** Two components only — energy and congestion. Loss component omitted (DC model, lossless).

---

## Graceful UI Warnings

All pages handle solver failure, numerical instability, and physically invalid slider combinations. Warnings appear as a red banner in the slider panel. The Plotly figure retains the last valid state while the warning is active.

| Condition | Message |
|-----------|---------|
| Rotor angle exceeds π rad | "Rotor lost synchronism (δ > π). Reduce Pm or increase D." |
| ODE solver failed | "Numerical integration failed. Try shorter simulation time or different parameters." |
| No stable equilibrium (Pm ≥ Pe_max) | "Pm exceeds transfer limit. No stable equilibrium exists." |
| No post-fault equilibrium | "No post-fault equilibrium. System cannot recover from fault." |
| Clearing angle exceeds δ_max | "Clearing angle exceeds maximum deceleration angle. Machine is unstable." |
| LP infeasible (OPF) | "No feasible dispatch for these parameters. Check line limits." |
| Power flow non-convergence (NR) | "Power flow did not converge. Reduce load or add reactive support." |
| Singular B-matrix | "Network is islanded or disconnected. Check generation and load balance." |
| Invalid input combination | Context-specific message per page. |

---

## Testing

### Solver Unit Tests (`pytest`)

Known analytic results used as ground truth:

- **Swing equation:** Undamped, Pm = 0 → small-angle period T = 2π√(M/Ks). Test energy conservation (not pendulum period) for large-angle case.
- **SMIB equilibrium:** Two-bus case — δ_s and δ_u sum to π. Both arcsin branches correct.
- **Equal area:** Symmetric fault case (Pf = 0, Pp = Pe_max_pre, δ₀ small) — areas computable analytically to verify integration.
- **Eigenvalue solver:** 2×2 A-matrix with known eigenvalues → verify `numpy.linalg.eig` output matches analytic solution.
- **DC power flow:** 3-bus example → KCL satisfied at all buses; two-bus hand-calc verified.
- **DC OPF:** Unconstrained case → matches economic dispatch solution. Constrained case → shadow price nonzero on binding constraint.

### Callback Integration Tests (`dash.testing` + Selenium)

- Each page loads without Python exception
- Slider interaction returns non-empty figure
- Warning banner appears for known invalid input
- Next/back navigation reaches correct URL

### Manual Visual QA

- Stable operating point → spiral inward in phase portrait (D > 0)
- D = 0 → closed orbits in phase portrait
- CCT slider above critical → δ(t) diverges
- Eigenvalue moves left as D increases
- Overloaded line → red in network diagram
- LMP higher at load bus than generator bus when line is congested

---

## Deployment

**Platform:** Render.com web service ($7/mo)

- GitHub repo connected; push to `main` triggers deploy
- Python buildpack; `requirements.txt` pins all dependencies
- Manim `.mp4` committed to `assets/videos/`; served as Dash static assets
- No database, no auth, no env vars at launch

**Manim render environment:** Local only. Manim not installed on server.

---

## Out of Scope

**Deferred to Spine A extension (after MVP 1):**
- Inter-area oscillations (A7)
- PV nose curve / voltage collapse (A8)
- QV reactive margin (A9)

**Deferred to MVP 2 (Spine B):**
- DC power flow, congestion, economic dispatch, OPF, LMPs

**Not planned:**
- AC OPF (nonlinear — loss components require this; DC OPF is lossless)
- Multi-machine coherency (beyond 2-machine pedagogical case)
- Duck curve, storage, inertia decline
- Audio narration in Manim clips
- User accounts or progress saving
- Mobile layout optimization
- Real grid data (all examples use toy systems, not planning-grade)
- Market power, unit commitment, scarcity pricing
