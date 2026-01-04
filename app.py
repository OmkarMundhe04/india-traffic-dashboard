import streamlit as st
import folium
from streamlit.components.v1 import html
import pandas as pd
from folium.plugins import HeatMap
from folium import CircleMarker
import os
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from traffic_data import get_congestion_for_cities
from utils import normalize_congestion, congestion_to_color, radius_from_congestion

# ---------------- CONFIG ----------------
MAPMYINDIA_KEY = os.getenv("MAPMYINDIA_KEY", "")
TOMTOM_KEY = os.getenv("TOMTOM_API_KEY", "P8syJbFkhS9wAsarqMtyIlHYDhnxbgUo")

st.set_page_config(
    page_title="India Real-Time Traffic Dashboard ",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded"
)

REFRESH_INTERVAL_SEC = 300  # 5 minutes cache to avoid rate limits

# ---------------- CUSTOM CSS ----------------
st.markdown("""
<style>

/* ================================
   BASE (shared across themes)
=================================*/

.block-container {
    padding-top: 2rem;
    border-radius: 20px;
    margin: 1rem;
    box-shadow: 0 20px 60px rgba(0,0,0,.25);
}

.card {
    border-radius: 15px;
    padding: 1.5rem;
    transition: .3s ease;
    border: 1px solid rgba(0,0,0,.1);
}

.card:hover { transform: translateY(-2px); }

.map-container {
    border-radius: 15px;
    overflow: hidden;
    margin: 1rem 0;
    box-shadow: 0 10px 40px rgba(0,0,0,.25);
}

/* Metric Gradient Text */
[data-testid="stMetricValue"] {
    font-size: 2.5rem;
    font-weight: 800;
    background: linear-gradient(135deg,#667eea,#764ba2);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* Buttons (base) */
.stButton > button {
    width: 100%;
    border-radius: 12px;
    padding: .75rem 1.5rem;
    font-weight: 700;
    border: none;
    transition: .25s;
    box-shadow: 0 4px 14px rgba(0,0,0,.25);
}
.stButton > button:hover { transform: translateY(-2px); }


/*****************************************
   🌞 LIGHT THEME
******************************************/
@media (prefers-color-scheme: light) {

    .main {
        background: linear-gradient(135deg,#e6ecff,#ffffff);
    }

    .block-container {
        background: #ffffff;
        border: 1px solid #e2e8f0;
    }

    h1 {
        background: linear-gradient(135deg,#5b6fe6,#764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 900;
    }

    h2,h3 { color:#2d3748; }

    .card {
        background:#ffffff;
        box-shadow:0 4px 18px rgba(0,0,0,.12);
    }

    /* ---------- SIDEBAR ---------- */

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg,#667eea,#764ba2);
    }

    /* Sidebar text & section labels */
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label {
        color:#ffffff !important;
    }

    /* ---------- SELECTBOX (Light mode readable) ---------- */

    /* Selected value */
    [data-testid="stSidebar"] [data-baseweb="select"] span {
        color:#111827 !important;
        font-weight:700;
    }

    /* Input text */
    [data-testid="stSidebar"] [data-baseweb="select"] input {
        color:#111827 !important;
    }

    /* Select container */
    [data-testid="stSidebar"] [data-baseweb="select"] > div {
        background:#ffffff !important;
        border:2px solid #cbd5e1 !important;
        border-radius:10px !important;
    }

    /* Dropdown options */
    [data-baseweb="menu"] * {
        color:#111827 !important;
    }

    /* ---------- FORCE REFRESH BUTTON (Human-eye contrast safe) ---------- */

    /* Normal state */
    [data-testid="stSidebar"] .stButton > button,
    [data-testid="stSidebar"] .stButton > button * {
        background:#ffffff !important;
        color:#1f2920 !important;        /* strong dark text */
        font-weight:700 !important;
        border:none !important;
        border-radius:9px !important;
        box-shadow:none !important;
        opacity:0.9 !important;
        filter:none !important;
    }

    /* Hover */
    [data-testid="stSidebar"] .stButton > button:hover:not(:disabled),
    [data-testid="stSidebar"] .stButton > button:hover:not(:disabled) * {
        background:#f1f5f9 !important;
        color:#0f172a !important;
        opacity:0.5 !important
        border-color:#020617 !important;
        transform:translateY(-0.5px);
    }

    /* Disabled / cooldown — readable but subtle */
    [data-testid="stSidebar"] .stButton > button:disabled,
    [data-testid="stSidebar"] .stButton > button:disabled * {
        background:#f3f4f6 !important;
        color:#475569 !important;        /* visible muted gray */
        border:1px solid #d1d5db !important;
        
        opacity:0.75 !important;            /* remove washout */
        filter:none !important;
    }

    /* ---------- INFO BOX ---------- */
    .info-box {
        background:#f7f9ff;
        border-left:4px solid #667eea;
    }
}


/*****************************************
   🌙 DARK THEME
******************************************/
@media (prefers-color-scheme: dark) {

    .main {
        background: linear-gradient(135deg,#0b1220,#141a2b);
    }

    .block-container {
        background:#0f172a;
        border:1px solid #1f2937;
    }

    h1 {
        background: linear-gradient(135deg,#9aa8ff,#c6a5ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight:900;
    }

    h2,h3 { color:#e5e7eb; }

    .card {
        background:#111c32;
        border:1px solid #1f2d4d;
        box-shadow:0 8px 30px rgba(0,0,0,.45);
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg,#1c2750,#2d1f64);
    }

    [data-testid="stSidebar"] * {
        color:#f1f5f9 !important;
    }

    /* Selectbox (dark mode readable) */
    [data-testid="stSidebar"] [data-baseweb="select"] span,
    [data-testid="stSidebar"] [data-baseweb="select"] input {
        color:#f8fafc !important;
        font-weight:600;
    }

    [data-baseweb="menu"] * {
        color:#f8fafc !important;
    }

    .info-box {
        background:rgba(118,75,162,.15);
        border-left:4px solid #9f7aea;
        color:#e5e7eb;
    }
}

/* Charts transparent */
.js-plotly-plot,
.plot-container {
    background:transparent !important;
}

</style>
""", unsafe_allow_html=True)


