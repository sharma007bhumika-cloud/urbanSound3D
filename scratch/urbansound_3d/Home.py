"""
UrbanSound 3D: Noise Pollution Propagation Simulator.
Interactive web application for urban noise propagation simulation, acoustic zoning audits,
and environmental mitigation analysis.
UrbanSound 3D: Simulation Framework for Noise Pollution Propagation Analysis in Urban Areas.
"""

import os
import streamlit as st
import streamlit.components.v1 as components
import numpy as np
import plotly.graph_objects as go

from core.utils import init_session_state, render_mobile_navigation
from core.visualization import DARK_LAYOUT_TEMPLATE

st.set_page_config(
    page_title="UrbanSound 3D - City Noise Pollution Simulator",
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

# Top navigation for phones (hidden on laptops)
render_mobile_navigation(show_settings_hint=False)

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
    padding-top: 10px;
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
    <h1>UrbanSound 3D</h1>
    <p style="font-size: 1.35rem; font-weight: 600; color: #38bdf8; margin-bottom: 12px;">
      City Noise Pollution Simulator
    </p>
    <p class="tagline">
      Explore how noise from cars, trucks, and building sites spreads across city streets.
      See how buildings block sound, and test how noise barriers and slower speeds make neighborhoods quieter.
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
    <div class="stat-label">Sound Types (Traffic, Diggers, Trucks)</div>
  </div>
  <div class="stat-card">
    <div class="stat-num" id="stat-grid">14,400</div>
    <div class="stat-label">Mapped Street Points</div>
  </div>
  <div class="stat-card">
    <div class="stat-num">30 - 110</div>
    <div class="stat-label">Loudness Range in dB(A) (Decibels)</div>
  </div>
  <div class="stat-card">
    <div class="stat-num" style="color: #10b981;">ISO 9613-2</div>
    <div class="stat-label">Standard Outdoor Sound Physics</div>
  </div>
</div>

<!-- SECTION 1: WHAT IS NOISE POLLUTION -->
<div class="reveal-section visible">
  <div class="section-title">🔊 What is Noise Pollution?</div>
  <p class="section-subtitle">
    Noise pollution means unwanted, harmful outdoor sounds that disturb everyday life.
    It mostly comes from fast road traffic, heavy trucks, building sites, and factories.
  </p>
  
  <!-- Interactive Decibel Scale -->
  <div class="db-scale-bar">
    <div class="db-seg" style="flex: 30; background: #27ae60;">30 dB<br><span style="font-size:0.65rem;">Whisper (Very Quiet)</span></div>
    <div class="db-seg" style="flex: 25; background: #2ecc71;">55 dB<br><span style="font-size:0.65rem;">Quiet Homes (Safe)</span></div>
    <div class="db-seg" style="flex: 15; background: #f1c40f; color:#000;">65 dB<br><span style="font-size:0.65rem;">Normal Talk</span></div>
    <div class="db-seg" style="flex: 15; background: #e67e22;">80 dB<br><span style="font-size:0.65rem;">Busy Highway (Loud)</span></div>
    <div class="db-seg" style="flex: 15; background: #e74c3c;">100 dB<br><span style="font-size:0.65rem;">Jackhammer (Dangerous)</span></div>
    <div class="db-seg" style="flex: 15; background: #8e44ad;">130 dB<br><span style="font-size:0.65rem;">Jet Engine (Painful)</span></div>
  </div>
  
  <div class="grid-cards" style="margin-top: 24px;">
    <div class="feature-card">
      <div class="card-icon">🦻</div>
      <div class="card-heading">Ear & Hearing Damage</div>
      <div class="card-body">Hearing sounds louder than 85 dB(A) (decibels) for long periods damages delicate inner ear cells. This damage cannot be cured.</div>
    </div>
    <div class="feature-card">
      <div class="card-icon">🫀</div>
      <div class="card-heading">Heart & Blood Pressure Stress</div>
      <div class="card-body">Constant background noise triggers stress hormones in the body. Over time, this increases blood pressure and risks of heart trouble.</div>
    </div>
    <div class="feature-card">
      <div class="card-icon">🛌</div>
      <div class="card-heading">Broken Sleep & Tiredness</div>
      <div class="card-body">Night noise over 45 dB(A) wakes people up or disturbs deep sleep stages, leading to daytime tiredness, poor focus, and headaches.</div>
    </div>
  </div>
</div>

<!-- SECTION 2: WHAT THIS PROJECT DOES -->
<div class="reveal-section visible">
  <div class="section-title">⚡ What You Can Do in This Simulator</div>
  <p class="section-subtitle">
    Test city noise scenarios on an easy, visual 3D interactive map.
  </p>
  
  <div class="grid-cards">
    <div class="feature-card">
      <div class="card-icon">🏙️</div>
      <div class="card-heading">3D City Views</div>
      <div class="card-body">Walk through 3D neighborhoods with buildings, roads, and colorful sound heatmaps on the ground.</div>
    </div>
    <div class="feature-card">
      <div class="card-icon">🚧</div>
      <div class="card-heading">Building & Wall Shadows</div>
      <div class="card-body">Watch how tall buildings and sound barrier walls block noise, creating quiet shadow zones behind them.</div>
    </div>
    <div class="feature-card">
      <div class="card-icon">⚖️</div>
      <div class="card-heading">Legal Limit Check</div>
      <div class="card-body">Instantly check if noise levels meet official CPCB (India's pollution control board) and WHO safety limits.</div>
    </div>
    <div class="feature-card">
      <div class="card-icon">🔄</div>
      <div class="card-heading">Try Solutions (What-If)</div>
      <div class="card-body">Test barrier walls, lower traffic speeds, and tree buffers side-by-side to find the best way to make areas quiet.</div>
    </div>
  </div>
</div>

<!-- SECTION 3: 5-STEP PIPELINE -->
<div class="reveal-section visible">
  <div class="section-title">⚙️ How the Sound Calculation Works in 5 Steps</div>
  <p class="section-subtitle">
    Based on the world standard ISO 9613-2 calculation method.
  </p>
  
  <div class="pipeline-container">
    <div class="pipe-step">
      <div class="step-num">STEP 01</div>
      <div class="step-title">Noise Output</div>
      <div class="step-desc">Starts with the sound power level of cars, trucks, diggers, and machinery.</div>
    </div>
    <div class="pipe-step">
      <div class="step-num">STEP 02</div>
      <div class="step-title">Distance Drop</div>
      <div class="step-desc">Sound naturally drops by 6 decibels every time distance doubles, plus air absorbs some sound.</div>
    </div>
    <div class="pipe-step">
      <div class="step-num">STEP 03</div>
      <div class="step-title">Obstacle Blocking</div>
      <div class="step-desc">Buildings and barrier walls block sound waves, casting quiet shadow zones behind them.</div>
    </div>
    <div class="pipe-step">
      <div class="step-num">STEP 04</div>
      <div class="step-title">Energy Summing</div>
      <div class="step-desc">Sound from all roads and sources is combined at every point using acoustic energy addition.</div>
    </div>
    <div class="pipe-step">
      <div class="step-num">STEP 05</div>
      <div class="step-title">Safety Check</div>
      <div class="step-desc">Compares building facade noise against legal standards with pass/fail reports.</div>
    </div>
  </div>
</div>

<!-- SECTION 4: APPLICATIONS & USE CASES -->
<div class="reveal-section visible">
  <div class="section-title">🌍 Where This Helps in Real Life</div>
  <p class="section-subtitle">
    How city planners and engineers use noise simulations for healthier towns.
  </p>
  
  <div class="grid-cards">
    <div class="feature-card">
      <div class="card-icon">🏛️</div>
      <div class="card-heading">Planning New Homes</div>
      <div class="card-body">Ensuring apartments and housing colonies are built safe distances away from noisy highways.</div>
    </div>
    <div class="feature-card">
      <div class="card-icon">🏥</div>
      <div class="card-heading">Protecting Hospitals & Schools</div>
      <div class="card-body">Placing schools and recovery clinics in quiet silence zones (under 50 dB in the daytime).</div>
    </div>
    <div class="feature-card">
      <div class="card-icon">🛣️</div>
      <div class="card-heading">Highway Sound Barriers</div>
      <div class="card-body">Finding the perfect barrier wall height (3 to 6 meters) to block highway roar from nearby houses.</div>
    </div>
    <div class="feature-card">
      <div class="card-icon">📋</div>
      <div class="card-heading">Environmental Approvals</div>
      <div class="card-body">Generating compliance audit reports required before starting new metro lines or factories.</div>
    </div>
  </div>
</div>

<!-- SECTION 5: WHY THIS PROJECT / THE GAP -->
<div class="reveal-section visible">
  <div class="section-title">💡 Why UrbanSound 3D?</div>
  <p class="section-subtitle">
    Making acoustic planning simple, visual, and accessible directly in your web browser.
  </p>
  
  <table class="comp-table">
    <thead>
      <tr>
        <th>Feature</th>
        <th>Old Commercial Tools (SoundPLAN / CadnaA)</th>
        <th>UrbanSound 3D</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><b>Cost</b></td>
        <td>Expensive licenses ($8,000 to $25,000+ per user)</td>
        <td><span style="color:#10b981; font-weight:700;">100% Free & Open Source</span></td>
      </tr>
      <tr>
        <td><b>Getting Started</b></td>
        <td>Heavy desktop software (Windows workstation only)</td>
        <td><span style="color:#10b981; font-weight:700;">Zero install: runs in any web browser</span></td>
      </tr>
      <tr>
        <td><b>Ease of Use</b></td>
        <td>Complex CAD menus for acoustics specialists only</td>
        <td><span style="color:#10b981; font-weight:700;">Simple sliders, live probes, and clear words</span></td>
      </tr>
      <tr>
        <td><b>Data Export</b></td>
        <td>Locked in private closed file formats</td>
        <td><span style="color:#10b981; font-weight:700;">Download clean CSV data and HTML audit reports</span></td>
      </tr>
    </tbody>
  </table>
</div>
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
st.markdown("### 🧪 Try It Yourself: How Sound Drops with Distance")
st.markdown("""
Move the slider below to see how loud a sound is as you step further away.
Every time you **double your distance** from a noise, it drops by about **6 dB** (decibels).
Turning on a barrier wall blocks sound even more.
""")

demo_col1, demo_col2 = st.columns([1, 2])
with demo_col1:
    mini_dist = st.slider(
        "Your Distance from Noise (meters)",
        min_value=1.0, max_value=200.0, value=20.0, step=1.0,
        help="How far away you are standing from the noise source."
    )
    mini_lw = st.slider(
        "Source Noise Strength (decibels)",
        min_value=80.0, max_value=110.0, value=96.0, step=1.0,
        help="Total sound power made at the source (e.g. 96 dB is a passing truck, 80 dB is a car)."
    )
    mini_barrier = st.checkbox(
        "Put up a 4-meter barrier wall (at 15m distance)",
        value=True,
        help="Blocks the straight line between the sound and your ears."
    )

    # Calculate levels
    d_eff = max(1.0, mini_dist)
    a_div = 20.0 * np.log10(d_eff) + 11.0
    a_atm = 1.9 * d_eff / 1000.0
    a_bar = 0.0
    if mini_barrier and mini_dist > 15.0:
        a_bar = 10.0  # 10 dB nominal barrier reduction behind wall
        
    received_spl = max(30.0, mini_lw - (a_div + a_atm + a_bar))
    status_word = "Safe (Quiet)" if received_spl <= 55 else "A bit loud" if received_spl <= 70 else "Too loud"
    status_col = "#10b981" if received_spl <= 55 else "#f59e0b" if received_spl <= 70 else "#ef4444"
    
    st.markdown(f"""
    <div class="glass-card" style="text-align:center; padding:18px;">
        <div style="font-size:0.8rem; color:#94a3b8; text-transform:uppercase;">Noise You Hear at {mini_dist:.0f}m</div>
        <div style="font-size:2.8rem; font-weight:800; color:{status_col}; font-family:'JetBrains Mono'; margin: 8px 0;">
            {received_spl:.1f} <span style="font-size:1.1rem; color:#94a3b8;">dB(A)</span>
        </div>
        <div style="font-size:0.95rem; font-weight:700; color:{status_col}; margin-bottom:6px;">
            Status: {status_word}
        </div>
        <div style="font-size:0.82rem; color:#cbd5e1;">
            Natural distance drop: <b>-{a_div:.1f} dB</b><br>
            {'Wall blocked sound: <b>-10.0 dB</b>' if a_bar > 0 else 'No barrier in between'}
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.caption("In simple words: Under 55 dB is comfortable for homes. Over 70 dB feels loud and tiring.")

with demo_col2:
    d_range = np.linspace(1.0, 200.0, 200)
    l_curve_free = mini_lw - (20.0 * np.log10(d_range) + 11.0)
    l_curve_real = l_curve_free - (1.9 * d_range / 1000.0)
    if mini_barrier:
        l_curve_real[d_range > 15.0] -= 10.0
        
    fig_mini = go.Figure()
    fig_mini.add_trace(go.Scatter(x=d_range, y=l_curve_free, mode="lines", name="Open Air (no obstacles)", line=dict(color="#94a3b8", dash="dash")))
    fig_mini.add_trace(go.Scatter(x=d_range, y=l_curve_real, mode="lines", name="Real Ground + Barrier Wall", line=dict(color="#38bdf8", width=3)))
    fig_mini.add_trace(go.Scatter(x=[mini_dist], y=[received_spl], mode="markers", name="Where You Stand", marker=dict(size=12, color="#ef4444", symbol="star")))
    
    fig_mini.update_layout(
        template="plotly_dark",
        paper_bgcolor=DARK_LAYOUT_TEMPLATE["paper_bgcolor"],
        plot_bgcolor=DARK_LAYOUT_TEMPLATE["plot_bgcolor"],
        font=DARK_LAYOUT_TEMPLATE["font"],
        title="Loudness vs Distance from Noise",
        xaxis=dict(title="Distance from Noise (meters)"),
        yaxis=dict(title="Loudness dB(A) (Decibels)", range=[30, 100]),
        margin=dict(l=20, r=20, t=35, b=20),
        legend=dict(orientation="h", y=1.12, x=0.05)
    )
    st.plotly_chart(fig_mini, width="stretch", key="home_fig_mini")
    st.caption("In simple words: The blue curve shows how sound falls rapidly nearby, then flattens out further away.")

with st.expander("Technical details (for students and experts)"):
    st.markdown(r"""
    Sound propagation in free air follows spherical geometric divergence according to the **Inverse Square Law**:
    """)
    st.latex(r"A_{\text{div}} = 20 \cdot \log_{10}(d) + 11.0 \quad [\text{dB}]")
    st.markdown(r"""
    Atmospheric absorption ($A_{\text{atm}}$) adds roughly $1.9\ \text{dB/km}$ under standard ambient air ($20^\circ\text{C}$, $50\%\ \text{RH}$), and diffraction screening behind barriers drops acoustic energy by an additional $5\text{ to }15\ \text{dB}$.
    """)

st.markdown("---")

# ----------------- FINAL CALL TO ACTION -----------------
st.markdown("### Ready to Try the City Noise Simulator?")
cta_c1, cta_c2 = st.columns([2, 1])
with cta_c1:
    st.markdown("""
    Explore 3D city layouts, place roads and construction diggers, and see how sound barrier walls protect residential homes.
    """)
with cta_c2:
    st.page_link("pages/1_Simulator.py", label="Open City Simulator", icon="🔊")
