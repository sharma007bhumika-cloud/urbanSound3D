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
from core.utils import init_session_state

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

# ----------------- SIDEBAR CONTROLS -----------------
with st.sidebar:
    st.markdown("### 🎛️ Simulation Parameters")
    
    # 1. City Selection
    st.markdown("#### 1. Urban Morphology")
    city_choice = st.selectbox(
        "Select City Layout",
        ["Residential Colony", "Dense Downtown", "Industrial + Residential Mix", "Custom (OpenStreetMap)"],
        index=["Residential Colony", "Dense Downtown", "Industrial + Residential Mix", "Custom (OpenStreetMap)"].index(
            st.session_state["city_type"] if st.session_state["city_type"] in ["Residential Colony", "Dense Downtown", "Industrial + Residential Mix"] else "Custom (OpenStreetMap)"
        ),
        help="Select built-in procedural urban grid or query OpenStreetMap."
    )
    
    if city_choice == "Custom (OpenStreetMap)":
        osm_query = st.text_input("City / Neighborhood Name", value="Connaught Place, New Delhi", help="Requires internet; automatically falls back if offline.")
        if st.button("Fetch OSM Data", key="btn_osm"):
            with st.spinner(f"Querying OpenStreetMap for {osm_query}..."):
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
            
    grid_res = st.slider("Spatial Grid Resolution", min_value=40, max_value=120, value=st.session_state["env_params"]["grid_res"], step=10, help="Grid density (e.g. 80 = 80x80 = 6,400 points). Higher values give smoother contours.")
    st.session_state["env_params"]["grid_res"] = grid_res

    st.markdown("---")
    
    # 2. Environmental Conditions
    st.markdown("#### 2. Environmental Physics")
    c1, c2 = st.columns(2)
    with c1:
        temp_c = st.slider("Temp (°C)", min_value=0.0, max_value=45.0, value=float(st.session_state["env_params"]["temp_c"]), step=1.0)
    with c2:
        humidity = st.slider("Humidity (%)", min_value=20.0, max_value=95.0, value=float(st.session_state["env_params"]["humidity"]), step=5.0)
    
    ground_type = st.selectbox(
        "Ground Absorption",
        ["mixed", "hard", "grass"],
        index=["mixed", "hard", "grass"].index(st.session_state["env_params"]["ground_type"]),
        help="Hard (asphalt/concrete) reflects acoustic energy; Grass absorbs high frequencies."
    )
    time_of_day = st.radio("Time of Day", ["Day", "Night"], horizontal=True)
    st.session_state["env_params"].update({
        "temp_c": temp_c, "humidity": humidity, "ground_type": ground_type, "time_of_day": time_of_day
    })
    
    alpha = calculate_atmospheric_alpha(temp_c, humidity)
    st.caption(f"⚡ Calculated Atmospheric Absorption: **{alpha:.2f} dB/km**")
    
    st.markdown("---")
    
    # 3. Mitigation Tools
    st.markdown("#### 3. Acoustic Mitigation Tools")
    barrier_enable = st.checkbox("Erect Sound Barrier Wall", value=st.session_state["mitigation_params"]["barrier_enabled"])
    b_height = 4.0
    if barrier_enable:
        b_height = st.slider("Barrier Height (m)", 2.0, 8.0, float(st.session_state["mitigation_params"]["barrier_height"]), step=0.5)
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
        
    traffic_reduction = st.slider("Traffic Reduction Policy (%)", 0, 75, int(st.session_state["mitigation_params"]["traffic_reduction_pct"]), step=5)
    st.session_state["mitigation_params"]["traffic_reduction_pct"] = traffic_reduction
    
    green_buffer = st.checkbox("Add Urban Green Buffer (Vegetation)", value=st.session_state["env_params"]["green_buffer"])
    st.session_state["env_params"]["green_buffer"] = green_buffer
    
    st.markdown("---")
    colorblind = st.toggle("Colorblind-Friendly Palette", value=st.session_state["colorblind_mode"])
    st.session_state["colorblind_mode"] = colorblind
    
    # Run Simulation Trigger
    run_sim = st.button("🚀 Run Live Acoustic Simulation", use_container_width=True)

