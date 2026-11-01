"""
UrbanSound 3D - Simulation Engine & Spatial Soundscape Studio.
Interactive 3D acoustics studio with city geometry, traffic sources, atmospheric parameters,
sound barriers, and live multidimensional Plotly renders.
"""

import os
import streamlit as st
import numpy as np
import pandas as pd

from core.geometry import (
    create_residential_colony,
    create_dense_downtown,
    create_industrial_residential_mix,
    fetch_osm_city,
    SoundBarrier
)
from core.sources import (
    SOURCE_PRESETS,
    NoiseSource,
    discretize_road_to_sources
)
from core.propagation import (
    simulate_grid,
    evaluate_single_receiver,
    calculate_atmospheric_alpha
)
from core.visualization import (
    build_3d_city_scene,
    build_3d_noise_surface_plot,
    build_2d_heatmap_plot,
    build_receiver_breakdown_chart,
    build_distance_decay_plot
)
from core.utils import init_session_state, render_mobile_navigation

st.set_page_config(
    page_title="UrbanSound 3D - Acoustic Simulator",
    page_icon="🔊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
css_path = os.path.join(os.path.dirname(__file__), "..", "assets", "style.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Initialize Session State
init_session_state()

# Mobile top navigation bar (visible only on small screens <= 768px)
render_mobile_navigation(show_settings_hint=True)

# ----------------- SIDEBAR CONTROLS -----------------
with st.sidebar:
    st.markdown("### 🎛️ Noise Settings")
    
    # 1. City Selection
    st.markdown("#### 1. Pick a City Layout")
    city_choice = st.selectbox(
        "Select City Layout",
        ["Residential Colony", "Dense Downtown", "Industrial + Residential Mix", "Custom (OpenStreetMap)"],
        index=["Residential Colony", "Dense Downtown", "Industrial + Residential Mix", "Custom (OpenStreetMap)"].index(
            st.session_state["city_type"] if st.session_state["city_type"] in ["Residential Colony", "Dense Downtown", "Industrial + Residential Mix"] else "Custom (OpenStreetMap)"
        ),
        help="Choose a pre-made neighborhood or download real streets from OpenStreetMap."
    )
    
    if city_choice == "Custom (OpenStreetMap)":
        osm_query = st.text_input("City / Neighborhood Name", value="Connaught Place, New Delhi", help="Requires internet; automatically falls back if offline.")
        if st.button("Fetch OSM Data", key="btn_osm"):
            with st.spinner(f"Downloading street map for {osm_query}..."):
                osm_city, msg = fetch_osm_city(osm_query)
                if osm_city is not None:
                    st.session_state["city"] = osm_city
                    st.session_state["city_type"] = f"OSM: {osm_query}"
                    st.success(msg)
                else:
                    st.warning(msg)
                    st.session_state["city"] = create_residential_colony()
                    st.session_state["city_type"] = "Residential Colony"
    else:
        if city_choice != st.session_state["city_type"]:
            st.session_state["city_type"] = city_choice
            if city_choice == "Residential Colony":
                st.session_state["city"] = create_residential_colony()
            elif city_choice == "Dense Downtown":
                st.session_state["city"] = create_dense_downtown()
            elif city_choice == "Industrial + Residential Mix":
                st.session_state["city"] = create_industrial_residential_mix()
            # Regenerate default road sources for this city
            city = st.session_state["city"]
            new_sources = []
            for road in city.roads:
                new_sources.extend(discretize_road_to_sources(
                    road["name"], road["start"], road["end"], traffic_vol=road["traffic_vol"]
                ))
            st.session_state["sources"] = new_sources
            
    grid_res = st.slider("Map Detail Level (Grid Points)", min_value=40, max_value=120, value=st.session_state["env_params"]["grid_res"], step=10, help="Grid detail (e.g. 80 gives 6,400 test spots across the area). Higher values give smoother pictures.")
    st.session_state["env_params"]["grid_res"] = grid_res

    st.markdown("---")
    
    # 2. Environmental Conditions
    st.markdown("#### 2. Weather & Ground")
    c1, c2 = st.columns(2)
    with c1:
        temp_c = st.slider("Temperature (°C)", min_value=0.0, max_value=45.0, value=float(st.session_state["env_params"]["temp_c"]), step=1.0, help="Air temperature affects how far sound travels.")
    with c2:
        humidity = st.slider("Humidity (%)", min_value=20.0, max_value=95.0, value=float(st.session_state["env_params"]["humidity"]), step=5.0, help="Moisture in the air absorbs sound over long distances.")
    
    ground_type = st.selectbox(
        "Ground Surface Type",
        ["mixed", "hard", "grass"],
        index=["mixed", "hard", "grass"].index(st.session_state["env_params"]["ground_type"]),
        format_func=lambda x: {"mixed": "Mixed (lawns & paved roads)", "hard": "Hard (concrete / asphalt - bounces sound)", "grass": "Soft / Grass (parks & soil - absorbs sound)"}[x],
        help="Hard surfaces bounce sound back into the air; grass and soil soak up sound."
    )
    time_of_day = st.radio("Time of Day", ["Day", "Night"], horizontal=True, help="Night traffic is usually lighter and quieter than daytime traffic.")
    st.session_state["env_params"].update({
        "temp_c": temp_c, "humidity": humidity, "ground_type": ground_type, "time_of_day": time_of_day
    })
    
    alpha = calculate_atmospheric_alpha(temp_c, humidity)
    st.caption(f"⚡ Sound reduced by air: **{alpha:.2f} dB/km**")
    
    st.markdown("---")
    
    # 3. Mitigation Tools
    st.markdown("#### 3. Noise Reduction Tools")
    barrier_enable = st.checkbox("Put Up a Sound Barrier Wall", value=st.session_state["mitigation_params"]["barrier_enabled"], help="A solid wall along the road that blocks sound waves from reaching homes.")
    b_height = 4.0
    if barrier_enable:
        b_height = st.slider("Wall Height (meters)", 2.0, 8.0, float(st.session_state["mitigation_params"]["barrier_height"]), step=0.5, help="Taller walls block more noise and cast larger quiet shadow zones.")
        st.session_state["mitigation_params"]["barrier_height"] = b_height
        st.session_state["mitigation_params"]["barrier_enabled"] = True
        
        # Configure barrier coordinates along main road frontage
        city = st.session_state["city"]
        city.clear_barriers()
        if city.roads:
            main_road = city.roads[0]
            # Place wall parallel to road 10m into property line
            ry = main_road["start"][1] + (10.0 if main_road["start"][1] < 150 else -10.0)
            wall = SoundBarrier(20.0, ry, 280.0, ry, height=b_height, name="Acoustic Shield Wall")
            city.add_barrier(wall)
    else:
        st.session_state["mitigation_params"]["barrier_enabled"] = False
        st.session_state["city"].clear_barriers()
        
    traffic_reduction = st.slider("Cut Traffic Volume (%)", 0, 75, int(st.session_state["mitigation_params"]["traffic_reduction_pct"]), step=5, help="Reducing vehicle numbers lowers overall neighborhood loudness.")
    st.session_state["mitigation_params"]["traffic_reduction_pct"] = traffic_reduction
    
    green_buffer = st.checkbox("Add Trees & Green Buffer", value=st.session_state["env_params"]["green_buffer"], help="Rows of trees and bushes absorb a small amount of extra sound.")
    st.session_state["env_params"]["green_buffer"] = green_buffer
    
    st.markdown("---")
    colorblind = st.toggle("Colorblind-Friendly Colors", value=st.session_state["colorblind_mode"], help="Use high-contrast blue and yellow colors suitable for all types of vision.")
    st.session_state["colorblind_mode"] = colorblind
    
    # Run Simulation Trigger
    run_sim = st.button("🚀 Update Noise Simulation", width="stretch")

# ----------------- PAGE HEADER & HOW TO USE -----------------
st.title("🏙️ City Noise Simulator: See How Sound Travels")
st.caption("See how noise from traffic and construction travels through city streets, bounces off buildings, and gets blocked by sound barriers.")

st.info("""
**How to use this page (in 3 easy steps):**
1. **Pick your city and weather** in the settings on the left sidebar (or tap the **>** arrow at the top left if on a phone).
2. **Try noise control tools** like putting up a sound barrier wall or cutting traffic flow.
3. **Explore the 3D and 2D views below** to see quiet green zones and loud red zones, or test any exact spot with the probe.
""")

# ----------------- NOISE SOURCES MANAGEMENT (EXPANDER) -----------------
with st.expander("🔊 View or Add Noise Sources (Traffic, Diggers, Trucks)", expanded=False):
    s_col1, s_col2 = st.columns([2, 1])
    with s_col1:
        st.markdown("##### Current Noise Sources on the Map")
        src_table_data = []
        for s in st.session_state["sources"]:
            src_table_data.append({
                "ID": s.sid, "Name": s.name, "Type": s.stype,
                "X (m)": round(s.x, 1), "Y (m)": round(s.y, 1),
                "Power Lw dB(A)": s.lw, "Active": s.active
            })
        st.dataframe(pd.DataFrame(src_table_data), width="stretch", height=180)
        
    with s_col2:
        st.markdown("##### Add a New Noise Source")
        preset_name = st.selectbox("Choose Noise Type", list(SOURCE_PRESETS.keys()), help="Select a typical sound like road traffic, a construction digger, or an emergency siren.")
        preset_info = SOURCE_PRESETS[preset_name]
        new_x = st.number_input("East-West Spot X (m)", min_value=0.0, max_value=300.0, value=150.0, step=10.0, help="Where horizontally the noise is located.")
        new_y = st.number_input("North-South Spot Y (m)", min_value=0.0, max_value=300.0, value=150.0, step=10.0, help="Where vertically the noise is located.")
        new_lw = st.slider("Source Loudness Lw dB(A)", 70.0, 120.0, float(preset_info["lw"]), step=1.0, help="Sound power emitted at the source in dB(A) (decibels, the unit for loudness).")
        
        if st.button("➕ Add Source to Grid"):
            new_id = f"SRC_{len(st.session_state['sources']) + 1}"
            st.session_state["sources"].append(NoiseSource(
                sid=new_id, name=preset_name.split("(")[0].strip(),
                x=new_x, y=new_y, z=preset_info["height"], lw=new_lw, stype=preset_info["category"]
            ))
            st.success(f"Added {preset_name} at ({new_x}, {new_y})")
            st.rerun()

# ----------------- SIMULATION EXECUTION -----------------
# Apply traffic reduction policy to active road sources
current_sources = []
for s in st.session_state["sources"]:
    s_copy = NoiseSource(s.sid, s.name, s.x, s.y, s.z, s.lw, s.stype)
    s_copy.active = s.active
    if s.stype == "Road Traffic" and traffic_reduction > 0:
        # Lw decreases with traffic flow reduction: 10 * log10(1 - reduction_pct)
        flow_factor = max(0.05, 1.0 - (traffic_reduction / 100.0))
        s_copy.lw = round(s.lw + 10.0 * np.log10(flow_factor), 1)
    # Day/Night shift
    if time_of_day == "Night" and s.stype == "Road Traffic":
        s_copy.lw = round(s_copy.lw - 6.0, 1) # Night traffic attenuation
    current_sources.append(s_copy)

if run_sim or "sim_current" not in st.session_state:
    with st.spinner("Calculating sound propagation across the neighborhood..."):
        sim_result = simulate_grid(
            city=st.session_state["city"],
            sources=current_sources,
            grid_res=st.session_state["env_params"]["grid_res"],
            ground_type=st.session_state["env_params"]["ground_type"],
            temp_c=st.session_state["env_params"]["temp_c"],
            rel_humidity=st.session_state["env_params"]["humidity"],
            green_buffer=st.session_state["env_params"]["green_buffer"]
        )
        st.session_state["sim_current"] = sim_result
        if not st.session_state["mitigation_params"]["barrier_enabled"] and traffic_reduction == 0:
            st.session_state["sim_baseline"] = sim_result

sim_current = st.session_state["sim_current"]

# ----------------- TOP KPI METRIC STRIP -----------------
L_grid = sim_current["L_total"]
max_spl = float(np.max(L_grid))
mean_spl = float(np.mean(L_grid))
min_spl = float(np.min(L_grid))
pct_loud = float(np.mean(L_grid > 65.0) * 100.0)

kpi_html = f"""
<div class="kpi-container">
    <div class="kpi-card">
        <div class="kpi-title">Loudest Spot</div>
        <div class="kpi-value">{max_spl:.1f} <span style="font-size:1.1rem; color:#94a3b8;">dB(A)</span></div>
        <div class="kpi-sub">Near the busiest road or machine</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-title">Average Neighborhood Noise</div>
        <div class="kpi-value">{mean_spl:.1f} <span style="font-size:1.1rem; color:#94a3b8;">dB(A)</span></div>
        <div class="kpi-sub">Average loudness across the whole area</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-title">Noisy Area (&gt; 65 dB)</div>
        <div class="kpi-value" style="color: {'#ef4444' if pct_loud > 25 else '#10b981'};">{pct_loud:.1f}%</div>
        <div class="kpi-sub">Too loud for comfortable living</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-title">Map Test Spots</div>
        <div class="kpi-value" style="color: #38bdf8;">{L_grid.size:,}</div>
        <div class="kpi-sub">{sim_current['grid_res']}x{sim_current['grid_res']} test spots calculated</div>
    </div>
</div>
"""
st.markdown(kpi_html, unsafe_allow_html=True)

# In simple words explainer under KPI cards
if mean_spl <= 55.0:
    sim_status_text = "Safe: Most of the neighborhood stays under 55 dB(A) (the recommended comfortable limit for homes)."
    status_border = "#10b981"
elif mean_spl <= 65.0:
    sim_status_text = "A bit loud: Noise is noticeable, especially near roads. Adding a barrier wall or reducing traffic helps."
    status_border = "#f59e0b"
else:
    sim_status_text = "Too loud: Wide areas exceed safe noise levels for neighborhoods. Noise barriers are strongly advised."
    status_border = "#ef4444"

st.markdown(f"""
<div style="background:rgba(30,41,59,0.5); border-left:4px solid {status_border}; padding:10px 14px; border-radius:6px; margin: 12px 0 20px 0;">
    <b>In simple words:</b> {sim_status_text} Sound is measured in <b>dB(A) (decibels, the unit for loudness)</b>.
</div>
""", unsafe_allow_html=True)

# ----------------- MAIN INTERACTIVE TABS -----------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏙️ 3D City View",
    "⛰️ 3D Noise Hills",
    "🗺️ 2D Noise Map",
    "🎯 Check Noise at Any Spot",
    "📉 How Sound Fades with Distance"
])

