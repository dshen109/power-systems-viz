---
title: Power Systems Viz — Design Spec
date: 2026-06-05
status: approved
---

# Power Systems Viz

Interactive learning website for undergraduate power systems students. Each concept page pairs a pre-rendered Manim explainer video with a live Plotly/Dash interactive widget driven by SciPy solvers.

## Goals

- Give undergrads intuitive feel for stability dynamics and network/market concepts
- Show equations on screen; build from first principles
- 12 concepts in linear course flow (next/back navigation)
- High visual quality: Manim clips for explanation, Plotly dark-themed widgets for exploration

## Scope

Covers four topic clusters: transient stability (A), small-signal/voltage stability (B), network/power flow (C), and OPF (F). Markets excluded from MVP.

---

## Architecture

### Stack

| Layer | Tool |
|-------|------|
| Web framework | Dash (multi-page) |
| Math/solvers | SciPy, NumPy |
| Interactive plots | Plotly |
| Explainer animations | Manim (pre-rendered .mp4, committed to repo) |
| Equation rendering | dash-katex |
| Network visualization | NetworkX + Plotly scatter |
| Hosting | Render.com ($7/mo web service) |
| Deploy trigger | Push to `main` → auto-deploy via GitHub integration |

### Directory Structure

```
power-systems-viz/
├── app.py                    # Dash app init, multi-page setup, server
├── pages/                    # One .py file per concept page
│   ├── 01_dc_power_flow.py
│   ├── 02_line_congestion.py
│   ├── 03_kirchhoff_loop_flows.py
│   ├── 04_opf.py
│   ├── 05_swing_equation.py
│   ├── 06_smib_phase_portrait.py
│   ├── 07_equal_area_criterion.py
│   ├── 08_multi_machine_coherency.py
│   ├── 09_eigenvalue_mode_damping.py
│   ├── 10_inter_area_oscillations.py
│   ├── 11_pv_nose_curve.py
│   └── 12_qv_reactive_margin.py
├── components/
│   ├── nav.py                # Next/back buttons, progress bar
│   └── equation_panel.py     # Styled KaTeX equation display
├── solvers/
│   ├── power_flow.py         # DC power flow, PTDF, B-matrix, OPF
│   ├── swing.py              # Swing equation ODE, multi-machine
│   └── stability.py          # Eigenvalue solver, nose curve, QV sweep
├── assets/
│   ├── videos/               # Pre-rendered Manim .mp4 files (one per concept)
│   └── styles.css            # Global dark theme styles
├── manim_scenes/             # Manim source scenes (render locally, commit output)
│   ├── 01_dc_power_flow.py
│   └── ...
├── tests/
│   ├── test_solvers.py       # Solver unit tests
│   └── test_callbacks.py     # Dash callback integration tests
└── requirements.txt
```

### Data Flow

```
User moves slider
  → Dash callback fires (Python, server-side)
  → solver function called (SciPy/NumPy)
  → returns numpy arrays
  → Plotly figure rebuilt and returned
  → browser renders updated figure
```

Latency target: <200ms per callback. All problems small-scale (≤4 machines, ≤20-bus network). Synchronous callbacks sufficient — no task queues.

### Manim Workflow

Scenes written in `manim_scenes/`. Rendered locally:

```bash
manim render manim_scenes/05_swing_equation.py SwingScene -qm
# Move output from media/videos/ to assets/videos/
```

Clips committed to repo as static assets. Not rendered at runtime. Each clip: 1–3 minutes, no narration initially (text on screen).

---

## UI / Page Layout

Each concept page follows identical structure:

```
┌─────────────────────────────────────────────────┐
│  [← Prev]   Concept 5 of 12: Swing Equation  [Next →]  │
│  ████████████░░░░░░░░░░░░  progress bar         │
├─────────────────────────────────────────────────┤
│   [Manim video player — controls on, autoplay off]      │
│   1–3 min clip builds up the concept visually.  │
├─────────────────────────────────────────────────┤
│  KEY EQUATION                                   │
│  ┌──────────────────────────────────┐           │
│  │   M δ̈ + D δ̇ = Pm − Pe sin(δ)   │  (KaTeX)  │
│  └──────────────────────────────────┘           │
│  2–3 sentence plain-English gloss.              │
├─────────────────────────────────────────────────┤
│  EXPLORE                                        │
│  ┌──────────────┬──────────────────────────┐   │
│  │  Sliders     │   Plotly figure           │   │
│  │  (dcc.Slider)│   (dcc.Graph)             │   │
│  └──────────────┴──────────────────────────┘   │
├─────────────────────────────────────────────────┤
│  [← Prev: DC Power Flow]    [Next: SMIB →]      │
└─────────────────────────────────────────────────┘
```

