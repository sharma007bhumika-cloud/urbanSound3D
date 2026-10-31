"""
UrbanSound 3D - Results, Compliance Auditing & Scenario Comparison.
Comparative analysis of baseline vs mitigated scenarios, CPCB/WHO regulatory compliance checks,
per-building facade noise exposure, diurnal 24-hr profiles, and report export.
"""

import os
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from core.standards import CPCB_STANDARDS, WHO_GUIDELINES, get_cpcb_limit
from core.sources import get_diurnal_traffic_factors
from core.propagation import (
    simulate_grid,
    evaluate_facade_exposures
)
from core.visualization import (
    build_2d_heatmap_plot,
    build_3d_city_scene,
    build_scenario_difference_plot,
    build_diurnal_24hr_chart,
    DARK_LAYOUT_TEMPLATE
)
from core.utils import init_session_state, generate_html_report

st.set_page_config(
    page_title="UrbanSound 3D - Results & Scenario Compare",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load CSS
css_path = os.path.join(os.path.dirname(__file__), "..", "assets", "style.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

init_session_state()

st.title("📊 Acoustic Analysis, Compliance & Scenario Studio")
st.caption("Quantitative audit of spatial noise distribution, regulatory threshold compliance, and mitigation effectiveness.")

# Check if simulation data exists
if "sim_current" not in st.session_state:
    st.info("No active simulation found. Please initialize the scenario in the Simulator.")
    st.stop()

sim_current = st.session_state["sim_current"]
sim_baseline = st.session_state.get("sim_baseline", sim_current)
city = sim_current["city"]

# ----------------- COMPLIANCE AUDIT CONTROLS -----------------
with st.sidebar:
    st.markdown("### ⚖️ Regulatory Standard")
    zone_choice = st.selectbox(
        "Designated Zoning Type",
        list(CPCB_STANDARDS.keys()),
        index=2, # Residential Area by default
        help="Central Pollution Control Board (CPCB) India ambient noise standards. Verify values against official CPCB notification."
    )
    time_setting = st.radio("Standard Time of Day", ["Day (06:00 - 22:00)", "Night (22:00 - 06:00)"])
    tod_key = "day" if "Day" in time_setting else "night"
    cpcb_threshold = get_cpcb_limit(zone_choice, tod_key)
    
    st.markdown(f"""
    <div class="glass-card" style="padding:14px; margin-top:10px;">
        <div style="font-size:0.8rem; color:#94a3b8;">CPCB REGULATORY LIMIT</div>
        <div style="font-size:1.8rem; font-weight:800; color:#38bdf8; font-family:'JetBrains Mono';">{cpcb_threshold} dB(A)</div>
        <div style="font-size:0.75rem; color:#64748b;">{CPCB_STANDARDS[zone_choice]['description']}</div>
    </div>
    """, unsafe_allow_html=True)

# ----------------- COMPUTE KEY COMPLIANCE METRICS -----------------
L_curr = sim_current["L_total"]
max_db = float(np.max(L_curr))
mean_db = float(np.mean(L_curr))
total_pts = L_curr.size
violating_pts = int(np.sum(L_curr > cpcb_threshold))
violation_pct = (violating_pts / total_pts) * 100.0

# Per-building facade evaluation
facade_data = evaluate_facade_exposures(
    city=city,
    sources=sim_current["sources"],
    ground_type=st.session_state["env_params"]["ground_type"],
    temp_c=st.session_state["env_params"]["temp_c"],
    rel_humidity=st.session_state["env_params"]["humidity"]
)
bld_df = pd.DataFrame(facade_data)
bld_fails = int(np.sum(bld_df["status"] == "FAIL")) if not bld_df.empty else 0
bld_total = len(bld_df)

# Top KPI row
kpi_html = f"""
<div class="kpi-container">
    <div class="kpi-card">
        <div class="kpi-title">Max Observed Level</div>
        <div class="kpi-value">{max_db:.1f} <span style="font-size:1rem; color:#94a3b8;">dB(A)</span></div>
        <div class="kpi-sub">CPCB Limit: {cpcb_threshold} dB(A)</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-title">Spatial Mean Leq</div>
        <div class="kpi-value">{mean_db:.1f} <span style="font-size:1rem; color:#94a3b8;">dB(A)</span></div>
        <div class="kpi-sub">Across entire 300x300m sector</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-title">Area in Non-Compliance</div>
        <div class="kpi-value" style="color: {'#ef4444' if violation_pct > 25 else '#10b981'};">{violation_pct:.1f}%</div>
        <div class="kpi-sub">{violating_pts:,} of {total_pts:,} grid cells</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-title">Buildings in Violation</div>
        <div class="kpi-value" style="color: {'#ef4444' if bld_fails > 0 else '#10b981'};">{bld_fails} <span style="font-size:1rem; color:#94a3b8;">/ {bld_total}</span></div>
        <div class="kpi-sub">Exceeding facade threshold</div>
    </div>
</div>
"""
st.markdown(kpi_html, unsafe_allow_html=True)

# ----------------- TABS FOR RESULTS & COMPARISON -----------------
res_tab1, res_tab2, res_tab3, res_tab4, res_tab5 = st.tabs([
    "⚖️ Regulatory Compliance & Facades",
    "🔄 Before vs After Mitigation",
    "📈 Statistical & Distribution Curves",
    "🌙 Day vs Night Diurnal Profiles",
    "📥 Export Audit Reports"
])

with res_tab1:
    st.markdown("#### Urban Zoning Compliance Assessment")
    st.caption(f"Spatial distribution of sound levels audited against the **{zone_choice}** limit of **{cpcb_threshold} dB(A)**.")
    
    col_map, col_chart = st.columns([3, 2])
    with col_map:
        fig_comp_2d = build_2d_heatmap_plot(sim_current, cpcb_limit=cpcb_threshold, colorblind_mode=st.session_state["colorblind_mode"])
        st.plotly_chart(fig_comp_2d, use_container_width=True, key="res_comp_2d")
        
    with col_chart:
        st.markdown("##### Zone Compliance Summary")
        comp_df = pd.DataFrame([
            {"Status": "Compliant Area", "Percentage": round(100.0 - violation_pct, 1), "Color": "#10b981"},
            {"Status": "Non-Compliant Violation", "Percentage": round(violation_pct, 1), "Color": "#ef4444"}
        ])
        fig_donut = go.Figure(data=[go.Pie(
            labels=comp_df["Status"],
            values=comp_df["Percentage"],
            hole=0.55,
            marker=dict(colors=["#10b981", "#ef4444"]),
            textinfo="label+percent"
        )])
        fig_donut.update_layout(
            template="plotly_dark",
            paper_bgcolor=DARK_LAYOUT_TEMPLATE["paper_bgcolor"],
            font=DARK_LAYOUT_TEMPLATE["font"],
            margin=dict(l=10, r=10, t=10, b=10),
            showlegend=False
        )
        st.plotly_chart(fig_donut, use_container_width=True, key="res_donut")
        
        # WHO Comparison Card
        st.markdown(f"""
        <div class="glass-card" style="padding:14px;">
            <div style="font-weight:700; color:#38bdf8; margin-bottom:6px;">WHO Environmental Guideline Check</div>
            <div style="font-size:0.85rem; color:#cbd5e1;">WHO recommends road traffic noise below <b>53 dB Lden</b> to prevent adverse physiological and cognitive impacts.</div>
            <div style="font-size:0.85rem; margin-top:8px; color:{'#ef4444' if mean_db > 53 else '#10b981'}; font-weight:700;">
                Current Sector Mean: {mean_db:.1f} dB(A) ({'EXCEEDS WHO GUIDELINE' if mean_db > 53 else 'MEETS WHO GUIDELINE'})
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("---")
    st.markdown("#### Building Facade Exposure Table")
    st.caption("Acoustic impact evaluated across perimeter receivers at 1.5m height. Buildings sorted by maximum facade exposure.")
    
    if not bld_df.empty:
        # Style the dataframe
        def highlight_status(val):
            return "color: #ef4444; font-weight: bold;" if val == "FAIL" else "color: #10b981; font-weight: bold;"
        styled_df = bld_df.sort_values(by="max_facade_db", ascending=False).reset_index(drop=True)
        st.dataframe(styled_df, use_container_width=True)

with res_tab2:
    st.markdown("#### Before vs After Mitigation Scenario Comparison")
    st.caption("Compare baseline conditions with implemented mitigation measures (sound barrier walls, traffic reduction, green buffers).")
    
    # Delta calculations
    mean_baseline = float(np.mean(sim_baseline["L_total"]))
    mean_mitigated = float(np.mean(sim_current["L_total"]))
    delta_mean = mean_baseline - mean_mitigated
    
    viol_base = float(np.mean(sim_baseline["L_total"] > cpcb_threshold) * 100.0)
    viol_mit = float(np.mean(sim_current["L_total"] > cpcb_threshold) * 100.0)
    delta_viol = viol_base - viol_mit
    
    # Summary Callout
    delta_color = "#10b981" if delta_mean >= 1.0 else "#94a3b8"
    st.markdown(f"""
    <div class="glass-card" style="border-left: 5px solid {delta_color};">
        <h4 style="margin:0 0 10px 0; color:#38bdf8;">Mitigation Impact Summary</h4>
        <div style="display:flex; gap:30px; flex-wrap:wrap;">
            <div>
                <span style="font-size:0.85rem; color:#94a3b8;">Average Sound Reduction:</span><br>
                <b style="font-size:1.6rem; color:{delta_color}; font-family:'JetBrains Mono';">+{delta_mean:.1f} dB(A)</b>
            </div>
            <div>
                <span style="font-size:0.85rem; color:#94a3b8;">Reduction in Area Violations:</span><br>
                <b style="font-size:1.6rem; color:{delta_color}; font-family:'JetBrains Mono';">-{delta_viol:.1f}%</b>
            </div>
            <div>
                <span style="font-size:0.85rem; color:#94a3b8;">Active Barrier Status:</span><br>
                <b style="font-size:1.1rem; color:#f8fafc;">{'4.5m Acoustic Wall Erected' if st.session_state['mitigation_params']['barrier_enabled'] else 'No Barrier'}</b>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Side-by-side or Difference map
    comp_mode = st.radio("Comparison Visualization View", ["Side-by-Side 3D Views", "Spatial Noise Reduction Heatmap (Baseline - Mitigated)"], horizontal=True)
    
    if comp_mode == "Side-by-Side 3D Views":
        col_b, col_m = st.columns(2)
        with col_b:
            st.markdown("##### 1. Baseline Scenario (Unmitigated)")
            fig_b3d = build_3d_city_scene(sim_baseline, colorblind_mode=st.session_state["colorblind_mode"])
            st.plotly_chart(fig_b3d, use_container_width=True, key="res_b3d")
        with col_m:
            st.markdown("##### 2. Mitigated Scenario (With Interventions)")
            fig_m3d = build_3d_city_scene(sim_current, colorblind_mode=st.session_state["colorblind_mode"])
            st.plotly_chart(fig_m3d, use_container_width=True, key="res_m3d")
    else:
        st.markdown("##### Spatial Decibel Reduction Heatmap")
        st.caption("Positive green-yellow regions indicate decibels mitigated by barriers or traffic policies.")
        fig_diff = build_scenario_difference_plot(sim_baseline, sim_current)
        st.plotly_chart(fig_diff, use_container_width=True, key="res_diff")
        
    # Auto-generated textual engineering conclusion
    st.markdown("##### 📝 Automated Engineering Assessment")
    conclusion_text = (
        f"Installation of the simulated mitigation measures achieved an average acoustic reduction of **{delta_mean:.1f} dB(A)** "
        f"across the study area. Area non-compliance with the {zone_choice} standard shifted from **{viol_base:.1f}%** down to **{viol_mit:.1f}%**. "
        f"Screening from the barrier wall notably protects lower-floor residential facades behind the transit corridor, while distance and ground absorption provide supplemental natural attenuation."
    )
    st.info(conclusion_text)

with res_tab3:
    st.markdown("#### Statistical Noise Distributions")
    st.caption("Analyze cumulative exposure probability and decibel frequency spectrum.")
    
    col_hist, col_cdf = st.columns(2)
    with col_hist:
        flat_levels = L_curr.flatten()
        fig_hist = go.Figure()
        fig_hist.add_trace(go.Histogram(
            x=flat_levels,
            nbinsx=35,
            marker_color="#38bdf8",
            opacity=0.8,
            name="Grid Distribution"
        ))
        fig_hist.add_vline(x=cpcb_threshold, line_width=2.5, line_dash="dash", line_color="#ef4444", annotation_text=f"CPCB Limit ({cpcb_threshold} dB)")
        fig_hist.update_layout(
            template="plotly_dark",
            paper_bgcolor=DARK_LAYOUT_TEMPLATE["paper_bgcolor"],
            plot_bgcolor=DARK_LAYOUT_TEMPLATE["plot_bgcolor"],
            font=DARK_LAYOUT_TEMPLATE["font"],
            title="Histogram of Decibel Levels Across Grid",
            xaxis=dict(title="Sound Level dB(A)"),
            yaxis=dict(title="Count of Grid Nodes")
        )
        st.plotly_chart(fig_hist, use_container_width=True, key="res_hist")
        
    with col_cdf:
        sorted_levels = np.sort(flat_levels)
        cdf = np.arange(1, len(sorted_levels) + 1) / len(sorted_levels) * 100.0
        
        fig_cdf = go.Figure()
        fig_cdf.add_trace(go.Scatter(
            x=sorted_levels,
            y=cdf,
            mode="lines",
            line=dict(color="#10b981", width=3),
            name="Cumulative Exposure CDF"
        ))
        fig_cdf.add_vline(x=cpcb_threshold, line_width=2.5, line_dash="dash", line_color="#ef4444")
        fig_cdf.update_layout(
            template="plotly_dark",
            paper_bgcolor=DARK_LAYOUT_TEMPLATE["paper_bgcolor"],
            plot_bgcolor=DARK_LAYOUT_TEMPLATE["plot_bgcolor"],
            font=DARK_LAYOUT_TEMPLATE["font"],
            title="Cumulative Distribution Function (% Area Below X dB)",
            xaxis=dict(title="Sound Level dB(A)"),
            yaxis=dict(title="% of Area Below Level", range=[0, 105])
        )
        st.plotly_chart(fig_cdf, use_container_width=True, key="res_cdf")

with res_tab4:
    st.markdown("#### 🌙 Day vs Night & 24-Hour Diurnal Dynamics")
    st.caption("Temporal acoustic progression, diurnal rush-hour cycles, composite Lden indicators, and nocturnal sleep guidelines.")
    
    # 24-Hour profile calculations
    hours = np.arange(24)
    factors = get_diurnal_traffic_factors()
    night_mean_db = mean_db - 6.0  # standard ~6-7 dB drop at night (20% traffic volume)
    
    # Lden indicator calculation
    # Day (07-19, 12h), Evening (19-23, 4h), Night (23-07, 8h)
    hourly_spl = mean_db + 10.0 * np.log10(np.maximum(0.08, factors))
    eve_spl = float(10.0 * np.log10(np.mean(10.0 ** (hourly_spl[[19, 20, 21, 22]] / 10.0))))
    
    e_day = (12.0 / 24.0) * (10.0 ** (mean_db / 10.0))
    e_eve = (4.0 / 24.0) * (10.0 ** ((eve_spl + 5.0) / 10.0))
    e_ngt = (8.0 / 24.0) * (10.0 ** ((night_mean_db + 10.0) / 10.0))
    l_den = float(10.0 * np.log10(e_day + e_eve + e_ngt))
    
    d_c1, d_c2, d_c3, d_c4 = st.columns(4)
    with d_c1:
        st.markdown(f"""
        <div style="background:rgba(30,41,59,0.7); border:1px solid rgba(56,189,248,0.3); border-radius:10px; padding:12px; text-align:center;">
            <div style="font-size:0.8rem; color:#94a3b8; text-transform:uppercase;">Daytime Leq (06-22h)</div>
            <div style="font-size:1.8rem; font-weight:800; color:#f59e0b; font-family:'JetBrains Mono';">{mean_db:.1f} dB</div>
            <div style="font-size:0.75rem; color:#cbd5e1;">CPCB Standard: {get_cpcb_limit(zone_choice, 'day')} dB</div>
        </div>
        """, unsafe_allow_html=True)
    with d_c2:
        st.markdown(f"""
        <div style="background:rgba(30,41,59,0.7); border:1px solid rgba(56,189,248,0.3); border-radius:10px; padding:12px; text-align:center;">
            <div style="font-size:0.8rem; color:#94a3b8; text-transform:uppercase;">Nighttime Leq (22-06h)</div>
            <div style="font-size:1.8rem; font-weight:800; color:#10b981; font-family:'JetBrains Mono';">{night_mean_db:.1f} dB</div>
            <div style="font-size:0.75rem; color:#cbd5e1;">CPCB Standard: {get_cpcb_limit(zone_choice, 'night')} dB</div>
        </div>
        """, unsafe_allow_html=True)
    with d_c3:
        st.markdown(f"""
        <div style="background:rgba(30,41,59,0.7); border:1px solid rgba(56,189,248,0.3); border-radius:10px; padding:12px; text-align:center;">
            <div style="font-size:0.8rem; color:#94a3b8; text-transform:uppercase;">Composite Indicator Lden</div>
            <div style="font-size:1.8rem; font-weight:800; color:#38bdf8; font-family:'JetBrains Mono';">{l_den:.1f} dB</div>
            <div style="font-size:0.75rem; color:#cbd5e1;">Includes +5dB (Eve) & +10dB (Night)</div>
        </div>
        """, unsafe_allow_html=True)
    with d_c4:
        drop_val = mean_db - night_mean_db
        st.markdown(f"""
        <div style="background:rgba(30,41,59,0.7); border:1px solid rgba(56,189,248,0.3); border-radius:10px; padding:12px; text-align:center;">
            <div style="font-size:0.8rem; color:#94a3b8; text-transform:uppercase;">Nocturnal Quiet Drop</div>
            <div style="font-size:1.8rem; font-weight:800; color:#34d399; font-family:'JetBrains Mono';">-{drop_val:.1f} dB</div>
            <div style="font-size:0.75rem; color:#cbd5e1;">Natural night traffic attenuation</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("---")
    
    # 24-Hour Diurnal Chart with Day and Night step thresholds
    cpcb_day = get_cpcb_limit(zone_choice, 'day')
    cpcb_night = get_cpcb_limit(zone_choice, 'night')
    cpcb_steps = [cpcb_night if (h < 6 or h >= 22) else cpcb_day for h in hours]
    who_sleep = [40.0 for _ in hours]
    
    fig_diurnal = go.Figure()
    fig_diurnal.add_vrect(x0=0, x1=6, fillcolor="rgba(30, 27, 75, 0.45)", layer="below", line_width=0, annotation_text="Night Sleep Window", annotation_position="top left")
    fig_diurnal.add_vrect(x0=22, x1=23, fillcolor="rgba(30, 27, 75, 0.45)", layer="below", line_width=0)
    
    fig_diurnal.add_trace(go.Scatter(
        x=hours, y=hourly_spl, mode="lines+markers",
        name="Estimated Hourly Area Leq",
        line=dict(color="#38bdf8", width=3),
        marker=dict(size=6, color="#0284c7")
    ))
    fig_diurnal.add_trace(go.Scatter(
        x=hours, y=cpcb_steps, mode="lines",
        name=f"CPCB {zone_choice} Standard ({cpcb_day} dB Day / {cpcb_night} dB Night)",
        line=dict(color="#ef4444", width=2.5, dash="dash")
    ))
    fig_diurnal.add_trace(go.Scatter(
        x=hours, y=who_sleep, mode="lines",
        name="WHO Restful Sleep Guideline (40 dB)",
        line=dict(color="#10b981", width=2, dash="dot")
    ))
    fig_diurnal.update_layout(
        template="plotly_dark",
        paper_bgcolor=DARK_LAYOUT_TEMPLATE["paper_bgcolor"],
        plot_bgcolor=DARK_LAYOUT_TEMPLATE["plot_bgcolor"],
        font=DARK_LAYOUT_TEMPLATE["font"],
        title="24-Hour Diurnal Exposure vs CPCB Day/Night Limits & WHO Restful Sleep Standard",
        xaxis=dict(title="Hour of Day (00:00 - 23:00)", tickmode="linear", dtick=2),
        yaxis=dict(title="Sound Level dB(A)", range=[30, max(80, max_curr + 2)]),
        legend=dict(orientation="h", y=1.12, x=0.05)
    )
    st.plotly_chart(fig_diurnal, use_container_width=True, key="res_diurnal")
    
    # Interactive hour inspector slider
    st.markdown("##### 🕒 Hourly Diurnal Inspector")
    ins_hour = st.slider("Select Time of Day to Inspect", min_value=0, max_value=23, value=8, step=1, key="slider_ins_hour")
    traffic_frac = factors[ins_hour] * 100.0
    hour_val = hourly_spl[ins_hour]
    h_limit = cpcb_night if (ins_hour < 6 or ins_hour >= 22) else cpcb_day
    h_status = "COMPLIANT" if hour_val <= h_limit else "EXCEEDANCE"
    st.info(
        f"**{ins_hour:02d}:00 Clock Time:** Traffic volume is at **{traffic_frac:.0f}%** of daytime peak. "
        f"Estimated area sound level is **{hour_val:.1f} dB(A)** against regulatory limit of **{h_limit} dB(A)** "
        f"({h_status})."
    )

with res_tab5:
    st.markdown("#### Export Audit & Simulation Reports")
    st.caption("Download simulation data, facade records, and comprehensive HTML environmental compliance documentation.")
    
    exp_c1, exp_c2, exp_c3 = st.columns(3)
    with exp_c1:
        st.markdown("##### 1. Full Audit Report")
        html_report = generate_html_report(
            sim_data=sim_current,
            building_df=bld_df,
            zone_type=zone_choice,
            cpcb_limit=cpcb_threshold,
            baseline_sim=sim_baseline if sim_baseline is not sim_current else None
        )
        st.download_button(
            label="📄 Download HTML Audit Report",
            data=html_report,
            file_name="UrbanSound3D_Noise_Audit_Report.html",
            mime="text/html",
            use_container_width=True
        )
        
    with exp_c2:
        st.markdown("##### 2. Building Facade CSV")
        if not bld_df.empty:
            csv_bld = bld_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📊 Download Facade CSV",
                data=csv_bld,
                file_name="UrbanSound3D_Facade_Compliance.csv",
                mime="text/csv",
                use_container_width=True
            )
            
    with exp_c3:
        st.markdown("##### 3. Grid Coordinates & SPL CSV")
        grid_df = pd.DataFrame({
            "X_m": sim_current["X"].flatten(),
            "Y_m": sim_current["Y"].flatten(),
            "SoundLevel_dBA": sim_current["L_total"].flatten()
        })
        csv_grid = grid_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="🗺️ Download Grid SPL CSV",
            data=csv_grid,
            file_name="UrbanSound3D_Grid_NoiseField.csv",
            mime="text/csv",
            use_container_width=True
        )
