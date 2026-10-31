"""
Acoustic and Spatial Visualizations powered by Plotly.
Includes 3D city scene with Mesh3d extruded buildings, 3D noise surfaces, 2D top-down heatmaps,
attenuation waterfall bar charts, distance decay curves, and scenario comparison maps.
"""

from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import plotly.graph_objects as go
from shapely.geometry import Polygon

from core.geometry import CityLayout, Building, SoundBarrier
from core.sources import NoiseSource
from core.standards import CPCB_STANDARDS

# Dark aesthetic color palettes
PALETTE_STANDARD = [
    [0.0, "rgb(39, 174, 96)"],    # Quiet green (< 45 dB)
    [0.3, "rgb(46, 204, 113)"],
    [0.45, "rgb(241, 196, 15)"],  # Moderate yellow (55 dB)
    [0.6, "rgb(230, 126, 34)"],   # Noticeable orange (65 dB)
    [0.75, "rgb(231, 76, 60)"],   # Loud red (75 dB)
    [1.0, "rgb(142, 68, 173)"]    # Severe purple (> 85 dB)
]

# Colorblind friendly alternative palette (Viridis or Plasma-based)
PALETTE_COLORBLIND = [
    [0.0, "rgb(68, 1, 84)"],
    [0.25, "rgb(59, 82, 139)"],
    [0.5, "rgb(33, 145, 140)"],
    [0.75, "rgb(94, 201, 98)"],
    [1.0, "rgb(253, 231, 37)"]
]

DARK_LAYOUT_TEMPLATE = dict(
    paper_bgcolor="rgba(15, 23, 42, 0.95)",
    plot_bgcolor="rgba(15, 23, 42, 0.95)",
    font=dict(family="Inter, Roboto, sans-serif", color="#e2e8f0"),
    margin=dict(l=20, r=20, t=40, b=20)
)

def building_to_mesh3d(building: Building) -> Dict[str, Any]:
    """
    Extrudes a 2D building footprint polygon into 3D vertices and triangular faces for go.Mesh3d.
    Supports arbitrary convex/concave polygons.
    """
    coords = list(building.polygon.exterior.coords)[:-1]  # drop duplicate closing vertex
    n = len(coords)
    if n < 3:
        return {}
        
    h = building.height
    
    # Vertices: 0..n-1 are ground (z=0), n..2n-1 are roof (z=h)
    x = [p[0] for p in coords] + [p[0] for p in coords]
    y = [p[1] for p in coords] + [p[1] for p in coords]
    z = [0.0] * n + [h] * n
    
    i_faces = []
    j_faces = []
    k_faces = []
    
    # Vertical side walls: each edge (k, k+1) forms 2 triangles
    for k in range(n):
        nxt = (k + 1) % n
        # Triangle 1: ground_k, ground_nxt, roof_k
        i_faces.append(k)
        j_faces.append(nxt)
        k_faces.append(k + n)
        
        # Triangle 2: ground_nxt, roof_nxt, roof_k
        i_faces.append(nxt)
        j_faces.append(nxt + n)
        k_faces.append(k + n)
        
    # Roof triangulation (simple fan triangulation from vertex 0)
    for k in range(1, n - 1):
        i_faces.append(n)
        j_faces.append(n + k)
        k_faces.append(n + k + 1)
        
    return {
        "x": x, "y": y, "z": z,
        "i": i_faces, "j": j_faces, "k": k_faces
    }