with tab1:
    st.markdown("#### Interactive 3D Neighborhood")
    st.caption("Rotate (click and drag), zoom (scroll wheel), or move around (right-click and drag) to explore how sound travels past buildings and walls.")
    
    layer_col1, layer_col2, layer_col3, layer_col4 = st.columns(4)
    with layer_col1:
        toggle_bld = st.checkbox("Show 3D Buildings", value=True, help="Display building shapes.")
    with layer_col2:
        toggle_surf = st.checkbox("Show Noise Colors on Ground", value=True, help="Show colored sound levels on the ground.")
    with layer_col3:
        toggle_src = st.checkbox("Show Noise Sources", value=True, help="Show dots where sound originates.")
    with layer_col4:
        toggle_bar = st.checkbox("Show Sound Barrier Wall", value=True, help="Show the protective acoustic wall.")
        
    fig_3d = build_3d_city_scene(
        sim_current,
        show_buildings=toggle_bld,
        show_noise_surface=toggle_surf,
        show_sources=toggle_src,
        show_barriers=toggle_bar,
        colorblind_mode=st.session_state["colorblind_mode"]
    )
    st.plotly_chart(fig_3d, width="stretch", config={"displayModeBar": True}, key="sim_fig_3d")
    st.caption("**In simple words:** This 3D view shows where noise spreads. Red and orange spots are loud; green and blue spots are quiet. Notice how buildings and walls block sound waves, creating quiet shadow zones behind them.")