# ---------------- CITY COORDINATES ----------------
city_coords = {
    "Mumbai": (19.0760, 72.8777),
    "Latur": (18.4070, 76.5604),
    "Pune": (18.5204, 73.8567),
    "Kolhapur": (16.7050, 74.2433),
    "Delhi": (28.6139, 77.2090),
    "Lucknow": (26.8467, 80.9462),
    "Jaipur": (26.9124, 75.7873),
    "Ahmedabad": (23.0225, 72.5714),
    "Bengaluru": (12.9716, 77.5946),
    "Chennai": (13.0827, 80.2707),
    "Hyderabad": (17.3850, 78.4867),
    "Kolkata": (22.5726, 88.3639)
    
    
}

# ---------------- DATA FETCH ----------------
@st.cache_data(ttl=REFRESH_INTERVAL_SEC, show_spinner=False)
def fetch_traffic_data():
    return get_congestion_for_cities(city_coords, TOMTOM_KEY, MAPMYINDIA_KEY)

with st.spinner('🔄 Fetching live traffic data from TomTom...'):
    hotspots, api_working, api_source = fetch_traffic_data()

# ---------------- SIDEBAR ----------------
with st.sidebar:
    
    st.markdown("### 🔍 Navigation & Controls")
    
    city_list = list(city_coords.keys())
    selected_city = st.selectbox("Select City", city_list, label_visibility="collapsed")

    st.markdown("---")
    
    # API Status with clear indicator
    st.markdown("### 📡 Connection Status")
    
    if api_working:
        st.markdown(f"""
        <div class='api-status-live'>
            ✅ LIVE API ACTIVE
        </div>
        """, unsafe_allow_html=True)
        st.success(f"🌐 Connected to {api_source}")
        st.info(f"🔄 Auto-refresh: {REFRESH_INTERVAL_SEC//60} minutes")
    else:
        st.markdown("""
        <div class='api-status-simulated'>
            🤖 SIMULATION MODE
        </div>
        """, unsafe_allow_html=True)
        st.warning("Using AI-based prediction model")
        
        if not TOMTOM_KEY:
            st.error("⚠️ No TomTom API key found")
            st.info("Set TOMTOM_API_KEY environment variable")
    
    st.markdown("---")
    
    # Refresh controls
    st.markdown("### 🔄 Data Controls")
    if st.button("🔄 Force Refresh Now", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
    
    st.markdown("---")
    
    # Stats
    st.markdown("### 📊 Quick Stats")
    st.metric("Cities Monitored", len(city_coords))
    st.metric("Data Source", "TomTom Traffic API" if api_working else "AI Model")
    
    st.markdown("---")
    
    # About
    st.markdown("### ℹ️ About")
    st.markdown("""
    Real-time traffic insights using:
    - 🌐 TomTom Traffic Flow API
    - 🗺️ MapmyIndia Maps
    - 🤖 AI Prediction Fallback
    - 📊 Interactive Analytics
    """)

# Create dataframe for analysis
df = pd.DataFrame([
    {
        "City": s["city"], 
        "Congestion": s["congestion"], 
        "Source": s["source"],
        "Speed": s.get("current_speed", "N/A"),
        "Free Flow": s.get("free_flow_speed", "N/A")
    } 
    for s in hotspots
])

# ---------------- TOP METRICS ----------------
st.markdown("## 📈 Key Metrics")

avg_congestion = df["Congestion"].mean()
max_congestion = df["Congestion"].max()
min_congestion = df["Congestion"].min()
top_city = df.loc[df["Congestion"].idxmax(), "City"]
best_city = df.loc[df["Congestion"].idxmin(), "City"]
selected_congestion = df[df["City"] == selected_city]["Congestion"].values[0]

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="🔴 Highest Congestion",
        value=f"{max_congestion:.1f}%",
        delta=f"{top_city}",
        delta_color="inverse"
    )

