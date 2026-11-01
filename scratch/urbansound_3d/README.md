# 🏙️ UrbanSound 3D: Noise Pollution Propagation Simulator
> *Simulation Framework for Noise Pollution Propagation Analysis in Urban Areas*

**UrbanSound 3D** is an open-source, interactive, physics-driven web simulation platform built entirely in **Python**. It models outdoor acoustic noise propagation across complex 3D urban geometries according to a simplified **ISO 9613-2** engineering framework.

The platform empowers urban planners, civil engineers, acoustic researchers, and citizens to visualize sound pollution, evaluate compliance with **CPCB (India)** and **WHO** regulatory thresholds, and conduct "what-if" testing of acoustic mitigations (sound barrier walls, traffic reduction policies, green foliage buffers).

---

## 🚀 Key Features

1. **Scroll-Story Landing Page (`Home.py`)**:
   - Concentric animated sound-wave ripples over a stylized generative SVG city skyline.
   - Plain-English decibel scale and health effects breakdown (hearing loss, hypertension, sleep disruption).
   - Interactive distance decay mini-demo showing the **-6 dB per doubling of distance** law in real-time.
   - 5-step engineering pipeline and comparison against high-cost commercial tools (SoundPLAN, CadnaA).

2. **3D Interactive Simulator Studio (`pages/1_Simulator.py`)**:
   - Extruded 3D architectural city blocks (`go.Mesh3d`), continuous road traffic sources, and ground sound pressure contours.
   - 3D Noise Surface (height = decibel level) illustrating acoustic shadow canyons cast behind buildings.
   - 2D Plan Heatmap with building footprint overlays, barrier lines, and source markers.
   - Calibrated Virtual Receiver Probe breaking down exact loss terms:
     $$L_{\text{rec}} = L_W + D_c - (A_{\text{div}} + A_{\text{atm}} + A_{\text{gr}} + A_{\text{bar}} + A_{\text{misc}})$$
   - Built-in procedural urban archetypes: *Residential Colony*, *Dense Downtown*, *Industrial + Residential Mix*, plus optional OpenStreetMap network queries.

3. **Results, Auditing & Mitigation Compare (`pages/2_Results_and_Compare.py`)**:
   - Compliance checking against **Central Pollution Control Board (CPCB) India** limits (Residential: 55 dB Day / 45 dB Night; Commercial: 65/55; Industrial: 75/70; Silence: 50/40).
   - Building facade exposure evaluation table with automatic Pass/Fail auditing.
   - Side-by-side Before vs After mitigation comparison and spatial noise reduction ($\Delta \text{dB}$) heatmap.
   - 24-Hour diurnal traffic curve modeling day and night exposure cycles with international $L_{\text{den}}$ composite indicators.
   - One-click exports: Full HTML Environmental Audit Report, Building Facade CSV, and Grid SPL CSV.

4. **Day vs Night & Diurnal Dynamics (`pages/3_Day_vs_Night_Diurnals.py`)**:
   - Side-by-side daytime vs nighttime spatial noise contour heatmaps.
   - Interactive 24-hour time scrubber with rush hour and nocturnal quiet tracking.
   - Continuous 24-hour diurnal noise trajectory vs statutory limits and WHO sleep guidelines.
   - Per-building nocturnal facade exposure Pass/Fail audit.

---

## 🛠️ Technology Stack (100% Python)

- **UI & Multi-page Engine:** Streamlit with custom dark glassmorphic CSS (`assets/style.css`)
- **2D & 3D Visualizations:** Plotly (`go.Mesh3d`, `go.Surface`, `go.Heatmap`, `go.Scatter3d`, `go.Bar`, `go.Histogram`)
- **Vectorized Spatial Math:** NumPy (grid calculations computed in < 1 second for 10,000+ points)
- **Geometry & Obstruction Screening:** Shapely & GeoPandas
- **Tabular Data:** Pandas
- **Testing:** Python `unittest` suite (`tests/test_propagation.py`)

---

## 📦 Installation & Quickstart

### 1. Clone or Open Project
```bash
cd urbansound_3d
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Unit Test Suite
```bash
python tests/test_propagation.py
```
*Tests verify inverse square law (-6 dB doubling), energy summation (60+60=63 dB), barrier screening, and non-negative attenuation terms.*

### 4. Launch the Interactive Web Application
```bash
streamlit run Home.py
```
Open your web browser at `http://localhost:8501`.

---

## 📂 Project Directory Structure

```text
urbansound_3d/
├── Home.py                       # Animated scroll-story landing page & interactive mini-demo
├── pages/
│   ├── 1_Simulator.py            # Live 3D/2D acoustic simulation studio & virtual probe
│   ├── 2_Results_and_Compare.py  # Regulatory compliance, before/after compare, diurnal cycles & export
│   └── 3_Day_vs_Night_Diurnals.py # Day vs night heatmaps, 24-hour scrubber, nocturnal sleep audit
├── core/
│   ├── __init__.py
│   ├── propagation.py            # Vectorized ISO 9613-2 calculation engine
│   ├── geometry.py               # Procedural cities, 3D building extrusions, sound barriers
│   ├── sources.py                # Acoustic source presets, highway traffic lines, diurnal curves
│   ├── standards.py              # CPCB India & WHO regulatory thresholds & zone limits
│   ├── visualization.py          # Reusable Plotly 3D/2D figure builders
│   └── utils.py                  # Session state persistence & HTML audit report generator
├── assets/
│   └── style.css                 # Dark glassmorphic theme styling & custom UI components
├── tests/
│   └── test_propagation.py      # Acoustic validation unit tests
├── requirements.txt              # Pinned Python package dependencies
└── README.md                     # Documentation & execution guide
```