def barrier_to_mesh3d(barrier: SoundBarrier) -> Dict[str, Any]:
    """Creates a thin 3D wall mesh for a sound barrier."""
    x1, y1, x2, y2, h = barrier.x1, barrier.y1, barrier.x2, barrier.y2, barrier.height
    # Create a small perpendicular offset for visual thickness (0.6m)
    dx = x2 - x1
    dy = y2 - y1
    L = np.hypot(dx, dy) + 1e-6
    nx = -dy / L * 0.4
    ny = dx / L * 0.4
    
    p1 = (x1 - nx, y1 - ny)
    p2 = (x2 - nx, y2 - ny)
    p3 = (x2 + nx, y2 + ny)
    p4 = (x1 + nx, y1 + ny)
    coords = [p1, p2, p3, p4]
    
    poly = Polygon(coords)
    dummy_bld = Building("barrier", barrier.name, poly, h, "Barrier")
    return building_to_mesh3d(dummy_bld)


def build_3d_city_scene(
    sim_data: Dict[str, Any],
    show_buildings: bool = True,
    show_noise_surface: bool = True,
    show_sources: bool = True,
    show_barriers: bool = True,
    colorblind_mode: bool = False
) -> go.Figure:
    """
    Constructs the interactive 3D Urban Soundscape Scene.
    Combines go.Mesh3d architectural blocks, noise ground surface, acoustic sources, and barriers.
    """
    fig = go.Figure()
    city: CityLayout = sim_data["city"]
    X = sim_data["X"]
    Y = sim_data["Y"]
    L_total = sim_data["L_total"]
    colorscale = PALETTE_COLORBLIND if colorblind_mode else PALETTE_STANDARD
    
    # 1. Ground Noise Heat Surface
    if show_noise_surface:
        # Ground plane placed at z = 0.2m so it's clearly visible
        z_plane = np.full_like(L_total, 0.2)
        fig.add_trace(go.Surface(
            x=X,
            y=Y,
            z=z_plane,
            surfacecolor=L_total,
            colorscale=colorscale,
            cmin=35.0,
            cmax=85.0,
            colorbar=dict(
                title=dict(text="dB(A)", font=dict(color="#f8fafc", size=13)),
                tickfont=dict(color="#cbd5e1", size=11),
                len=0.75,
                thickness=18,
                x=1.02
            ),
            contours=dict(z=dict(show=False)),
            lighting=dict(ambient=0.8, diffuse=0.4, specular=0.1),
            opacity=0.88,
            name="Ground Noise Field",
            hovertemplate="X: %{x:.1f}m<br>Y: %{y:.1f}m<br>Sound Level: <b>%{surfacecolor:.1f} dB(A)</b><extra></extra>"
        ))
        
    # 2. Extruded 3D Buildings
    if show_buildings and city.buildings:
        b_type_colors = {
            "Residential Area": "#3b82f6",  # Modern blue
            "Commercial Area": "#06b6d4",   # Cyan
            "Industrial Area": "#f59e0b",   # Amber
            "Silence Zone": "#10b981"       # Emerald green
        }
        
        for bld in city.buildings:
            mesh = building_to_mesh3d(bld)
            if not mesh:
                continue
            color = b_type_colors.get(bld.btype, "#64748b")
            fig.add_trace(go.Mesh3d(
                x=mesh["x"],
                y=mesh["y"],
                z=mesh["z"],
                i=mesh["i"],
                j=mesh["j"],
                k=mesh["k"],
                color=color,
                opacity=0.92,
                flatshading=True,
                lighting=dict(ambient=0.6, diffuse=0.7, specular=0.3, roughness=0.5),
                name=bld.name,
                hovertext=f"<b>{bld.name}</b><br>Type: {bld.btype}<br>Height: {bld.height}m",
                hoverinfo="text"
            ))
            
    # 3. Sound Barrier Walls
    if show_barriers and city.barriers:
        for bar in city.barriers:
            bmesh = barrier_to_mesh3d(bar)
            if not bmesh:
                continue
            fig.add_trace(go.Mesh3d(
                x=bmesh["x"],
                y=bmesh["y"],
                z=bmesh["z"],
                i=bmesh["i"],
                j=bmesh["j"],
                k=bmesh["k"],
                color="#ec4899",  # Neon pink barrier wall
                opacity=0.95,
                flatshading=True,
                name=f"Barrier: {bar.name}",
                hovertext=f"<b>Acoustic Barrier</b><br>{bar.name}<br>Height: {bar.height}m",
                hoverinfo="text"
            ))
            
    # 4. Noise Sources (Point and Road segments)
    if show_sources and sim_data.get("sources"):
        sources = sim_data["sources"]
        sx = [s.x for s in sources]
        sy = [s.y for s in sources]
        sz = [max(s.z, 1.2) for s in sources]
        stext = [f"<b>{s.name}</b><br>Type: {s.stype}<br>Power Lw: {s.lw} dB(A)" for s in sources]
        
        fig.add_trace(go.Scatter3d(
            x=sx,
            y=sy,
            z=sz,
            mode="markers",
            marker=dict(
                size=5,
                color="#f43f5e",
                symbol="circle",
                line=dict(color="#ffffff", width=1.5)
            ),
            name="Noise Sources",
            hovertext=stext,
            hoverinfo="text"
        ))
        
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=DARK_LAYOUT_TEMPLATE["paper_bgcolor"],
        plot_bgcolor=DARK_LAYOUT_TEMPLATE["plot_bgcolor"],
        font=DARK_LAYOUT_TEMPLATE["font"],
        scene=dict(
            xaxis=dict(title="East-West (m)", backgroundcolor="#0f172a", gridcolor="#1e293b", showbackground=True),
            yaxis=dict(title="North-South (m)", backgroundcolor="#0f172a", gridcolor="#1e293b", showbackground=True),
            zaxis=dict(title="Elevation (m)", range=[0, 80], backgroundcolor="#0f172a", gridcolor="#1e293b", showbackground=True),
            camera=dict(
                eye=dict(x=-1.35, y=-1.45, z=1.2),
                center=dict(x=0, y=0, z=-0.1)
            ),
            aspectratio=dict(x=1, y=1, z=0.45)
        ),
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=0.02,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(15, 23, 42, 0.75)"
        )
    )
    return fig