with tab2:
    st.markdown("#### 3D Noise Landscape (Taller Hills = Louder Spots)")
    st.caption("This view turns sound loudness into height. Peaks show where sound is loudest; valleys show quiet sheltered pockets.")
    fig_surface = build_3d_noise_surface_plot(sim_current, colorblind_mode=st.session_state["colorblind_mode"])
    st.plotly_chart(fig_surface, width="stretch", key="sim_fig_surface")
    st.caption("**In simple words:** Think of this as a mountain map of sound. Tall red peaks are loud areas near busy roads. Valleys behind tall buildings show quiet shadow zones where noise cannot easily reach.")

with tab3:
    st.markdown("#### 2D Top-Down Noise Map with Legal Limits")
    st.caption("A bird's-eye map showing building shapes, roads, and sound contours.")
    cpcb_thresh = st.selectbox(
        "Highlight Legal Limit Line",
        [None, 45.0, 50.0, 55.0, 65.0, 75.0],
        index=3,
        format_func=lambda x: "Show no limit line" if x is None else f"CPCB Limit: {x} dB(A) (India's pollution control standard)",
        help="Draws a bold boundary line around areas that exceed this legal limit."
    )
    fig_2d = build_2d_heatmap_plot(sim_current, cpcb_limit=cpcb_thresh, colorblind_mode=st.session_state["colorblind_mode"])
    st.plotly_chart(fig_2d, width="stretch", key="sim_fig_2d")
    st.caption("**In simple words:** This top-down map shows where sound spreads across the ground. Areas inside the highlighted contour line exceed the selected legal limit set by CPCB (India's Central Pollution Control Board).")

