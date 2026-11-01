"""
UrbanSound 3D: Noise Pollution Propagation Simulator.
Interactive web application for urban noise propagation simulation, acoustic zoning audits,
and environmental mitigation analysis.
Academic Engineering Project: Simulation Framework for Noise Pollution Propagation Analysis in Urban Areas.
"""

import os
import streamlit as st
import streamlit.components.v1 as components
import numpy as np
import plotly.graph_objects as go

from core.utils import init_session_state
from core.visualization import DARK_LAYOUT_TEMPLATE

st.set_page_config(
    page_title="UrbanSound 3D - Noise Pollution Propagation Simulator",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load global CSS
css_path = os.path.join(os.path.dirname(__file__), "assets", "style.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

init_session_state()

# ----------------- HERO SECTION & SCROLL-STORY HTML COMPONENT -----------------
landing_hero_html = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800;900&family=JetBrains+Mono:wght@500;700&display=swap');
  
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: transparent;
    color: #f8fafc;
    font-family: 'Inter', -apple-system, sans-serif;
    overflow-x: hidden;
  }
  
  /* Hero Container */
  .hero-container {
    position: relative;
    padding: 60px 20px 40px 20px;
    text-align: center;
    overflow: hidden;
    border-radius: 24px;
    background: radial-gradient(circle at 50% 30%, rgba(30, 27, 75, 0.7) 0%, rgba(10, 14, 23, 0.95) 70%);
    border: 1px solid rgba(56, 189, 248, 0.2);
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6);
    margin-bottom: 40px;
  }
  
  /* Concentric Sound Wave Animation */
  .soundwave-box {
    position: absolute;
    top: 35%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 600px;
    height: 400px;
    pointer-events: none;
    z-index: 1;
    display: flex;
    justify-content: center;
    align-items: center;
  }
  
  .wave-ring {
    position: absolute;
    border-radius: 50%;
    animation: ripple 6s infinite cubic-bezier(0.2, 0.8, 0.2, 1);
    opacity: 0;
  }
  
  .ring-1 { width: 120px; height: 120px; border: 2px solid #ef4444; animation-delay: 0s; }
  .ring-2 { width: 220px; height: 220px; border: 2px solid #f59e0b; animation-delay: 1.5s; }
  .ring-3 { width: 340px; height: 340px; border: 2px solid #10b981; animation-delay: 3s; }
  .ring-4 { width: 480px; height: 480px; border: 2px solid #38bdf8; animation-delay: 4.5s; }
  
  @keyframes ripple {
    0% { transform: scale(0.4); opacity: 0.9; }
    50% { opacity: 0.5; }
    100% { transform: scale(1.6); opacity: 0; }
  }
  
  .hero-content {
    position: relative;
    z-index: 2;
    max-width: 900px;
    margin: 0 auto;
  }
  
  .badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 16px;
    border-radius: 9999px;
    background: rgba(56, 189, 248, 0.1);
    border: 1px solid rgba(56, 189, 248, 0.3);
    color: #38bdf8;
    font-size: 0.85rem;
    font-weight: 600;
    margin-bottom: 20px;
    letter-spacing: 0.05em;
    text-transform: uppercase;
  }
  
  h1 {
    font-size: 3.2rem;
    font-weight: 900;
    line-height: 1.15;
    background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 50%, #38bdf8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 18px;
  }
  
  .tagline {
    font-size: 1.25rem;
    color: #e2e8f0;
    line-height: 1.6;
    margin-bottom: 30px;
    max-width: 750px;
    margin-left: auto;
    margin-right: auto;
  }
  
  /* SVG Skyline Container */
  .skyline-svg {
    width: 100%;
    height: 120px;
    margin-top: 30px;
    position: relative;
    z-index: 2;
  }
  
  /* Live Stats Strip */
  .stats-strip {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 16px;
    margin: 30px 0 50px 0;
  }
  
  .stat-card {
    background: rgba(30, 41, 59, 0.6);
    border: 1px solid rgba(56, 189, 248, 0.15);
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    transition: transform 0.3s ease;
  }
  .stat-card:hover { transform: translateY(-4px); border-color: rgba(56, 189, 248, 0.4); }
  
  .stat-num {
    font-size: 2.2rem;
    font-weight: 800;
    color: #38bdf8;
    font-family: 'JetBrains Mono', monospace;
  }
  
  .stat-label {
    font-size: 0.82rem;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-top: 6px;
  }
  
  /* Sections - Always 100% visible with crisp contrast */
  .reveal-section {
    margin: 45px 0;
    opacity: 1 !important;
    transform: none !important;
  }
  
  .section-title {
    font-size: 2.1rem;
    font-weight: 800;
    color: #ffffff;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 12px;
  }
  
  .section-subtitle {
    font-size: 1.1rem;
    color: #cbd5e1;
    margin-bottom: 24px;
    line-height: 1.6;
  }
  
  /* Grid Cards */
  .grid-cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 20px;
  }
  
  .feature-card {
    background: rgba(15, 23, 42, 0.85);
    border: 1px solid rgba(56, 189, 248, 0.25);
    border-radius: 16px;
    padding: 24px;
    backdrop-filter: blur(8px);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35);
    transition: all 0.3s ease;
  }
  .feature-card:hover {
    border-color: rgba(56, 189, 248, 0.6);
    transform: translateY(-4px);
    background: rgba(30, 41, 59, 0.9);
  }
  
  .card-icon {
    font-size: 2.2rem;
    margin-bottom: 12px;
    display: inline-block;
  }
  
  .card-heading {
    font-size: 1.25rem;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 10px;
  }
  
  .card-body {
    font-size: 0.95rem;
    color: #e2e8f0;
    line-height: 1.6;
  }
  
  /* Pipeline Steps */
  .pipeline-container {
    display: flex;
    flex-wrap: wrap;
    gap: 14px;
    margin-top: 20px;
  }
  
  .pipe-step {
    flex: 1;
    min-width: 170px;
    background: rgba(15, 23, 42, 0.9);
    border: 1px solid rgba(56, 189, 248, 0.25);
    border-radius: 12px;
    padding: 18px;
    position: relative;
    border-top: 3px solid #38bdf8;
    box-shadow: 0 4px 16px rgba(0,0,0,0.3);
  }
  
  .step-num {
    font-size: 0.8rem;
    color: #38bdf8;
    font-weight: 800;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: 0.05em;
  }
  
  .step-title {
    font-size: 1.05rem;
    font-weight: 700;
    color: #ffffff;
    margin: 6px 0 8px 0;
  }
  
  .step-desc {
    font-size: 0.88rem;
    color: #cbd5e1;
    line-height: 1.5;
  }
  
  /* Decibel Scale Visualizer */
  .db-scale-bar {
    display: flex;
    border-radius: 12px;
    overflow: hidden;
    margin: 20px 0;
    height: 48px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.4);
  }
  .db-seg {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    color: #fff;
    font-weight: 700;
    font-size: 0.85rem;
    transition: filter 0.2s;
  }
  .db-seg:hover { filter: brightness(1.2); }
  
  /* Comparison Table */
  .comp-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 18px;
    background: rgba(15, 23, 42, 0.9);
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid rgba(56, 189, 248, 0.3);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35);
  }
  .comp-table th, .comp-table td {
    padding: 16px 20px;
    text-align: left;
    border-bottom: 1px solid rgba(56, 189, 248, 0.15);
    font-size: 0.95rem;
  }
  .comp-table th { background: #0b1120; color: #38bdf8; font-weight: 800; border-bottom: 2px solid rgba(56, 189, 248, 0.4); }
  .comp-table td { color: #f1f5f9; }
  .comp-table tr:hover { background: rgba(56, 189, 248, 0.08); }
</style>
</head>
<body>

<!-- HERO SECTION -->
<div class="hero-container">
  <!-- Soundwave Ripple Rings -->
  <div class="soundwave-box">
    <div class="wave-ring ring-1"></div>
    <div class="wave-ring ring-2"></div>
    <div class="wave-ring ring-3"></div>
    <div class="wave-ring ring-4"></div>
  </div>
  
  <div class="hero-content">
    <div class="badge">🔊 3rd-Semester Engineering Project</div>
    <h1>UrbanSound 3D</h1>
    <p style="font-size: 1.35rem; font-weight: 600; color: #38bdf8; margin-bottom: 12px;">
      Simulation Framework for Noise Pollution Propagation Analysis in Urban Areas
    </p>
    <p class="tagline">
      An open, physics-driven acoustic engine that calculates outdoor sound propagation, 
      casts 3D building shadows, checks CPCB/WHO regulatory compliance, and evaluates mitigation in real time.
    </p>
    
    <!-- Stylized Skyline SVG -->
    <svg class="skyline-svg" viewBox="0 0 1000 120" preserveAspectRatio="none">
      <!-- Background skyline -->
      <polygon points="50,120 50,60 80,60 80,30 110,30 110,120" fill="#1e293b" opacity="0.6"/>
      <polygon points="120,120 120,40 160,40 160,120" fill="#1e293b" opacity="0.5"/>
      <polygon points="170,120 170,20 220,20 220,120" fill="#334155" opacity="0.7"/>
      <polygon points="230,120 230,50 270,50 270,120" fill="#1e293b" opacity="0.6"/>
      <polygon points="290,120 290,10 340,10 340,120" fill="#0f172a" opacity="0.8"/>
      <!-- Foreground skyscrapers -->
      <polygon points="360,120 360,35 410,35 410,120" fill="#1e293b" opacity="0.9"/>
      <polygon points="430,120 430,15 480,15 480,120" fill="#38bdf8" opacity="0.25"/>
      <polygon points="500,120 500,45 560,45 560,120" fill="#1e293b" opacity="0.8"/>
      <polygon points="580,120 580,25 640,25 640,120" fill="#334155" opacity="0.9"/>
      <polygon points="660,120 660,50 710,50 710,120" fill="#1e293b" opacity="0.7"/>
      <polygon points="730,120 730,10 790,10 790,120" fill="#38bdf8" opacity="0.3"/>
      <polygon points="810,120 810,40 860,40 860,120" fill="#1e293b" opacity="0.6"/>
      <polygon points="880,120 880,20 940,20 940,120" fill="#334155" opacity="0.8"/>
      <!-- Base ground line -->
      <line x1="0" y1="118" x2="1000" y2="118" stroke="#38bdf8" stroke-width="2" opacity="0.4"/>
    </svg>
  </div>
</div>

<!-- LIVE STATS STRIP -->
<div class="stats-strip">
  <div class="stat-card">
    <div class="stat-num" id="stat-sources">7+</div>
    <div class="stat-label">Acoustic Presets Modelled</div>
  </div>
  <div class="stat-card">
    <div class="stat-num" id="stat-grid">14,400</div>
    <div class="stat-label">Vectorized Grid Points</div>
  </div>
  <div class="stat-card">
    <div class="stat-num">30 - 110</div>
    <div class="stat-label">Decibel Range dB(A)</div>
  </div>
  <div class="stat-card">
    <div class="stat-num" style="color: #10b981;">ISO 9613-2</div>
    <div class="stat-label">Physics Propagation Standard</div>
  </div>
</div>

<!-- SECTION 1: WHAT IS NOISE POLLUTION -->
<div class="reveal-section visible">
  <div class="section-title">🔊 What is Noise Pollution?</div>
  <p class="section-subtitle">
    Noise pollution is an invisible hazard: prolonged exposure to unwanted or harmful outdoor sound 
    generated by highway traffic, construction equipment, heavy industrial mills, and commercial activity.
  </p>
  
  <!-- Interactive Decibel Scale -->
  <div class="db-scale-bar">
    <div class="db-seg" style="flex: 30; background: #27ae60;">30 dB<br><span style="font-size:0.65rem;">Whisper</span></div>
    <div class="db-seg" style="flex: 25; background: #2ecc71;">55 dB<br><span style="font-size:0.65rem;">Quiet Res.</span></div>
    <div class="db-seg" style="flex: 15; background: #f1c40f; color:#000;">65 dB<br><span style="font-size:0.65rem;">Conversation</span></div>
    <div class="db-seg" style="flex: 15; background: #e67e22;">80 dB<br><span style="font-size:0.65rem;">Busy Highway</span></div>
    <div class="db-seg" style="flex: 15; background: #e74c3c;">100 dB<br><span style="font-size:0.65rem;">Jackhammer</span></div>
    <div class="db-seg" style="flex: 15; background: #8e44ad;">130 dB<br><span style="font-size:0.65rem;">Jet Takeoff</span></div>
  </div>
  
  <div class="grid-cards" style="margin-top: 24px;">
    <div class="feature-card">
      <div class="card-icon">🦻</div>
      <div class="card-heading">Permanent Hearing Loss</div>
      <div class="card-body">Continuous exposure above 85 dB(A) causes irreversible degradation of the delicate stereocilia hair cells inside the inner ear cochlea.</div>
    </div>
    <div class="feature-card">
      <div class="card-icon">🫀</div>
      <div class="card-heading">Cardiovascular Stress</div>
      <div class="card-body">WHO epidemiological studies confirm chronic nocturnal noise elevates cortisol, inducing systemic hypertension and ischemic heart risks.</div>
    </div>
    <div class="feature-card">
      <div class="card-icon">🛌</div>
      <div class="card-heading">Severe Sleep Disturbance</div>
      <div class="card-body">Nighttime peaks exceeding 45 dB fragment sleep stages, reducing REM restorative sleep and triggering daytime cognitive impairments.</div>
    </div>
  </div>
</div>

<!-- SECTION 2: WHAT THIS PROJECT DOES -->
<div class="reveal-section visible">
  <div class="section-title">⚡ What This Simulation Platform Does</div>
  <p class="section-subtitle">
    Transforming complex acoustic equations into an intuitive, visually stunning, multi-layer 3D planning workspace.
  </p>
  
  <div class="grid-cards">
    <div class="feature-card">
      <div class="card-icon">🏙️</div>
      <div class="card-heading">3D City Soundscapes</div>
      <div class="card-body">Procedural 3D building blocks with accurate spatial heights, road networks, and dynamic ground noise contours.</div>
    </div>
    <div class="feature-card">
      <div class="card-icon">🚧</div>
      <div class="card-heading">Building & Barrier Obstruction</div>
      <div class="card-body">Vectorized diffraction algorithms calculate acoustic shadow zones behind buildings and test sound barrier effectiveness.</div>
    </div>
    <div class="feature-card">
      <div class="card-icon">⚖️</div>
      <div class="card-heading">CPCB & WHO Compliance Audit</div>
      <div class="card-body">Automated auditing of Indian CPCB ambient limits and WHO guidelines across residential, commercial, industrial, and silence zones.</div>
    </div>
    <div class="feature-card">
      <div class="card-icon">🔄</div>
      <div class="card-heading">Mitigation What-If Studio</div>
      <div class="card-body">Side-by-side comparative views: test acoustic walls, traffic reduction policies, and green foliage buffers before infrastructure investment.</div>
    </div>
  </div>
</div>

<!-- SECTION 3: 5-STEP PIPELINE -->
<div class="reveal-section visible">
  <div class="section-title">⚙️ How It Works: The 5-Step Pipeline</div>
  <p class="section-subtitle">
    Vectorized NumPy implementation of the ISO 9613-2 outdoor propagation standard.
  </p>
  
  <div class="pipeline-container">
    <div class="pipe-step">
      <div class="step-num">STAGE 01</div>
      <div class="step-title">Emission Modeling</div>
      <div class="step-desc">Point sources & discretized continuous highway traffic lines characterized by sound power level Lw.</div>
    </div>
    <div class="pipe-step">
      <div class="step-num">STAGE 02</div>
      <div class="step-title">Atmospheric Decay</div>
      <div class="step-desc">Inverse-square spherical divergence (-6 dB/doubling) and temperature/humidity air absorption.</div>
    </div>
    <div class="pipe-step">
      <div class="step-num">STAGE 03</div>
      <div class="step-title">Obstacle Screening</div>
      <div class="step-desc">Vectorized ray-obstacle path difference diffraction (Maekawa theory) casts acoustic shadows.</div>
    </div>
    <div class="pipe-step">
      <div class="step-num">STAGE 04</div>
      <div class="step-title">Energy Summation</div>
      <div class="step-desc">Logarithmic decibel summation combines multiple source contributions into spatial sound pressure grids.</div>
    </div>
    <div class="pipe-step">
      <div class="step-num">STAGE 05</div>
      <div class="step-title">Compliance & Action</div>
      <div class="step-desc">Building facade exposure evaluation, regulatory pass/fail auditing, and exportable engineering reports.</div>
    </div>
  </div>
</div>

<!-- SECTION 4: APPLICATIONS & USE CASES -->
<div class="reveal-section visible">
  <div class="section-title">🌍 Real-World Urban Applications</div>
  <p class="section-subtitle">
    Where acoustic propagation simulation drives smarter, healthier civic design.
  </p>
  
  <div class="grid-cards">
    <div class="feature-card">
      <div class="card-icon">🏛️</div>
      <div class="card-heading">Urban Master Planning & Zoning</div>
      <div class="card-body">Ensuring residential colonies and high-density towers are acoustically buffered from major transport corridors.</div>
    </div>
    <div class="feature-card">
      <div class="card-icon">🏥</div>
      <div class="card-heading">Hospital & School Siting</div>
      <div class="card-body">Locating sensitive healthcare and educational institutions within compliant Silence Zones (< 50 dB Day).</div>
    </div>
    <div class="feature-card">
      <div class="card-icon">🛣️</div>
      <div class="card-heading">Flyovers & Highway Barriers</div>
      <div class="card-body">Optimizing acoustic wall placement and height (3m to 6m) along elevated arterial transit corridors.</div>
    </div>
    <div class="feature-card">
      <div class="card-icon">📋</div>
      <div class="card-heading">Environmental Impact Assessment</div>
      <div class="card-body">Fulfilling statutory EIA compliance reports for new industrial facilities and metro line expansions.</div>
    </div>
  </div>
</div>

<!-- SECTION 5: WHY THIS PROJECT / THE GAP -->
<div class="reveal-section visible">
  <div class="section-title">💡 Why This Project? Closing the Industry Gap</div>
  <p class="section-subtitle">
    Democratizing acoustic simulation with modern open-source web technologies.
  </p>
  
  <table class="comp-table">
    <thead>
      <tr>
        <th>Evaluation Criteria</th>
        <th>Commercial Tools (SoundPLAN / CadnaA)</th>
        <th>UrbanSound 3D Open Framework</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><b>Accessibility & Cost</b></td>
        <td>Enterprise licenses ($8,000 - $25,000+ / seat)</td>
        <td><span style="color:#10b981; font-weight:700;">100% Free & Open Source Python Platform</span></td>
      </tr>
      <tr>
        <td><b>Installation Friction</b></td>
        <td>Heavy desktop workstation software (Windows only)</td>
        <td><span style="color:#10b981; font-weight:700;">Zero-install web app runs in any modern browser</span></td>
      </tr>
      <tr>
        <td><b>Interactive Learning</b></td>
        <td>Complex CAD menus designed solely for acoustic specialists</td>
        <td><span style="color:#10b981; font-weight:700;">Pedagogical sliders, live probes & visual intuition</span></td>
      </tr>
      <tr>
        <td><b>Data Export & Customization</b></td>
        <td>Proprietary closed file formats</td>
        <td><span style="color:#10b981; font-weight:700;">Standard NumPy / CSV / HTML / Plotly JSON exports</span></td>
      </tr>
    </tbody>
  </table>
</div>

<script>
  // Simple intersection observer to animate sections on scroll
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
      }
    });
  }, { threshold: 0.1 });
  
  document.querySelectorAll('.reveal-section').forEach(sec => observer.observe(sec));