def build_3d_noise_surface_plot(sim_data: Dict[str, Any], colorblind_mode: bool = False) -> go.Figure:
    """
    Renders 3D Noise Surface where Z-height equals the sound pressure level (dB).
    Visually showcases acoustic decay peaks and building shadow troughs.
    """
    X = sim_data["X"]
    Y = sim_data["Y"]
    L_total = sim_data["L_total"]
    colorscale = PALETTE_COLORBLIND if colorblind_mode else PALETTE_STANDARD
    
    fig = go.Figure()
    fig.add_trace(go.Surface(
        x=X,
        y=Y,
        z=L_total,
        surfacecolor=L_total,
        colorscale=colorscale,
        cmin=35.0,
        cmax=85.0,
        colorbar=dict(title="dB(A)", len=0.7, thickness=18),
        hovertemplate="X: %{x:.1f}m<br>Y: %{y:.1f}m<br>SPL: <b>%{z:.1f} dB(A)</b><extra></extra>"
    ))
    
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=DARK_LAYOUT_TEMPLATE["paper_bgcolor"],
        scene=dict(
            xaxis=dict(title="X (m)", backgroundcolor="#0f172a", gridcolor="#1e293b"),
            yaxis=dict(title="Y (m)", backgroundcolor="#0f172a", gridcolor="#1e293b"),
            zaxis=dict(title="Sound Level (dB(A))", range=[30, 95], backgroundcolor="#0f172a", gridcolor="#1e293b"),
            camera=dict(eye=dict(x=-1.3, y=-1.5, z=1.1))
        ),
        margin=dict(l=0, r=0, t=10, b=0)
    )
    return fig