with col2:
    st.metric(
        label="📊 Average Traffic",
        value=f"{avg_congestion:.1f}%",
        delta=f"{max_congestion - avg_congestion:.1f}% from peak"
    )

with col3:
    st.metric(
        label="🟢 Lowest Congestion",
        value=f"{min_congestion:.1f}%",
        delta=f"{best_city}"
    )

with col4:
    delta_val = selected_congestion - avg_congestion
    st.metric(
        label=f"📍 {selected_city}",
        value=f"{selected_congestion:.1f}%",
        delta=f"{delta_val:+.1f}% vs avg",
        delta_color="inverse" if delta_val > 0 else "normal"
    )

# ---------------- MAP ----------------
st.markdown("## 🗺️ Interactive Traffic Map")

lat, lon = city_coords[selected_city]
m = folium.Map(
    location=[lat, lon], 
    zoom_start=11, 
    tiles="cartodbpositron",
    control_scale=True
)

# Add MapmyIndia traffic tiles if available
if MAPMYINDIA_KEY:
    folium.TileLayer(
        tiles=f"https://apis.mapmyindia.com/advancedmaps/v1/{MAPMYINDIA_KEY}/traffic/256/{{z}}/{{x}}/{{y}}.png",
        attr="MapmyIndia Traffic",
        name="Traffic Overlay",
        overlay=True,
        control=True,
        max_zoom=18
    ).add_to(m)

