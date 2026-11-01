"""
Application Utilities and Session State Helpers.
Manages persistent state across Streamlit pages, report exports, and formatting.
"""

from typing import Dict, Any, List, Optional
import streamlit as st
import pandas as pd
import numpy as np

from core.geometry import (
    create_residential_colony,
    create_dense_downtown,
    create_industrial_residential_mix,
    CityLayout,
    SoundBarrier
)
from core.sources import NoiseSource, discretize_road_to_sources
from core.propagation import simulate_grid

def init_session_state():
    """Initializes default application session state if not already set."""
    if "city_type" not in st.session_state:
        st.session_state["city_type"] = "Residential Colony"
        
    if "city" not in st.session_state:
        st.session_state["city"] = create_residential_colony()
        
    if "sources" not in st.session_state:
        # Default sources: Road traffic + 1 construction site + 1 commercial vehicle
        city = st.session_state["city"]
        road_srcs = discretize_road_to_sources("Arterial South Road", (0.0, 25.0), (300.0, 25.0), traffic_vol=1800, heavy_pct=15.0)
        custom_srcs = [
            NoiseSource("CS_1", "Excavator Worksite", 60.0, 75.0, 1.5, 104.0, "Industrial / Construction"),
            NoiseSource("TRK_1", "Delivery Truck Loading", 230.0, 75.0, 1.2, 95.0, "Traffic")
        ]
        st.session_state["sources"] = road_srcs + custom_srcs
        
    if "env_params" not in st.session_state:
        st.session_state["env_params"] = {
            "ground_type": "mixed",
            "temp_c": 25.0,
            "humidity": 60.0,
            "time_of_day": "Day",
            "grid_res": 80,
            "green_buffer": False
        }
        
    if "mitigation_params" not in st.session_state:
        st.session_state["mitigation_params"] = {
            "barrier_enabled": False,
            "barrier_x1": 10.0,
            "barrier_y1": 35.0,
            "barrier_x2": 290.0,
            "barrier_y2": 35.0,
            "barrier_height": 4.5,
            "traffic_reduction_pct": 0.0,
            "green_buffer_enabled": False
        }
        
    if "colorblind_mode" not in st.session_state:
        st.session_state["colorblind_mode"] = False
        
    # Auto-run baseline simulation if not present
    if "sim_baseline" not in st.session_state:
        with st.spinner("Initializing UrbanSound 3D Baseline Engine..."):
            sim_baseline = simulate_grid(
                city=st.session_state["city"],
                sources=st.session_state["sources"],
                grid_res=st.session_state["env_params"]["grid_res"],
                ground_type=st.session_state["env_params"]["ground_type"],
                temp_c=st.session_state["env_params"]["temp_c"],
                rel_humidity=st.session_state["env_params"]["humidity"],
                green_buffer=st.session_state["env_params"]["green_buffer"]
            )
            st.session_state["sim_baseline"] = sim_baseline
            st.session_state["sim_current"] = sim_baseline

def generate_html_report(
    sim_data: Dict[str, Any],
    building_df: pd.DataFrame,
    zone_type: str,
    cpcb_limit: float,
    baseline_sim: Optional[Dict[str, Any]] = None
) -> str:
    """Generates an executive HTML audit report for download."""
    L = sim_data["L_total"]
    max_db = float(np.max(L))
    mean_db = float(np.mean(L))
    min_db = float(np.min(L))
    
    total_pts = L.size
    violating_pts = int(np.sum(L > cpcb_limit))
    violation_pct = round((violating_pts / total_pts) * 100.0, 1)
    
    bld_total = len(building_df)
    bld_fail = int(np.sum(building_df["status"] == "FAIL")) if bld_total > 0 else 0
    bld_pass = bld_total - bld_fail
    
    # Delta comparison if baseline provided
    mitigation_text = ""
    if baseline_sim is not None:
        delta = float(np.mean(baseline_sim["L_total"]) - mean_db)
        mitigation_text = f"""
        <div class="card highlight">
            <h3>Mitigation Impact Analysis</h3>
            <p>Average noise reduction achieved: <b>+{delta:.1f} dB(A)</b></p>
            <p>Critical area violation reduced to: <b>{violation_pct}%</b></p>
        </div>
        """
        
    # Table rows
    table_rows = ""
    for _, row in building_df.iterrows():
        status_color = "#ef4444" if row["status"] == "FAIL" else "#10b981"
        table_rows += f"""
        <tr>
            <td><b>{row['building_name']}</b></td>
            <td>{row['zone_type']}</td>
            <td>{row['max_facade_db']} dB(A)</td>
            <td>{row['cpcb_limit_db']} dB(A)</td>
            <td style="color:{status_color}; font-weight:bold;">{row['status']}</td>
        </tr>
        """
        
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>UrbanSound 3D Environmental Noise Assessment Report</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0b0f19; color: #f1f5f9; padding: 30px; margin: 0; }}
            h1, h2, h3 {{ color: #38bdf8; }}
            .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 20px; margin-bottom: 20px; }}
            .highlight {{ border-left: 5px solid #10b981; background: #132238; }}
            .metrics {{ display: flex; gap: 20px; flex-wrap: wrap; margin-bottom: 20px; }}
            .metric-box {{ flex: 1; min-width: 140px; background: #0f172a; padding: 15px; border-radius: 8px; border: 1px solid #1e293b; text-align: center; }}
            .metric-box h4 {{ margin: 0 0 8px 0; color: #94a3b8; font-size: 13px; text-transform: uppercase; }}
            .metric-box div {{ font-size: 24px; font-weight: bold; color: #38bdf8; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #334155; font-size: 14px; }}
            th {{ background: #0f172a; color: #94a3b8; }}
            .disclaimer {{ font-size: 12px; color: #64748b; margin-top: 30px; border-top: 1px solid #1e293b; padding-top: 15px; }}
        </style>
    </head>
    <body>
        <h1>UrbanSound 3D: Acoustic Audit & Compliance Report</h1>
        <p>Project: <i>Simulation Framework for Noise Pollution Propagation Analysis in Urban Areas</i></p>
        <p>Standard: <b>CPCB India Noise Rules / ISO 9613-2 Framework</b> | Evaluation Zone: <b>{zone_type} ({cpcb_limit} dB limit)</b></p>
        
        <div class="metrics">
            <div class="metric-box">
                <h4>Peak Sound Level</h4>
                <div>{max_db:.1f} dB(A)</div>
            </div>
            <div class="metric-box">
                <h4>Spatial Mean Leq</h4>
                <div>{mean_db:.1f} dB(A)</div>
            </div>
            <div class="metric-box">
                <h4>Area Over CPCB Limit</h4>
                <div style="color: {'#ef4444' if violation_pct > 20 else '#10b981'};">{violation_pct}%</div>
            </div>
            <div class="metric-box">
                <h4>Building Pass Rate</h4>
                <div style="color: #38bdf8;">{bld_pass} / {bld_total}</div>
            </div>
        </div>
        
        {mitigation_text}
        
        <div class="card">
            <h2>Building Facade Compliance Inventory</h2>
            <table>
                <thead>
                    <tr>
                        <th>Building Name</th>
                        <th>Designated Zone</th>
                        <th>Max Facade SPL</th>
                        <th>CPCB Threshold</th>
                        <th>Compliance Status</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """
    return html