def build_2d_heatmap_plot(
    sim_data: Dict[str, Any],
    cpcb_limit: Optional[float] = None,
    colorblind_mode: bool = False
) -> go.Figure:
    """
    Top-down 2D acoustic contour map with building footprint overlays and source locations.
    Optionally highlights non-compliant violation zones.
    """
    X = sim_data["X"]
    Y = sim_data["Y"]
    L_total = sim_data["L_total"]
    city: CityLayout = sim_data["city"]
    sources = sim_data.get("sources", [])
    
    colorscale = PALETTE_COLORBLIND if colorblind_mode else PALETTE_STANDARD
    
    fig = go.Figure()
    
    # 2D Heatmap
    fig.add_trace(go.Heatmap(
        x=sim_data["x_coords"],
        y=sim_data["y_coords"],
        z=L_total,
        colorscale=colorscale,
        zmin=35.0,
        zmax=85.0,
        colorbar=dict(title="dB(A)", len=0.8, thickness=16),
        hovertemplate="X: %{x:.1f}m<br>Y: %{y:.1f}m<br>Noise Level: <b>%{z:.1f} dB(A)</b><extra></extra>",
        name="Noise Contour"
    ))
    
    # Building outlines
    for bld in city.buildings:
        coords = list(bld.polygon.exterior.coords)
        bx = [c[0] for c in coords]
        by = [c[1] for c in coords]
        fig.add_trace(go.Scatter(
            x=bx,
            y=by,
            fill="toself",
            fillcolor="rgba(30, 41, 59, 0.7)",
            line=dict(color="#38bdf8", width=1.5),
            mode="lines",
            name=bld.name,
            hovertext=f"<b>{bld.name}</b><br>{bld.btype} ({bld.height}m)",
            hoverinfo="text",
            showlegend=False
        ))
        
    # Sound Barriers
    for bar in city.barriers:
        fig.add_trace(go.Scatter(
            x=[bar.x1, bar.x2],
            y=[bar.y1, bar.y2],
            mode="lines",
            line=dict(color="#ec4899", width=4, dash="solid"),
            name="Sound Barrier",
            hovertext=f"Barrier: {bar.name} ({bar.height}m)",
            hoverinfo="text",
            showlegend=False
        ))
        
    # Noise Sources
    if sources:
        fig.add_trace(go.Scatter(
            x=[s.x for s in sources],
            y=[s.y for s in sources],
            mode="markers",
            marker=dict(size=8, color="#ef4444", symbol="x", line=dict(width=1, color="#ffffff")),
            name="Sources",
            hovertext=[f"Source: {s.name} ({s.lw} dB)" for s in sources],
            hoverinfo="text",
            showlegend=False
        ))
        
    # Optional CPCB contour boundary line
    if cpcb_limit is not None:
        fig.add_trace(go.Contour(
            x=sim_data["x_coords"],
            y=sim_data["y_coords"],
            z=L_total,
            contours=dict(
                start=cpcb_limit,
                end=cpcb_limit,
                size=1,
                coloring="none"
            ),
            line=dict(color="#ffffff", width=2.5, dash="dash"),
            name=f"CPCB Limit ({cpcb_limit} dB)",
            showlegend=True
        ))
        
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=DARK_LAYOUT_TEMPLATE["paper_bgcolor"],
        plot_bgcolor=DARK_LAYOUT_TEMPLATE["plot_bgcolor"],
        font=DARK_LAYOUT_TEMPLATE["font"],
        xaxis=dict(title="X Coordinate (meters)", range=[0, city.width], constrain="domain"),
        yaxis=dict(title="Y Coordinate (meters)", range=[0, city.height], scaleanchor="x", scaleratio=1),
        margin=dict(l=40, r=40, t=30, b=40)
    )
    return fig