**Visual theme:** Dark background `#1a1a2e`, white text, electric blue accent `#4fc3f7`. Matches 3b1b aesthetic.

**Rotor clipart:** SVG circle + arrow rendered as Plotly `shapes` and `annotations` within `dcc.Graph`, updated each callback. Rotor angle δ maps directly to arrow angle via trigonometry. No custom HTML injection needed.

---

## Concept Pages — Interactive Details

| # | Concept | Sliders / Controls | Solver | Plot(s) |
|---|---------|-------------------|--------|---------|
| 1 | DC Power Flow | Gen outputs per bus, load per bus | B-matrix solve (`numpy.linalg.solve`) | Network graph: nodes = buses, edges = lines colored by % flow |
| 2 | Line Congestion + N-1 | Load level, dropdown: line to trip | DC power flow pre/post contingency | Network before vs after; overloaded lines red |
| 3 | Kirchhoff Loop Flows | Contract path MW, parallel line impedances | DC power flow | Actual vs contracted path arrows; loop flow magnitude |
| 4 | OPF | Demand level, generator cost coefficients | LP via `scipy.optimize.linprog` | Merit order stack; LMP per bus; energy/congestion/loss components |
| 5 | Swing Equation | H (inertia), D (damping), Pm, fault duration | `scipy.integrate.solve_ivp` | δ(t) and ω(t) time series; rotor SVG clipart |
| 6 | SMIB Phase Portrait | H, D, Pm, Pe_max | `solve_ivp` multi-IC sweep | Phase portrait δ vs ω; separatrix; stable/unstable equilibria marked |
| 7 | Equal Area + CCT | Fault clearing time, pre/during/post-fault impedances | Numerical integration of P-δ curve areas | P-δ curve; shaded accelerating/decelerating areas; stable vs unstable |
| 8 | Multi-Machine Coherency | H per machine, fault location | Coupled swing ODE system (`solve_ivp`) | δ(t) per machine; color-coded coherent groups |
| 9 | Eigenvalue / Mode Damping | AVR gain, line loading, damping coefficient | `numpy.linalg.eig` on linearized A-matrix | Eigenvalue locus in complex plane; poles move live with sliders |
| 10 | Inter-Area Oscillations | Tie-line loading, area inertias, damping | Two-area linearized ODE (`solve_ivp`) | Tie-line P(t); frequency deviation both areas |
| 11 | PV Nose Curve | Load power factor, reactive compensation | Parametric Newton-Raphson sweep (AC power flow) | PV curve; nose point; current operating point marker |
| 12 | QV Reactive Margin | Bus selection, reactive compensation added | QV sweep (repeated power flow) | QV curve; reactive margin shaded to collapse point |

**Implementation notes:**
- Pages 1–4: `networkx` for graph topology, Plotly scatter traces for nodes/edges
- Pages 5–8: rotor SVG clipart updated via callback; overlaid on or beside Plotly figure
- Page 11: continuation power flow simplified to parametric NR sweep at undergrad level; full predictor-corrector not required

---

## Testing

### Solver Unit Tests (`pytest`)

Each solver tested against known analytic results:
- DC power flow: Kirchhoff current law satisfied at all buses; two-bus case matches hand calc
- Swing equation: undamped case (D=0, Pm=0) oscillation period matches pendulum formula
- Eigenvalue solver: 2×2 test matrix eigenvalues match analytic solution

### Callback Integration Tests (`dash.testing` + Selenium)

- Each page loads without Python exception
- Slider interaction produces non-empty figure output
- Next/back navigation reaches correct URL

### Manual Visual QA

- Stable operating point → spiral inward in phase portrait
- Fault clearing time beyond CCT → rotor angle diverges
- Nose curve → voltage collapses at tip as load → loadability limit
- Overloaded line → turns red in network diagram

---

## Deployment

**Platform:** Render.com web service ($7/mo)

- GitHub repo connected; push to `main` triggers deploy
- Python buildpack; `requirements.txt` specifies all dependencies
- Manim `.mp4` files committed to `assets/videos/`; served as Dash static assets
- No database, no auth, no env vars required at launch

**Manim render environment:** Local only. Manim not installed on server.

---

## Out of Scope (MVP)

- Electricity markets (economic dispatch, unit commitment, market power)
- Duck curve / inertia decline / storage
- Audio narration in Manim clips
- User accounts / progress saving
- Mobile optimization
- Real grid data (all examples use toy networks)
