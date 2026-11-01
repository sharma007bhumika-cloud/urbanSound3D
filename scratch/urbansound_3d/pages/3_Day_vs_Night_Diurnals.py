"""
UrbanSound 3D - Day vs Night Dynamics & 24-Hour Diurnal Analysis Studio.
Analyzes temporal acoustic progression, 24-hour urban traffic diurnal cycles,
nocturnal sleep disruption assessment, and night compliance against CPCB and WHO guidelines.
"""

import os
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from core.geometry import (
    create_residential_colony,
    CityLayout
)
from core.sources import (
    NoiseSource,
    get_diurnal_traffic_factors,
    discretize_road_to_sources
)
from core.standards import CPCB_STANDARDS, WHO_GUIDELINES, get_cpcb_limit
from core.propagation import (
    simulate_grid,
    evaluate_single_receiver,
    evaluate_facade_exposures
)
from core.visualization import (
    DARK_LAYOUT_TEMPLATE,
    build_2d_heatmap_plot,
    build_scenario_difference_plot
)
from core.utils import init_session_state, render_mobile_navigation

st.set_page_config(
    page_title="UrbanSound 3D - Day vs Night Noise",
    page_icon="🌓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load CSS
css_path = os.path.join(os.path.dirname(__file__), "..", "assets", "style.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

init_session_state()

# Mobile top navigation bar (visible only on small screens <= 768px)
render_mobile_navigation(show_settings_hint=True)

# ----------------- PAGE HEADER -----------------
st.title("🌓 Noise Through the Day and Night")
st.caption("See how traffic quietens down after dark, check sleep protection standards, and find out if nighttime noise is within legal limits.")

# Ensure city and sources are available
if "city" not in st.session_state or st.session_state["city"] is None:
    st.session_state["city"] = create_residential_colony()
    st.session_state["city_type"] = "Residential Colony"

city: CityLayout = st.session_state["city"]

if "sources" not in st.session_state or not st.session_state["sources"]:
    new_sources = []
    for road in city.roads:
        new_sources.extend(discretize_road_to_sources(
            road["name"], road["start"], road["end"], traffic_vol=road.get("traffic_vol", 1200)
        ))
    st.session_state["sources"] = new_sources

# How to use this page
st.info("""
**How to use this page (in 3 easy steps):**
1. **Choose your neighborhood type and night policies** in the sidebar settings on the left (or tap the **>** arrow at the top left if on a phone).
2. **Look at the Day vs Night maps** to see how much quieter the streets become after dark.
3. **Use the 24-hour slider** to check any specific hour of the day or review the sleep protection audit.
""")

# ----------------- SIDEBAR CONTROLS -----------------
with st.sidebar:
    st.markdown("### ⚖️ Area Type & Night Rules")
    
    # 1. Zoning Standard
    zone_choice = st.selectbox(
        "Designated Zoning Type",
        list(CPCB_STANDARDS.keys()),
        index=2, # Residential Area
        format_func=lambda x: {
            "Industrial Area": "Industrial Area (factories)",
            "Commercial Area": "Commercial Area (markets & shops)",
            "Residential Area": "Residential Area (homes & apartments)",
            "Silence Zone": "Silence Zone (hospitals & schools)"
        }.get(x, x),
        help="CPCB (Central Pollution Control Board, India's pollution authority) ambient limits for Day vs Night.",
        key="sb_p3_zone_choice"
    )
    cpcb_day_limit = get_cpcb_limit(zone_choice, "day")
    cpcb_night_limit = get_cpcb_limit(zone_choice, "night")
    
    st.markdown(f"""
    <div style="background:rgba(30,41,59,0.7); border:1px solid rgba(56,189,248,0.3); border-radius:10px; padding:12px; margin-bottom:16px;">
        <div style="font-size:0.8rem; color:#94a3b8; text-transform:uppercase;">CPCB Legal Limits ({zone_choice})</div>
        <div style="display:flex; justify-content:space-between; margin-top:6px;">
            <div><span style="color:#f59e0b; font-weight:700;">☀️ Day:</span> <b style="color:#f8fafc;">{cpcb_day_limit} dB(A)</b></div>
            <div><span style="color:#38bdf8; font-weight:700;">🌙 Night:</span> <b style="color:#f8fafc;">{cpcb_night_limit} dB(A)</b></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 🌙 Night Noise Control Policies")
    
    night_traffic_reduction = st.slider(
        "Night Traffic Drop (%)",
        min_value=40, max_value=95, value=80, step=5,
        help="Percentage drop in vehicular traffic flow at night (e.g. 80% drop means night traffic is 20% of daytime peak).",
        key="sb_p3_night_reduc"
    )
    
    night_truck_curfew = st.checkbox(
        "Night Heavy Truck Curfew (10 PM to 6 AM)",
        value=True,
        help="Bans heavy trucks at night, cutting loud rumbling and vehicle pass-by noise.",
        key="sb_p3_truck_curfew"
    )
    
    night_speed_calming = st.checkbox(
        "Enforce 30 km/h Night Speed Limit",
        value=False,
        help="Reduces tyre-road contact noise by lowering vehicle speeds from 40 km/h to 30 km/h.",
        key="sb_p3_speed_calming"
    )
    
    calc_res = st.slider(
        "Map Detail Level",
        min_value=40, max_value=100, value=60, step=10,
        help="Grid resolution for day and night comparative noise maps.",
        key="sb_p3_calc_res"
    )

# ----------------- SIMULATION CALCULATIONS -----------------
# 1. Day Sources
day_sources = []
for s in st.session_state["sources"]:
    if s.active:
        day_sources.append(s)

# 2. Night Sources (with policy scaling)
night_sources = []
flow_fraction = max(0.05, 1.0 - (night_traffic_reduction / 100.0))
flow_db_drop = 10.0 * np.log10(flow_fraction)
if night_truck_curfew:
    flow_db_drop -= 3.0  # Removing heavy vehicle pass-by peak saves ~3 dB
if night_speed_calming:
    flow_db_drop -= 2.0  # 40 to 30 km/h speed reduction saves ~2 dB

for s in st.session_state["sources"]:
    if not s.active:
        continue
    s_night = NoiseSource(s.sid, s.name, s.x, s.y, s.z, s.lw, s.stype)
    if s.stype == "Road Traffic":
        s_night.lw = round(max(40.0, s.lw + flow_db_drop), 1)
        night_sources.append(s_night)
    elif "construction" in s.name.lower() or "drill" in s.name.lower() or "jackhammer" in s.name.lower():
        # Construction machinery turned off at night
        pass
    else:
        # Stationary baseline equipment continues
        night_sources.append(s_night)

# Execute vectorized simulation for Day & Night
with st.spinner("Computing Day and Night sound fields across the neighborhood..."):
    sim_day = simulate_grid(
        city=city,
        sources=day_sources,
        grid_res=calc_res,
        ground_type=st.session_state["env_params"]["ground_type"],
        temp_c=st.session_state["env_params"]["temp_c"],
        rel_humidity=st.session_state["env_params"]["humidity"],
        green_buffer=st.session_state["env_params"]["green_buffer"]
    )
    
    sim_night = simulate_grid(
        city=city,
        sources=night_sources,
        grid_res=calc_res,
        ground_type=st.session_state["env_params"]["ground_type"],
        temp_c=max(5.0, st.session_state["env_params"]["temp_c"] - 5.0), # Cooler night
        rel_humidity=min(95.0, st.session_state["env_params"]["humidity"] + 15.0),
        green_buffer=st.session_state["env_params"]["green_buffer"]
    )

# ----------------- COMPOSITE METRICS (Lden & Ldn) -----------------
L_grid_day = sim_day["L_total"]
L_grid_night = sim_night["L_total"]
delta_grid = L_grid_day - L_grid_night

mean_day_db = float(np.mean(L_grid_day))
max_day_db = float(np.max(L_grid_day))
mean_night_db = float(np.mean(L_grid_night))
max_night_db = float(np.max(L_grid_night))
mean_drop_db = mean_day_db - mean_night_db

# 24-Hour traffic distribution factors
hours = np.arange(24)
factors = get_diurnal_traffic_factors()

# Hourly mean area levels
hourly_area_levels = mean_day_db + 10.0 * np.log10(np.maximum(0.08, factors))

# Evening level (19:00 - 23:00)
evening_hours = np.array([19, 20, 21, 22])
mean_evening_db = float(10.0 * np.log10(np.mean(10.0 ** (hourly_area_levels[evening_hours] / 10.0))))

# Lden formula: 12h Day, 4h Evening (+5 dB), 8h Night (+10 dB)
e_day = (12.0 / 24.0) * (10.0 ** (mean_day_db / 10.0))
e_eve = (4.0 / 24.0) * (10.0 ** ((mean_evening_db + 5.0) / 10.0))
e_ngt = (8.0 / 24.0) * (10.0 ** ((mean_night_db + 10.0) / 10.0))
L_den = float(10.0 * np.log10(e_day + e_eve + e_ngt))

# Compliance rates
night_compliant_pct = float(np.mean(L_grid_night <= cpcb_night_limit) * 100.0)
day_compliant_pct = float(np.mean(L_grid_day <= cpcb_day_limit) * 100.0)

# Receiver probe levels
rec_coords = st.session_state.get("receiver", (150.0, 150.0, 1.5))
rec_day_info = evaluate_single_receiver(
    rx=rec_coords[0], ry=rec_coords[1], rz=rec_coords[2],
    city=city, sources=day_sources,
    ground_type=st.session_state["env_params"]["ground_type"]
)
rec_day = rec_day_info["total_db"]

rec_night_info = evaluate_single_receiver(
    rx=rec_coords[0], ry=rec_coords[1], rz=rec_coords[2],
    city=city, sources=night_sources,
    ground_type=st.session_state["env_params"]["ground_type"]
)
rec_night = rec_night_info["total_db"]

# ----------------- TOP KPI METRIC STRIP -----------------
kpi_html = f"""
<div class="kpi-container">
    <div class="kpi-card">
        <div class="kpi-title">Daytime Average (06:00 - 22:00)</div>
        <div class="kpi-value">{mean_day_db:.1f} <span style="font-size:1.1rem; color:#94a3b8;">dB(A)</span></div>
        <div class="kpi-sub">Peak: {max_day_db:.1f} dB(A) | Within limit: {day_compliant_pct:.0f}%</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-title">Nighttime Average (22:00 - 06:00)</div>
        <div class="kpi-value" style="color:#10b981;">{mean_night_db:.1f} <span style="font-size:1.1rem; color:#94a3b8;">dB(A)</span></div>
        <div class="kpi-sub">Night Drop: <b>-{mean_drop_db:.1f} dB</b> | Peak: {max_night_db:.1f} dB</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-title">Full-Day Noise Score (Lden)</div>
        <div class="kpi-value" style="color:#38bdf8;">{L_den:.1f} <span style="font-size:1.1rem; color:#94a3b8;">dB(A)</span></div>
        <div class="kpi-sub">Overall 24h score with evening & sleep weight</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-title">Night Legal Check ({cpcb_night_limit} dB)</div>
        <div class="kpi-value" style="color: {'#10b981' if night_compliant_pct >= 70 else '#f59e0b' if night_compliant_pct >= 40 else '#ef4444'};">
            {night_compliant_pct:.1f}%
        </div>
        <div class="kpi-sub">{'Meets Night Limit' if night_compliant_pct >= 70 else 'Action Recommended' if night_compliant_pct >= 40 else 'Exceeds Night Limit'}</div>
    </div>
</div>
"""
st.markdown(kpi_html, unsafe_allow_html=True)

# Status explainer under KPI strip
if night_compliant_pct >= 70:
    diurnal_status = f"Safe: {night_compliant_pct:.1f}% of the neighborhood stays within the legal night limit ({cpcb_night_limit} dB) for restful sleep."
    diurnal_border = "#10b981"
elif night_compliant_pct >= 40:
    diurnal_status = f"A bit loud: {100.0 - night_compliant_pct:.1f}% of the area exceeds the night limit near roads. Truck curfews help reduce this."
    diurnal_border = "#f59e0b"
else:
    diurnal_status = f"Too loud: Only {night_compliant_pct:.1f}% meets the night limit. Strict truck curfews and speed limits are recommended."
    diurnal_border = "#ef4444"

st.markdown(f"""
<div style="background:rgba(30,41,59,0.5); border-left:4px solid {diurnal_border}; padding:10px 14px; border-radius:6px; margin: 12px 0 20px 0;">
    <b>In simple words:</b> {diurnal_status} Sound is measured in <b>dB(A) (decibels, the unit for loudness)</b>.
</div>
""", unsafe_allow_html=True)

# ----------------- MAIN INTERACTIVE TABS (4 TABS ONLY - TAB 5 REMOVED) -----------------
tab1, tab2, tab3, tab4 = st.tabs([
    "🗺️ Day vs Night Noise Maps",
    "🕒 24-Hour Time Slider",
    "📈 24-Hour Noise Graph",
    "🛌 Sleep Protection & Building Check"
])

# ----------------- TAB 1: DUAL SPATIAL HEATMAPS -----------------
with tab1:
    st.markdown("#### Day vs Night Noise Maps Side-by-Side")
    st.caption("See how streets quieten down at night as vehicle traffic thins and construction stops.")
    
    col_day, col_night = st.columns(2)
    with col_day:
        st.markdown(f"##### ☀️ Daytime Noise (Legal Limit: {cpcb_day_limit} dB)")
        fig_day = build_2d_heatmap_plot(
            sim_data=sim_day,
            cpcb_limit=cpcb_day_limit,
            colorblind_mode=st.session_state.get("colorblind_mode", False)
        )
        st.plotly_chart(fig_day, width="stretch", key="p3_fig_day_plot")
        
    with col_night:
        st.markdown(f"##### 🌙 Nighttime Noise (Legal Limit: {cpcb_night_limit} dB)")
        fig_night = build_2d_heatmap_plot(
            sim_data=sim_night,
            cpcb_limit=cpcb_night_limit,
            colorblind_mode=st.session_state.get("colorblind_mode", False)
        )
        st.plotly_chart(fig_night, width="stretch", key="p3_fig_night_plot")
        
    st.markdown("---")
    st.markdown("#### How Much Quieter is it at Night? (Day dB - Night dB)")
    st.caption("Green and yellow areas show where sound drops by 6 to 14 dB after dark.")
    fig_delta = build_scenario_difference_plot(sim_baseline=sim_day, sim_mitigated=sim_night)
    fig_delta.update_layout(title="Nighttime Sound Drop: (Daytime Noise - Nighttime Noise in dB)")
    st.plotly_chart(fig_delta, width="stretch", key="p3_fig_delta_plot")

    st.caption("**In simple words:** Streets are significantly louder during the day (red and orange areas). At night, lower traffic volumes turn most residential streets green and blue (quiet).")

# ----------------- TAB 2: 24-HOUR INTERACTIVE SCRUBBER -----------------
with tab2:
    st.markdown("#### 🕒 Hour-by-Hour Neighborhood Noise")
    st.caption("Slide through each hour of the 24-hour day to see morning rush hour, afternoon traffic, and nighttime calm.")
    
    sel_hour = st.slider("Select Hour of the Day (00:00 to 23:00)", min_value=0, max_value=23, value=8, step=1, key="p3_scrubber_hour")
    
    # Classify time of day
    if 7 <= sel_hour <= 10:
        hour_tag = "🌅 Morning Rush Hour (Going to work/school)"
        tag_color = "#f59e0b"
    elif 11 <= sel_hour <= 16:
        hour_tag = "☀️ Daytime Regular Traffic & Shops"
        tag_color = "#38bdf8"
    elif 17 <= sel_hour <= 20:
        hour_tag = "🌆 Evening Rush Hour (Going home)"
        tag_color = "#ec4899"
    elif 21 <= sel_hour <= 22:
        hour_tag = "🌙 Late Evening Wind-down"
        tag_color = "#818cf8"
    else:
        hour_tag = "🛌 Quiet Sleep Hours"
        tag_color = "#10b981"
        
    traffic_pct_at_hour = factors[sel_hour] * 100.0
    hour_spl_area = hourly_area_levels[sel_hour]
    hour_spl_rec = rec_day + 10.0 * np.log10(max(0.08, factors[sel_hour]))
    current_limit = cpcb_night_limit if (sel_hour < 6 or sel_hour >= 22) else cpcb_day_limit
    
    scrub_col1, scrub_col2, scrub_col3, scrub_col4 = st.columns(4)
    with scrub_col1:
        st.markdown(f"""
        <div style="background:rgba(30,41,59,0.7); border:1px solid rgba(56,189,248,0.3); border-radius:10px; padding:14px; text-align:center;">
            <div style="font-size:0.8rem; color:#94a3b8; text-transform:uppercase;">Clock Time</div>
            <div style="font-size:1.8rem; font-weight:800; color:#ffffff; font-family:'JetBrains Mono';">{sel_hour:02d}:00</div>
            <div style="font-size:0.8rem; color:{tag_color}; font-weight:600;">{hour_tag.split('(')[0]}</div>
        </div>
        """, unsafe_allow_html=True)
    with scrub_col2:
        st.markdown(f"""
        <div style="background:rgba(30,41,59,0.7); border:1px solid rgba(56,189,248,0.3); border-radius:10px; padding:14px; text-align:center;">
            <div style="font-size:0.8rem; color:#94a3b8; text-transform:uppercase;">Traffic Volume</div>
            <div style="font-size:1.8rem; font-weight:800; color:#38bdf8; font-family:'JetBrains Mono';">{traffic_pct_at_hour:.0f}%</div>
            <div style="font-size:0.8rem; color:#cbd5e1;">Relative to peak traffic</div>
        </div>
        """, unsafe_allow_html=True)
    with scrub_col3:
        st.markdown(f"""
        <div style="background:rgba(30,41,59,0.7); border:1px solid rgba(56,189,248,0.3); border-radius:10px; padding:14px; text-align:center;">
            <div style="font-size:0.8rem; color:#94a3b8; text-transform:uppercase;">Average Area Noise</div>
            <div style="font-size:1.8rem; font-weight:800; color:{'#ef4444' if hour_spl_area > current_limit else '#10b981'}; font-family:'JetBrains Mono';">{hour_spl_area:.1f} dB</div>
            <div style="font-size:0.8rem; color:#cbd5e1;">Legal Limit: {current_limit} dB</div>
        </div>
        """, unsafe_allow_html=True)
    with scrub_col4:
        st.markdown(f"""
        <div style="background:rgba(30,41,59,0.7); border:1px solid rgba(56,189,248,0.3); border-radius:10px; padding:14px; text-align:center;">
            <div style="font-size:0.8rem; color:#94a3b8; text-transform:uppercase;">Meter Probe Spot</div>
            <div style="font-size:1.8rem; font-weight:800; color:#38bdf8; font-family:'JetBrains Mono';">{hour_spl_rec:.1f} dB</div>
            <div style="font-size:0.8rem; color:#cbd5e1;">Probe at ({rec_coords[0]:.0f}m, {rec_coords[1]:.0f}m)</div>
        </div>
        """, unsafe_allow_html=True)
        
    # Generate scaled grid for selected hour
    scale_delta = 10.0 * np.log10(max(0.08, factors[sel_hour]))
    hour_grid = np.clip(L_grid_day + scale_delta, 25.0, 95.0)
    sim_hour = {
        "X": sim_day["X"],
        "Y": sim_day["Y"],
        "x_coords": sim_day["x_coords"],
        "y_coords": sim_day["y_coords"],
        "L_total": hour_grid,
        "grid_res": sim_day["grid_res"],
        "city": city,
        "sources": day_sources
    }
    
    fig_hour = build_2d_heatmap_plot(
        sim_data=sim_hour,
        cpcb_limit=current_limit,
        colorblind_mode=st.session_state.get("colorblind_mode", False)
    )
    fig_hour.update_layout(title=f"Noise Map at {sel_hour:02d}:00 ({hour_tag})")
    st.plotly_chart(fig_hour, width="stretch", key="p3_fig_hour_scrub")
    st.caption(f"**In simple words:** At {sel_hour:02d}:00, traffic is at {traffic_pct_at_hour:.0f}% of peak flow. Green and blue areas are quiet, while red areas exceed the {current_limit} dB legal limit.")

# ----------------- TAB 3: 24-HOUR EXPOSURE CURVES -----------------
with tab3:
    st.markdown("#### 📈 24-Hour Noise Graph")
    st.caption("See how loudness rises and falls through the day compared to legal limits and healthy sleep guidelines.")
    
    # Calculate hourly receptor progression
    rec_hourly = rec_day + 10.0 * np.log10(np.maximum(0.08, factors))
    cpcb_step = [cpcb_night_limit if (h < 6 or h >= 22) else cpcb_day_limit for h in hours]
    who_sleep_limit = [40.0 for _ in hours]
    
    fig_curve = go.Figure()
    
    # Shaded Night Regions (00:00 - 06:00 and 22:00 - 24:00)
    fig_curve.add_vrect(x0=0, x1=6, fillcolor="rgba(30, 27, 75, 0.45)", layer="below", line_width=0, annotation_text="Night Sleep Window", annotation_position="top left")
    fig_curve.add_vrect(x0=22, x1=23, fillcolor="rgba(30, 27, 75, 0.45)", layer="below", line_width=0)
    
    # Area Mean line
    fig_curve.add_trace(go.Scatter(
        x=hours, y=hourly_area_levels, mode="lines+markers",
        name="Area Average Loudness",
        line=dict(color="#38bdf8", width=3),
        marker=dict(size=7, color="#0284c7")
    ))
    
    # Receiver probe line
    fig_curve.add_trace(go.Scatter(
        x=hours, y=rec_hourly, mode="lines+markers",
        name=f"Meter Probe Spot ({rec_coords[0]:.0f}m, {rec_coords[1]:.0f}m)",
        line=dict(color="#ec4899", width=2.5, dash="dot"),
        marker=dict(size=6, color="#be185d")
    ))
    
    # CPCB Limit Step Function
    fig_curve.add_trace(go.Scatter(
        x=hours, y=cpcb_step, mode="lines",
        name=f"CPCB Legal Limit ({cpcb_day_limit} dB Day / {cpcb_night_limit} dB Night)",
        line=dict(color="#f59e0b", width=2.5, dash="dash")
    ))
    
    # WHO Restful Sleep guideline
    fig_curve.add_trace(go.Scatter(
        x=hours, y=who_sleep_limit, mode="lines",
        name="WHO Healthy Sleep Target (40 dB)",
        line=dict(color="#10b981", width=1.8, dash="longdash")
    ))
    
    fig_curve.update_layout(
        template="plotly_dark",
        paper_bgcolor=DARK_LAYOUT_TEMPLATE["paper_bgcolor"],
        plot_bgcolor=DARK_LAYOUT_TEMPLATE["plot_bgcolor"],
        font=DARK_LAYOUT_TEMPLATE["font"],
        title="24-Hour Noise Profile vs Legal Limits & Biological Sleep Target",
        xaxis=dict(title="Hour of Day (00:00 to 23:00)", tickmode="linear", dtick=2),
        yaxis=dict(title="Sound Level dB(A)", range=[30, max(85, max_day_db + 2)]),
        legend=dict(orientation="h", y=1.14, x=0.05),
        margin=dict(l=30, r=30, t=50, b=30)
    )
    st.plotly_chart(fig_curve, width="stretch", key="p3_fig_curve_diurnal_trajectory")
    st.caption("**In simple words:** The blue line shows loudness over the day. Notice the spikes during morning (8-9 AM) and evening (6-7 PM) rush hours, and the drop during the shaded night sleep period. The green line is the WHO 40 dB target for deep, healthy sleep.")

    with st.expander("Technical details (for students and experts)"):
        st.markdown("""
        **Hourly Diurnal Traffic Modeling:**
        - Traffic volume follows empirical urban diurnal distributions with morning and evening commuter peaks.
        - Hourly sound levels are computed via logarithmic energy conversion:
        $$L_{\\text{hour}} = L_{\\text{day}} + 10 \\cdot \\log_{10}(f_{\\text{traffic}})$$
        """)

# ----------------- TAB 4: SLEEP DISRUPTION & HEALTH AUDIT -----------------
with tab4:
    st.markdown("#### 🛌 Sleep Protection & Health Check")
    st.caption("Checking nighttime noise against World Health Organization (WHO) Night Noise Guidelines to protect sleep.")
    
    # WHO NNG categories for night grid
    pct_restful = float(np.mean(L_grid_night < 40.0) * 100.0)
    pct_moderate = float(np.mean((L_grid_night >= 40.0) & (L_grid_night < 50.0)) * 100.0)
    pct_severe = float(np.mean(L_grid_night >= 50.0) * 100.0)
    
    nng_c1, nng_c2, nng_c3 = st.columns(3)
    with nng_c1:
        st.markdown(f"""
        <div style="background:rgba(16,185,129,0.12); border:1px solid rgba(16,185,129,0.3); border-radius:12px; padding:18px; text-align:center;">
            <div style="font-size:0.82rem; color:#34d399; font-weight:700; text-transform:uppercase;">Restful Sleep Area (&lt; 40 dB)</div>
            <div style="font-size:2.2rem; font-weight:800; color:#34d399; font-family:'JetBrains Mono'; margin:6px 0;">{pct_restful:.1f}%</div>
            <div style="font-size:0.8rem; color:#cbd5e1;">Ideal biological sleep; no wake-up triggers</div>
        </div>
        """, unsafe_allow_html=True)
    with nng_c2:
        st.markdown(f"""
        <div style="background:rgba(245,158,11,0.12); border:1px solid rgba(245,158,11,0.3); border-radius:12px; padding:18px; text-align:center;">
            <div style="font-size:0.82rem; color:#fbbf24; font-weight:700; text-transform:uppercase;">Moderate Noise (40 - 50 dB)</div>
            <div style="font-size:2.2rem; font-weight:800; color:#fbbf24; font-family:'JetBrains Mono'; margin:6px 0;">{pct_moderate:.1f}%</div>
            <div style="font-size:0.8rem; color:#cbd5e1;">Slight disturbance for light sleepers</div>
        </div>
        """, unsafe_allow_html=True)
    with nng_c3:
        st.markdown(f"""
        <div style="background:rgba(239,68,68,0.12); border:1px solid rgba(239,68,68,0.3); border-radius:12px; padding:18px; text-align:center;">
            <div style="font-size:0.82rem; color:#f87171; font-weight:700; text-transform:uppercase;">High Noise Area (&gt; 50 dB)</div>
            <div style="font-size:2.2rem; font-weight:800; color:#f87171; font-family:'JetBrains Mono'; margin:6px 0;">{pct_severe:.1f}%</div>
            <div style="font-size:0.8rem; color:#cbd5e1;">Can disrupt deep sleep and raise stress</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.caption(f"**In simple words:** WHO guidelines recommend bedroom noise stay under 40 dB(A) for restful sleep. In this neighborhood, {pct_restful:.1f}% of the area achieves this restful standard at night.")

    st.markdown("---")
    st.markdown("#### Building Outside Wall Exposure at Night")
    st.caption("How much noise reaches the outside walls of each building at night. Buildings marked 'FAIL' exceed the nighttime legal limit.")
    facade_day = evaluate_facade_exposures(city, day_sources, st.session_state["env_params"]["ground_type"])
    facade_night = evaluate_facade_exposures(city, night_sources, st.session_state["env_params"]["ground_type"])
    
    table_rows = []
    for fd, fn in zip(facade_day, facade_night):
        status = "PASS" if fn["max_facade_db"] <= cpcb_night_limit else "FAIL"
        drop = fd["max_facade_db"] - fn["max_facade_db"]
        table_rows.append({
            "Building": fn["building_name"],
            "Zoning": fn["zone_type"],
            "Height (m)": fn["height_m"],
            "Day Loudness (dB)": fd["max_facade_db"],
            "Night Loudness (dB)": fn["max_facade_db"],
            "Night Drop (dB)": f"-{drop:.1f} dB",
            "Night Legal Limit": f"{cpcb_night_limit} dB",
            "Status": status
        })
    df_facade = pd.DataFrame(table_rows)
    st.dataframe(df_facade, width="stretch")
    st.caption(f"**In simple words:** Buildings marked 'PASS' have outside noise within the {cpcb_night_limit} dB nighttime legal limit. For buildings marked 'FAIL', night truck curfews or double-pane windows help ensure quiet bedrooms.")