def build_receiver_breakdown_chart(probe_data: Dict[str, Any]) -> go.Figure:
    """
    Renders an attenuation breakdown chart showing physical loss terms for each source.
    """
    breakdown = probe_data["breakdown"]
    if not breakdown:
        fig = go.Figure()
        fig.update_layout(title="No active sources detected.")
        return fig
        
    names = [b["source_name"][:16] for b in breakdown]
    a_div = [b["A_div"] for b in breakdown]
    a_atm = [b["A_atm"] for b in breakdown]
    a_gr = [b["A_gr"] for b in breakdown]
    a_bar = [b["A_bar"] for b in breakdown]
    rec_db = [b["received_db"] for b in breakdown]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(name="A_div (Distance)", x=names, y=a_div, marker_color="#3b82f6"))
    fig.add_trace(go.Bar(name="A_atm (Atmosphere)", x=names, y=a_atm, marker_color="#06b6d4"))
    fig.add_trace(go.Bar(name="A_gr (Ground)", x=names, y=a_gr, marker_color="#10b981"))
    fig.add_trace(go.Bar(name="A_bar (Barrier/Obstacle)", x=names, y=a_bar, marker_color="#ec4899"))
    
    fig.update_layout(
        barmode="group",
        template="plotly_dark",
        paper_bgcolor=DARK_LAYOUT_TEMPLATE["paper_bgcolor"],
        plot_bgcolor=DARK_LAYOUT_TEMPLATE["plot_bgcolor"],
        font=DARK_LAYOUT_TEMPLATE["font"],
        title="Acoustic Attenuation Breakdown per Source (dB)",
        xaxis=dict(title="Source"),
        yaxis=dict(title="Attenuation (dB)"),
        legend=dict(orientation="h", y=1.15, x=0.1)
    )
    return fig


def build_distance_decay_plot(
    source_lw: float = 95.0,
    barrier_height: float = 3.5,
    ground_type: str = "mixed"
) -> go.Figure:
    """
    Plots decibel level vs distance (1 to 200m) comparing Free-Field theoretical decay vs real terrain.
    """
    distances = np.linspace(1.0, 200.0, 200)
    
    # 1. Theoretical Free Field: L = Lw + 11 - 20*log10(d)
    l_free = source_lw + 11.0 - (20.0 * np.log10(distances) + 11.0)
    
    # 2. With Atmospheric Absorption + Ground Effect
    alpha = 1.9
    a_atm = alpha * distances / 1000.0
    a_gr = 3.0 * (1.0 - np.exp(-distances / 50.0))
    l_ground = l_free - a_atm - a_gr
    
    # 3. With Acoustic Barrier (starting at 30m)
    a_bar = np.zeros_like(distances)
    mask_bar = distances > 30.0
    a_bar[mask_bar] = np.clip(10.0 * np.log10(3.0 + 20.0 * (barrier_height / 3.0)), 6.0, 18.0)
    l_barrier = l_ground - a_bar
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=distances, y=l_free, mode="lines", name="Free-Field (-6 dB/doubling)", line=dict(color="#94a3b8", dash="dash")))
    fig.add_trace(go.Scatter(x=distances, y=l_ground, mode="lines", name="Atmosphere + Ground Effect", line=dict(color="#38bdf8", width=2.5)))
    fig.add_trace(go.Scatter(x=distances, y=l_barrier, mode="lines", name=f"With Sound Barrier ({barrier_height}m)", line=dict(color="#ec4899", width=3)))
    
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=DARK_LAYOUT_TEMPLATE["paper_bgcolor"],
        plot_bgcolor=DARK_LAYOUT_TEMPLATE["plot_bgcolor"],
        font=DARK_LAYOUT_TEMPLATE["font"],
        title="Distance Decay Profile: Geometric vs Atmospheric vs Barrier Effect",
        xaxis=dict(title="Distance from Source (meters)", gridcolor="#334155"),
        yaxis=dict(title="Received Sound Level (dB(A))", gridcolor="#334155"),
        legend=dict(orientation="h", y=1.12, x=0.05)
    )
    return fig