</script>

</body>
</html>
"""

components.html(landing_hero_html, height=2450, scrolling=False)

# ----------------- INTERACTIVE MINI-DEMO: HOW DOES NOISE TRAVEL? -----------------
st.markdown("### 🧪 Interactive Mini-Demo: How Sound Travels & Decays")
st.markdown("""
Move the slider below to observe how sound pressure drops as you move away from an acoustic source.
Notice the exact **~6 dB reduction every time distance doubles** (Inverse Square Law), plus extra absorption when a sound barrier is introduced.
""")

demo_col1, demo_col2 = st.columns([1, 2])
with demo_col1:
    mini_dist = st.slider("Observer Distance from Source (m)", min_value=1.0, max_value=200.0, value=20.0, step=1.0, help="Distance in meters from the reference noise source.")
    mini_lw = st.slider("Source Power Level Lw (dB)", min_value=80.0, max_value=110.0, value=96.0, step=1.0)
    mini_barrier = st.checkbox("Include 4.0m Sound Barrier (at 15m distance)", value=True)

    # Calculate levels
    d_eff = max(1.0, mini_dist)
    a_div = 20.0 * np.log10(d_eff) + 11.0
    a_atm = 1.9 * d_eff / 1000.0
    a_bar = 0.0
    if mini_barrier and mini_dist > 15.0:
        a_bar = 10.0  # 10 dB nominal barrier reduction behind wall
        
    received_spl = max(30.0, mini_lw - (a_div + a_atm + a_bar))
    
    st.markdown(f"""
    <div class="glass-card" style="text-align:center; padding:18px;">
        <div style="font-size:0.8rem; color:#94a3b8; text-transform:uppercase;">Received Sound Level at {mini_dist:.0f}m</div>
        <div style="font-size:2.8rem; font-weight:800; color:#38bdf8; font-family:'JetBrains Mono'; margin: 8px 0;">
            {received_spl:.1f} <span style="font-size:1.1rem;">dB(A)</span>
        </div>
        <div style="font-size:0.85rem; color:#cbd5e1;">
            Free-field geometric drop: <b>-{a_div:.1f} dB</b><br>
            {'Barrier attenuation: <b>-10.0 dB</b>' if a_bar > 0 else 'Direct Line-of-Sight'}
        </div>
    </div>
    """, unsafe_allow_html=True)

with demo_col2:
    d_range = np.linspace(1.0, 200.0, 200)
    l_curve_free = mini_lw - (20.0 * np.log10(d_range) + 11.0)
    l_curve_real = l_curve_free - (1.9 * d_range / 1000.0)
    if mini_barrier:
        l_curve_real[d_range > 15.0] -= 10.0
        
    fig_mini = go.Figure()
    fig_mini.add_trace(go.Scatter(x=d_range, y=l_curve_free, mode="lines", name="Free Field (-6 dB/doubling)", line=dict(color="#94a3b8", dash="dash")))
    fig_mini.add_trace(go.Scatter(x=d_range, y=l_curve_real, mode="lines", name="With Terrain + Barrier", line=dict(color="#38bdf8", width=3)))
    fig_mini.add_trace(go.Scatter(x=[mini_dist], y=[received_spl], mode="markers", name="Your Observer Probe", marker=dict(size=12, color="#ef4444", symbol="star")))
    
    fig_mini.update_layout(
        template="plotly_dark",
        paper_bgcolor=DARK_LAYOUT_TEMPLATE["paper_bgcolor"],
        plot_bgcolor=DARK_LAYOUT_TEMPLATE["plot_bgcolor"],
        font=DARK_LAYOUT_TEMPLATE["font"],
        title="Decibel Level vs Distance Profile",
        xaxis=dict(title="Distance (meters)"),
        yaxis=dict(title="Sound Level (dB(A))", range=[30, 100]),
        margin=dict(l=20, r=20, t=35, b=20),
        legend=dict(orientation="h", y=1.12, x=0.05)
    )
    st.plotly_chart(fig_mini, use_container_width=True)

st.markdown("---")

# ----------------- FINAL CALL TO ACTION -----------------
st.markdown("### Ready to Test Urban Sound Propagation?")
cta_c1, cta_c2 = st.columns([2, 1])
with cta_c1:
    st.markdown("""
    Explore 3D city layouts, position construction machinery, configure highway traffic volumes, 
    and evaluate acoustic wall mitigation across residential sectors.
    """)
with cta_c2:
    st.page_link("pages/1_Simulator.py", label="🚀 Launch 3D Sound Simulator", icon="🔊")