with tab4:
    st.markdown("#### Sound Meter Probe (Check Any Location)")
    st.caption("Move this virtual sound meter anywhere in the neighborhood to see how loud it is and how much sound gets absorbed.")
    
    probe_c1, probe_c2, probe_c3 = st.columns(3)
    with probe_c1:
        probe_x = st.slider("Position East-West X (meters)", 0.0, float(sim_current["city"].width), 150.0, step=5.0, help="Move the meter horizontally across the neighborhood.")
    with probe_c2:
        probe_y = st.slider("Position North-South Y (meters)", 0.0, float(sim_current["city"].height), 150.0, step=5.0, help="Move the meter vertically across the neighborhood.")
    with probe_c3:
        probe_z = st.slider("Meter Height above ground (meters)", 0.5, 20.0, 1.5, step=0.5, help="1.5m is ear height for a standing person; higher values test upper-floor balconies.")
        
    probe_res = evaluate_single_receiver(
        probe_x, probe_y, probe_z,
        city=sim_current["city"],
        sources=current_sources,
        ground_type=st.session_state["env_params"]["ground_type"],
        temp_c=st.session_state["env_params"]["temp_c"],
        rel_humidity=st.session_state["env_params"]["humidity"],
        green_buffer=st.session_state["env_params"]["green_buffer"]
    )
    
    res_c1, res_c2 = st.columns([1, 2])
    with res_c1:
        st.markdown(f"""
        <div class="glass-card" style="text-align:center; padding: 20px;">
            <div style="font-size:0.85rem; color:#94a3b8; text-transform:uppercase;">Loudness at this spot</div>
            <div style="font-size:3rem; font-weight:800; color:#38bdf8; font-family:'JetBrains Mono'; margin: 10px 0;">
                {probe_res['total_db']} <span style="font-size:1.2rem;">dB(A)</span>
            </div>
            <div style="font-size:0.85rem; color:#cbd5e1;">Spot at X={probe_x:.0f}m, Y={probe_y:.0f}m, Height={probe_z:.1f}m</div>
        </div>
        """, unsafe_allow_html=True)
        
    with res_c2:
        fig_breakdown = build_receiver_breakdown_chart(probe_res)
        st.plotly_chart(fig_breakdown, width="stretch", key="sim_fig_breakdown")
        
    if probe_res['total_db'] <= 55.0:
        spot_status = "Safe: Well within residential limits for comfortable conversation and rest."
    elif probe_res['total_db'] <= 65.0:
        spot_status = "A bit loud: Noticeable street noise; keep windows closed for quiet studying."
    else:
        spot_status = "Too loud: Exceeds safe residential levels; can cause irritation or headache over time."
    st.caption(f"**In simple words:** At this exact spot, the loudness is **{probe_res['total_db']} dB(A)** ({spot_status}).")

    with st.expander("Technical details (for students and experts)"):
        st.markdown("""
        **Sound Propagation Formula (ISO 9613-2):**
        $$L_{\\text{receiver}} = L_{\\text{source}} + D_c - (A_{\\text{div}} + A_{\\text{atm}} + A_{\\text{gr}} + A_{\\text{bar}} + A_{\\text{misc}})$$
        - **$A_{\\text{div}}$**: Geometric spreading loss ($-20 \\log_{10}(d) - 11$)
        - **$A_{\\text{atm}}$**: Atmospheric absorption ($\\alpha \\cdot d / 1000$)
        - **$A_{\\text{gr}}$**: Ground reflection / absorption factor
        - **$A_{\\text{bar}}$**: Maekawa diffraction barrier attenuation
        """)
        if probe_res["breakdown"]:
            st.markdown("##### Attenuation Breakdown Table")
            st.dataframe(pd.DataFrame(probe_res["breakdown"]), width="stretch")