def build_scenario_difference_plot(sim_baseline: Dict[str, Any], sim_mitigated: Dict[str, Any]) -> go.Figure:
    """
    Renders 2D Difference Heatmap: Noise Reduction achieved (dB baseline - dB mitigated).
    Positive values represent noise reduction (cooling effect).
    """
    delta_db = sim_baseline["L_total"] - sim_mitigated["L_total"]
    
    fig = go.Figure()
    fig.add_trace(go.Heatmap(
        x=sim_baseline["x_coords"],
        y=sim_baseline["y_coords"],
        z=delta_db,
        colorscale="Viridis",
        zmin=0.0,
        zmax=18.0,
        colorbar=dict(title="dB Reduction", len=0.8, thickness=16),
        hovertemplate="X: %{x:.1f}m<br>Y: %{y:.1f}m<br>Noise Reduction: <b>+%{z:.1f} dB</b><extra></extra>"
    ))
    
    city = sim_baseline["city"]
    for bld in city.buildings:
        coords = list(bld.polygon.exterior.coords)
        bx = [c[0] for c in coords]
        by = [c[1] for c in coords]
        fig.add_trace(go.Scatter(
            x=bx, y=by, mode="lines", line=dict(color="#94a3b8", width=1),
            fill="toself", fillcolor="rgba(30, 41, 59, 0.5)",
            hovertext=bld.name, hoverinfo="text", showlegend=False
        ))
        
    for bar in sim_mitigated["city"].barriers:
        fig.add_trace(go.Scatter(
            x=[bar.x1, bar.x2], y=[bar.y1, bar.y2],
            mode="lines", line=dict(color="#ec4899", width=4),
            name="Barrier Installed", showlegend=True
        ))
        
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=DARK_LAYOUT_TEMPLATE["paper_bgcolor"],
        plot_bgcolor=DARK_LAYOUT_TEMPLATE["plot_bgcolor"],
        font=DARK_LAYOUT_TEMPLATE["font"],
        title="Spatial Noise Reduction: [Baseline - Mitigated Scenario] (dB)",
        xaxis=dict(title="X (meters)"),
        yaxis=dict(title="Y (meters)", scaleanchor="x", scaleratio=1),
        margin=dict(l=40, r=40, t=40, b=40)
    )
    return fig


def build_diurnal_24hr_chart(day_mean_db: float, night_reduction_db: float = 6.0) -> go.Figure:
    """Generates 24-hour diurnal noise exposure line chart against CPCB day/night standards."""
    from core.sources import get_diurnal_traffic_factors
    
    hours = np.arange(24)
    traffic_profile = get_diurnal_traffic_factors()
    
    # Noise scales logarithmically with traffic flow
    # dB_hour = day_mean_db + 10*log10(traffic_profile)
    spl_hourly = day_mean_db + 10.0 * np.log10(np.maximum(0.08, traffic_profile))
    
    # CPCB residential limit lines
    cpcb_limits = [45.0 if (h < 6 or h >= 22) else 55.0 for h in hours]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hours,
        y=spl_hourly,
        mode="lines+markers",
        name="Estimated Hourly Leq",
        line=dict(color="#38bdf8", width=3),
        marker=dict(size=6, color="#0284c7")
    ))
    fig.add_trace(go.Scatter(
        x=hours,
        y=cpcb_limits,
        mode="lines",
        name="CPCB Residential Limit (Day 55 / Night 45 dB)",
        line=dict(color="#ef4444", width=2, dash="dash")
    ))
    
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=DARK_LAYOUT_TEMPLATE["paper_bgcolor"],
        plot_bgcolor=DARK_LAYOUT_TEMPLATE["plot_bgcolor"],
        font=DARK_LAYOUT_TEMPLATE["font"],
        title="24-Hour Diurnal Noise Exposure vs CPCB Regulatory Thresholds",
        xaxis=dict(title="Hour of Day (0:00 - 23:00)", tickmode="linear", dtick=2),
        yaxis=dict(title="Sound Level (dB(A))", range=[35, 80]),
        legend=dict(orientation="h", y=1.12, x=0.1)
    )
    return fig