# ----------------- PAGE HEADER -----------------
st.title("🏙️ UrbanSound 3D: Acoustic Simulation Studio")
st.caption("Interactive 3D ISO 9613-2 propagation modeling, ray diffraction building shadows, and spatial sound level calculation.")

# ----------------- NOISE SOURCES MANAGEMENT (EXPANDER) -----------------
with st.expander("🔊 Manage Active Noise Sources & Traffic Streams", expanded=False):
    s_col1, s_col2 = st.columns([2, 1])
    with s_col1:
        st.markdown("##### Current Noise Sources in Scenario")
        src_table_data = []
        for s in st.session_state["sources"]:
            src_table_data.append({
                "ID": s.sid, "Name": s.name, "Type": s.stype,
                "X (m)": round(s.x, 1), "Y (m)": round(s.y, 1),
                "Power Lw (dB)": s.lw, "Active": s.active
            })
        st.dataframe(pd.DataFrame(src_table_data), use_container_width=True, height=180)
        
    with s_col2:
        st.markdown("##### Add New Point Source")
        preset_name = st.selectbox("Select Preset", list(SOURCE_PRESETS.keys()))
        preset_info = SOURCE_PRESETS[preset_name]
        new_x = st.number_input("Source X (m)", min_value=0.0, max_value=300.0, value=150.0, step=10.0)
        new_y = st.number_input("Source Y (m)", min_value=0.0, max_value=300.0, value=150.0, step=10.0)
        new_lw = st.slider("Sound Power Lw dB(A)", 70.0, 120.0, float(preset_info["lw"]), step=1.0)
        
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
    with st.spinner("Computing Vectorized ISO 9613-2 Propagation Engine..."):
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
        <div class="kpi-title">Peak Sound Level</div>
        <div class="kpi-value">{max_spl:.1f} <span style="font-size:1.1rem; color:#94a3b8;">dB(A)</span></div>
        <div class="kpi-sub">Near highest active source</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-title">Spatial Mean Leq</div>
        <div class="kpi-value">{mean_spl:.1f} <span style="font-size:1.1rem; color:#94a3b8;">dB(A)</span></div>
        <div class="kpi-sub">Area-averaged exposure</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-title">Area Above 65 dB(A)</div>
        <div class="kpi-value" style="color: {'#ef4444' if pct_loud > 25 else '#10b981'};">{pct_loud:.1f}%</div>
        <div class="kpi-sub">Critical acoustic impact zone</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-title">Simulated Grid Points</div>
        <div class="kpi-value" style="color: #38bdf8;">{L_grid.size:,}</div>
        <div class="kpi-sub">{sim_current['grid_res']}x{sim_current['grid_res']} Vectorized Nodes</div>
    </div>