with tab5:
    st.markdown("#### How Noise Fades with Distance (Distance Decay)")
    st.caption("See how sound drops naturally over distance, and how much a barrier wall cuts it down.")
    dd_c1, dd_c2 = st.columns(2)
    with dd_c1:
        decay_lw = st.slider("Source Sound Power (dB)", 75.0, 115.0, 95.0, step=1.0, help="How much sound energy is made at the machine or vehicle.")
    with dd_c2:
        decay_bar_h = st.slider("Sound Barrier Wall Height (meters)", 1.5, 7.0, 4.0, step=0.5, help="Height of the protective acoustic sound barrier wall.")
        
    fig_decay = build_distance_decay_plot(decay_lw, decay_bar_h, st.session_state["env_params"]["ground_type"])
    st.plotly_chart(fig_decay, width="stretch", key="sim_fig_decay")
    st.caption("**In simple words:** Every time you double your distance from a noise source (like stepping from 10m to 20m), the sound drops by about 6 dB(A). A solid barrier wall knocks off another 5 to 15 dB(A).")

    with st.expander("Technical details (for students and experts)"):
        st.markdown("""
        **Inverse-Square Geometric Attenuation:**
        $$A_{\\text{div}} = 20 \\log_{10}(d) + 11 \\quad \\text{dB}$$
        **Barrier Attenuation (Maekawa Approximation):**
        $$N = \\frac{2}{\\lambda} (A + B - d) = \\frac{2 f}{c} \\delta$$
        $$A_{\\text{bar}} = 10 \\log_{10}(3 + 20 N) \\quad (\\text{clipped to } 20\\text{ dB})$$
        """)