# Add markers and heatmap data
heat_data = []
for spot in hotspots:
    city = spot["city"]
    clat = spot["lat"]
    clon = spot["lon"]
    congestion = float(spot["congestion"])

    heat_data.append([clat, clon, normalize_congestion(congestion)])

    # Popup content
    popup_html = f"""
    <div style='font-family: Arial; padding: 12px; min-width: 200px;'>
        <h4 style='margin: 0 0 10px 0; color: #2d3748;'>{city}</h4>
        <p style='margin: 5px 0;'><strong>🚦 Congestion:</strong> {congestion:.1f}%</p>
        <p style='margin: 5px 0;'><strong>📊 Source:</strong> {spot.get('source', 'N/A')}</p>
    """
    
    if 'current_speed' in spot and spot['current_speed'] != 'N/A':
        popup_html += f"<p style='margin: 5px 0;'><strong>🚗 Current Speed:</strong> {spot['current_speed']} km/h</p>"
        popup_html += f"<p style='margin: 5px 0;'><strong>⚡ Free Flow:</strong> {spot['free_flow_speed']} km/h</p>"
    
    popup_html += f"<p style='margin: 5px 0; font-size: 0.85em; color: #718096;'><strong>⏰ Updated:</strong> {datetime.now().strftime('%H:%M')}</p>"
    popup_html += "</div>"

    CircleMarker(
        location=[clat, clon],
        radius=radius_from_congestion(congestion),
        color=congestion_to_color(congestion),
        fill=True,
        fill_opacity=0.7,
        weight=2,
        popup=folium.Popup(popup_html, max_width=300)
    ).add_to(m)

    # City label
    folium.map.Marker(
        [clat, clon],
        icon=folium.DivIcon(
            html=f"""
            <div style="
                font-size: 11px;
                font-weight: 700;
                color: #2d3748;
                background: white;
                padding: 6px 12px;
                border-radius: 12px;
                border: 2px solid {congestion_to_color(congestion)};
                box-shadow: 0 2px 8px rgba(0,0,0,0.2);
                white-space: nowrap;
            ">
                {city}: {congestion:.1f}%
            </div>
            """
        )
    ).add_to(m)

# Add heatmap overlay
HeatMap(heat_data, radius=25, blur=18, min_opacity=0.4, name="Traffic Heatmap").add_to(m)
folium.LayerControl().add_to(m)

# Save and display map
m.save("traffic_map.html")
with open("traffic_map.html", "r", encoding="utf-8") as f:
    map_html = f.read()

st.markdown("<div class='map-container'>", unsafe_allow_html=True)
st.components.v1.html(map_html, height=650, scrolling=True)
st.markdown("</div>", unsafe_allow_html=True)

# ---------------- VISUALIZATIONS ----------------
st.markdown("## 📊 Traffic Analytics")

tab1, tab2, tab3 = st.tabs(["📊 City Comparison", "📈 Detailed Analysis", "📋 Data Table"])

with tab1:
    df_sorted = df.sort_values("Congestion", ascending=True)
    
    fig = px.bar(
        df_sorted,
        x="Congestion",
        y="City",
        orientation='h',
        title="Traffic Congestion Levels Across Cities",
        color="Congestion",
        color_continuous_scale=["#48bb78", "#ecc94b", "#f56565"],
        text="Congestion"
    )
    
    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig.update_layout(
        height=500,
        showlegend=False,
        xaxis_title="Congestion Level (%)",
        yaxis_title="",
        font=dict(size=12),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )
    
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    col1, col2 = st.columns(2)
    
    with col1:
        # Pie chart
        fig_pie = px.pie(
            df,
            values="Congestion",
            names="City",
            title="Traffic Distribution by City",
            hole=0.4,
            color_discrete_sequence=px.colors.sequential.RdBu_r
        )
        fig_pie.update_layout(height=400)
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Gauge chart for selected city
        selected_data = df[df["City"] == selected_city].iloc[0]
        
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=selected_data["Congestion"],
            title={'text': f"{selected_city} Traffic Level"},
            delta={'reference': avg_congestion, 'suffix': '% vs avg'},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': congestion_to_color(selected_data["Congestion"])},
                'steps': [
                    {'range': [0, 30], 'color': "#e6f4ea"},
                    {'range': [30, 60], 'color': "#fef5e7"},
                    {'range': [60, 100], 'color': "#fadbd8"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 80
                }
            }
        ))
        
        fig_gauge.update_layout(height=400)
        st.plotly_chart(fig_gauge, use_container_width=True)