</div>
"""
st.markdown(kpi_html, unsafe_allow_html=True)

# ----------------- MAIN INTERACTIVE TABS -----------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏙️ 3D City Soundscape",
    "⛰️ 3D Noise Surface (Z=dB)",
    "🗺️ 2D Acoustic Heatmap",
    "🎯 Receiver Probe & Term Breakdown",
    "📉 Distance Decay Curve"
])

with tab1:
    st.markdown("#### Interactive 3D Urban Soundscape")
    st.caption("Rotate (click & drag), zoom (scroll), and pan (right-click) to explore acoustic fields interacting with buildings and barriers.")
    
    layer_col1, layer_col2, layer_col3, layer_col4 = st.columns(4)
    with layer_col1:
        toggle_bld = st.checkbox("Show 3D Buildings", value=True)
    with layer_col2:
        toggle_surf = st.checkbox("Show Ground Noise Field", value=True)
    with layer_col3:
        toggle_src = st.checkbox("Show Noise Sources", value=True)
    with layer_col4:
        toggle_bar = st.checkbox("Show Barrier Walls", value=True)
        
    fig_3d = build_3d_city_scene(
        sim_current,
        show_buildings=toggle_bld,
        show_noise_surface=toggle_surf,
        show_sources=toggle_src,
        show_barriers=toggle_bar,
        colorblind_mode=st.session_state["colorblind_mode"]
    )
    st.plotly_chart(fig_3d, use_container_width=True, config={"displayModeBar": True}, key="sim_fig_3d")

with tab2:
    st.markdown("#### 3D Acoustic Topography (Elevation = Decibel Level)")
    st.caption("Visualizes sound intensity as virtual elevation peaks, illustrating acoustic shadow canyons cast behind shielding buildings.")
    fig_surface = build_3d_noise_surface_plot(sim_current, colorblind_mode=st.session_state["colorblind_mode"])
    st.plotly_chart(fig_surface, use_container_width=True, key="sim_fig_surface")

with tab3:
    st.markdown("#### 2D Top-Down Acoustic Heatmap & Zone Outlines")
    st.caption("Accurate plan-view contour map with building footprint overlays, barrier locations, and source markers.")
    cpcb_thresh = st.selectbox("Highlight Regulatory Limit Contour", [None, 45.0, 50.0, 55.0, 65.0, 75.0], index=3, format_func=lambda x: f"None" if x is None else f"CPCB {x} dB(A)")
    fig_2d = build_2d_heatmap_plot(sim_current, cpcb_limit=cpcb_thresh, colorblind_mode=st.session_state["colorblind_mode"])
    st.plotly_chart(fig_2d, use_container_width=True, key="sim_fig_2d")

with tab4:
    st.markdown("#### Acoustic Receiver Virtual Probe")
    st.caption("Position a virtual calibrated sound level meter anywhere in the city to inspect exact physical attenuation terms.")
    
    probe_c1, probe_c2, probe_c3 = st.columns(3)
    with probe_c1:
        probe_x = st.slider("Probe X Position (m)", 0.0, float(sim_current["city"].width), 150.0, step=5.0)
    with probe_c2:
        probe_y = st.slider("Probe Y Position (m)", 0.0, float(sim_current["city"].height), 150.0, step=5.0)
    with probe_c3:
        probe_z = st.slider("Receiver Height Z (m)", 0.5, 20.0, 1.5, step=0.5, help="1.5m corresponds to standard human ear level; higher values represent balcony/upper floor exposures.")
        
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
            <div style="font-size:0.85rem; color:#94a3b8; text-transform:uppercase;">Total Received Sound Level</div>
            <div style="font-size:3rem; font-weight:800; color:#38bdf8; font-family:'JetBrains Mono'; margin: 10px 0;">
                {probe_res['total_db']} <span style="font-size:1.2rem;">dB(A)</span>
            </div>
            <div style="font-size:0.85rem; color:#cbd5e1;">Probe at ({probe_x:.1f}m, {probe_y:.1f}m, {probe_z:.1f}m)</div>
        </div>
        """, unsafe_allow_html=True)
        
    with res_c2:
        fig_breakdown = build_receiver_breakdown_chart(probe_res)
        st.plotly_chart(fig_breakdown, use_container_width=True, key="sim_fig_breakdown")
        
    st.markdown("##### Detailed Attenuation Breakdown Table")
    if probe_res["breakdown"]:
        st.dataframe(pd.DataFrame(probe_res["breakdown"]), use_container_width=True)

with tab5:
    st.markdown("#### Distance Decay Analysis")
    st.caption("Observe the inverse-square geometric drop (-6 dB per doubling) alongside atmospheric absorption and barrier attenuation.")
    dd_c1, dd_c2 = st.columns(2)
    with dd_c1:
        decay_lw = st.slider("Source Sound Power Lw (dB)", 75.0, 115.0, 95.0, step=1.0)
    with dd_c2:
        decay_bar_h = st.slider("Sound Barrier Height (m)", 1.5, 7.0, 4.0, step=0.5)
        
    fig_decay = build_distance_decay_plot(decay_lw, decay_bar_h, st.session_state["env_params"]["ground_type"])
    st.plotly_chart(fig_decay, use_container_width=True, key="sim_fig_decay")