with tab3:
    # Enhanced data table
    df_display = df.copy()
    df_display["Congestion"] = df_display["Congestion"].apply(lambda x: f"{x:.1f}%")
    df_display["Updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Reorder columns
    column_order = ["City", "Congestion", "Speed", "Free Flow", "Source", "Updated"]
    df_display = df_display[column_order]
    
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "City": st.column_config.TextColumn("City", width="medium"),
            "Congestion": st.column_config.TextColumn("Congestion", width="small"),
            "Speed": st.column_config.TextColumn("Current Speed (km/h)", width="small"),
            "Free Flow": st.column_config.TextColumn("Free Flow (km/h)", width="small"),
            "Source": st.column_config.TextColumn("Data Source", width="medium"),
            "Updated": st.column_config.TextColumn("Last Updated", width="medium")
        }
    )

# ---------------- INSIGHTS ----------------
st.markdown("## 💡 Traffic Insights")

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"""
    <div class='card'>
        <h3>🎯 Dashboard Statistics</h3>
        <ul style='line-height: 2; list-style: none; padding-left: 0;'>
            <li>🏙️ <strong>Cities:</strong> {len(city_coords)} major metros</li>
            <li>🔄 <strong>Refresh:</strong> Every {REFRESH_INTERVAL_SEC//60} minutes</li>
            <li>📡 <strong>Source:</strong> {api_source if api_working else 'AI Model'}</li>
            <li>✅ <strong>Status:</strong> {'Live Data' if api_working else 'Simulated'}</li>
            <li>📊 <strong>Coverage:</strong> Pan-India</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with col2:
    # Traffic status interpretation for selected city
    if selected_congestion < 30:
        status = "🟢 Free Flow"
        color = "#48bb78"
        advice = "Traffic is moving smoothly. Excellent time to travel!"
    elif selected_congestion < 60:
        status = "🟡 Moderate Traffic"
        color = "#ecc94b"
        advice = "Expect some delays. Plan extra time for your journey."
    else:
        status = "🔴 Heavy Congestion"
        color = "#f56565"
        advice = "Significant delays expected. Consider alternate routes or wait."
    
    st.markdown(f"""
    <div class='card' style='border-left: 4px solid {color};'>
        <h3>{status}</h3>
        <p style='font-size: 1.2rem; margin: 1rem 0; font-weight: 600;'>
            <strong>{selected_city}:</strong> {selected_congestion:.1f}% congestion
        </p>
        <p style='color: #4a5568; line-height: 1.6;'>{advice}</p>
    </div>
    """, unsafe_allow_html=True)

# ---------------- FOOTER ----------------
st.markdown("---")
st.markdown(f"""
<div style='text-align: center; padding: 2rem 0;'>
    <p style='font-size: 1.1rem; color: #4a5568; margin-bottom: 0.5rem; font-weight: 600;'>
        Made with ❤️ using Python, Streamlit, Folium, Plotly & TomTom Traffic API
    </p>
    <p style='font-size: 0.95rem; color: #718096; margin: 0.5rem 0;'>
        {'🟢 Live API Connected - Real-time data from ' + api_source if api_working else '🤖 Running in AI Prediction Mode'}
    </p>
    <p style='font-size: 0.875rem; color: #a0aec0;'>
        🚦 Traffic data updates automatically every {REFRESH_INTERVAL_SEC//60} minutes
    </p>
    <p style='font-size: 1.1rem; color: #4a5568; margin-bottom: 0.5rem; font-weight: 600;'>
        CREATOR: Made with ❤️ using Python BY ->> OMKAR MUNDHE , omkarmundhe04@gmail.com
    </p>
</div>
""", unsafe_allow_html=True)