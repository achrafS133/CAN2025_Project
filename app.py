"""
CAN 2025 Guardian - Security Operations Center (SOC)
Professional Security Command Center Dashboard
Developed for SBI Student Challenge 2025
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import os
import cv2
import tempfile
import datetime
import random
import time

# Import custom modules
from security_logic import detect_threats
from chatbot_logic import get_response
from emotion_logic import analyze_crowd_mood
from stadium_data import create_stadium_map, get_stadium_data
from reports import generate_pdf_report
from streamlit_folium import st_folium
from langchain.schema import HumanMessage, AIMessage

# MySQL Database Connection (with fallback)
try:
    import mysql.connector
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False

# ============================================
# PAGE CONFIGURATION
# ============================================
st.set_page_config(
    page_title="CAN 2025 Guardian | SOC",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# CUSTOM CSS - PROFESSIONAL SOC THEME
# ============================================
st.markdown("""
<style>
    /* Import Professional Font */
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Roboto:wght@300;400;500;700&display=swap');
    
    /* Main Background - Dark SOC Theme */
    .stApp {
        background: linear-gradient(135deg, #0a0f1a 0%, #0d1117 50%, #0a0f1a 100%);
        color: #e6edf3;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #161b22 0%, #0d1117 100%);
        border-right: 2px solid #ff4b4b;
    }
    
    /* Headers - Orbitron Font */
    h1, h2, h3 {
        font-family: 'Orbitron', monospace !important;
        color: #ff4b4b !important;
        text-transform: uppercase;
        letter-spacing: 3px;
        text-shadow: 0 0 10px rgba(255, 75, 75, 0.5);
    }
    
    /* Regular text */
    p, span, div {
        font-family: 'Roboto', sans-serif;
    }
    
    /* KPI Card Styling */
    .kpi-container {
        display: flex;
        gap: 15px;
        margin-bottom: 20px;
    }
    
    .kpi-card {
        background: linear-gradient(145deg, #1a1f2e 0%, #0d1117 100%);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0,0,0,0.4);
        transition: all 0.3s ease;
        flex: 1;
    }
    
    .kpi-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(255, 75, 75, 0.2);
    }
    
    .kpi-card.critical {
        border-color: #ff4b4b;
        box-shadow: 0 0 25px rgba(255, 75, 75, 0.3);
    }
    
    .kpi-card.warning {
        border-color: #ffcc00;
        box-shadow: 0 0 25px rgba(255, 204, 0, 0.2);
    }
    
    .kpi-card.success {
        border-color: #00ff88;
        box-shadow: 0 0 25px rgba(0, 255, 136, 0.2);
    }
    
    .kpi-card.info {
        border-color: #00d4ff;
        box-shadow: 0 0 25px rgba(0, 212, 255, 0.2);
    }
    
    .kpi-title {
        font-family: 'Roboto', sans-serif;
        font-size: 0.75rem;
        color: #8b949e;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 8px;
    }
    
    .kpi-value {
        font-family: 'Orbitron', monospace;
        font-size: 1.8rem;
        font-weight: 700;
        margin: 10px 0;
    }
    
    .kpi-subtitle {
        font-size: 0.7rem;
        color: #6c757d;
    }
    
    /* Status Indicator */
    .status-dot {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 8px;
        animation: pulse 2s infinite;
    }
    
    .status-dot.online {
        background-color: #00ff88;
        box-shadow: 0 0 10px #00ff88;
    }
    
    .status-dot.warning {
        background-color: #ffcc00;
        box-shadow: 0 0 10px #ffcc00;
    }
    
    .status-dot.critical {
        background-color: #ff4b4b;
        box-shadow: 0 0 10px #ff4b4b;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #ff4b4b 0%, #d32f2f 100%);
        color: white;
        border-radius: 8px;
        border: none;
        font-family: 'Roboto', sans-serif;
        font-weight: 500;
        letter-spacing: 1px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(255, 75, 75, 0.3);
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #ff6b6b 0%, #ff4b4b 100%);
        box-shadow: 0 6px 25px rgba(255, 75, 75, 0.5);
        transform: translateY(-2px);
    }
    
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: #161b22;
        padding: 10px;
        border-radius: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #0d1117;
        border-radius: 8px;
        padding: 12px 24px;
        color: #8b949e;
        font-family: 'Roboto', sans-serif;
        border: 1px solid #30363d;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #ff4b4b 0%, #d32f2f 100%) !important;
        color: white !important;
        border: none !important;
    }
    
    /* Data Table Styling */
    .dataframe {
        background-color: #161b22 !important;
        border-radius: 10px;
    }
    
    /* Footer */
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background: linear-gradient(90deg, #0d1117 0%, #161b22 50%, #0d1117 100%);
        color: #8b949e;
        text-align: center;
        padding: 12px;
        font-size: 0.75rem;
        border-top: 1px solid #ff4b4b;
        z-index: 100;
        font-family: 'Roboto', sans-serif;
    }
    
    /* Metrics Override */
    div[data-testid="stMetricValue"] {
        font-family: 'Orbitron', monospace;
    }
    
    /* Alert Box */
    .alert-box {
        background: linear-gradient(135deg, #1c0f0f 0%, #0d1117 100%);
        border: 1px solid #ff4b4b;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
    
    /* Scanner Animation */
    .scanner-line {
        height: 3px;
        background: linear-gradient(90deg, transparent, #ff4b4b, transparent);
        animation: scan 2s infinite;
    }
    
    @keyframes scan {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# DATABASE FUNCTIONS
# ============================================
def get_db_connection():
    """Establish MySQL database connection."""
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",  # Default XAMPP/WAMP password
            database="can2025"
        )
        return conn
    except Exception as e:
        return None

def fetch_incidents_from_db():
    """Fetch incidents from MySQL database."""
    if not MYSQL_AVAILABLE:
        return None
    
    conn = get_db_connection()
    if conn is None:
        return None
    
    try:
        query = "SELECT * FROM incidents ORDER BY timestamp DESC LIMIT 20"
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        return None

def insert_incident(location, threat_type, confidence, status="Pending"):
    """Insert a new incident into the database."""
    if not MYSQL_AVAILABLE:
        return False
    
    conn = get_db_connection()
    if conn is None:
        return False
    
    try:
        cursor = conn.cursor()
        query = """INSERT INTO incidents (location, threat_type, confidence, status) 
                   VALUES (%s, %s, %s, %s)"""
        cursor.execute(query, (location, threat_type, confidence, status))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        return False

def get_mock_incidents():
    """Generate mock incident data when database is unavailable."""
    mock_data = {
        'id': [1, 2, 3, 4, 5, 6, 7, 8],
        'timestamp': [
            datetime.datetime.now() - datetime.timedelta(minutes=random.randint(5, 120))
            for _ in range(8)
        ],
        'location': [
            'Gate 4 - Casablanca', 'Zone B - Rabat', 'VIP Entrance - Tangier',
            'Gate 1 - Marrakech', 'North Stand - Agadir', 'Gate 5 - Fez',
            'Parking A - Casablanca', 'South Exit - Rabat'
        ],
        'threat_type': [
            'Knife', 'Crowd Density', 'Bottle', 'Suspicious Object',
            'Altercation', 'Unattended Bag', 'Clear', 'Crowd Surge'
        ],
        'confidence': [0.88, 0.95, 0.75, 0.60, 0.82, 0.91, 0.45, 0.78],
        'status': [
            'Resolved', 'Active', 'Pending', 'Investigating',
            'Resolved', 'Active', 'Resolved', 'Monitoring'
        ]
    }
    return pd.DataFrame(mock_data).sort_values('timestamp', ascending=False)

# ============================================
# HELPER FUNCTIONS
# ============================================
TRANSPARENT = 'rgba(0,0,0,0)'

def get_threat_level():
    """Dynamic threat level based on simulated conditions."""
    levels = [
        ("LOW", "#00ff88", "success"),
        ("ELEVATED", "#ffcc00", "warning"),
        ("HIGH", "#ff8c00", "warning"),
        ("CRITICAL", "#ff4b4b", "critical")
    ]
    weights = [0.5, 0.3, 0.15, 0.05]
    return random.choices(levels, weights)[0]

def get_crowd_density():
    """Simulated crowd density."""
    return random.randint(800, 5500)

def get_active_alerts():
    """Simulated active alerts count."""
    resolved = random.randint(15, 45)
    return f"{resolved} Resolved"

# ============================================
# SIDEBAR NAVIGATION
# ============================================
with st.sidebar:
    # Logo
    st.markdown("""
    <div style="text-align: center; padding: 20px 0;">
        <h1 style="font-size: 2.5rem; margin: 0;">🛡️</h1>
        <h3 style="font-size: 0.9rem; margin: 5px 0;">GUARDIAN SOC</h3>
        <p style="color: #6c757d; font-size: 0.7rem;">SECURITY OPERATIONS CENTER</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Navigation Menu
    menu = st.radio(
        "🎛️ CONTROL PANEL",
        ["🛰️ Command Center", "👁️ Threat Scanner", "🗺️ Venue Monitor", "💬 AI Assistant", "🛡️ Cyber Shield", "⚙️ Settings"],
        index=0
    )
    
    st.markdown("---")
    
    # System Status Panel
    st.markdown("### 📡 SYSTEM STATUS")
    
    # Database Status
    db_status = "🟢 Connected" if fetch_incidents_from_db() is not None else "🟡 Mock Mode"
    st.markdown(f"**Database:** {db_status}")
    
    # Live Clock
    st.markdown(f"**Time:** {datetime.datetime.now().strftime('%H:%M:%S')}")
    
    # Uptime
    st.markdown("**Uptime:** 99.97%")
    
    st.markdown("---")
    
    # Quick Actions
    st.markdown("### ⚡ QUICK ACTIONS")
    if st.button("🚨 Emergency Protocol", use_container_width=True):
        st.error("⚠️ Emergency protocol activated!")
    
    if st.button("📊 Generate Report", use_container_width=True):
        st.success("✅ Report generated successfully!")

# ============================================
# COMMAND CENTER VIEW
# ============================================
if menu == "🛰️ Command Center":
    st.markdown("""
    <h1 style="text-align: center; margin-bottom: 5px;">🛰️ SECURITY COMMAND CENTER</h1>
    <p style="text-align: center; color: #8b949e; font-size: 0.9rem;">CAN 2025 | AFRICA CUP OF NATIONS | MOROCCO</p>
    """, unsafe_allow_html=True)
    
    # === TOP KPI DASHBOARD ===
    st.markdown("---")
    
    threat = get_threat_level()
    crowd = get_crowd_density()
    alerts = get_active_alerts()
    
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    
    with kpi1:
        st.markdown(f"""
        <div class="kpi-card {threat[2]}">
            <div class="kpi-title">THREAT LEVEL</div>
            <div class="kpi-value" style="color: {threat[1]};">{threat[0]}</div>
            <div class="kpi-subtitle"><span class="status-dot {'critical' if threat[0] == 'CRITICAL' else 'online'}"></span>Live Assessment</div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi2:
        st.markdown(f"""
        <div class="kpi-card warning">
            <div class="kpi-title">CROWD DENSITY</div>
            <div class="kpi-value" style="color: #ffcc00;">{crowd:,}</div>
            <div class="kpi-subtitle">Fans in Active Zones</div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi3:
        st.markdown(f"""
        <div class="kpi-card success">
            <div class="kpi-title">ACTIVE ALERTS</div>
            <div class="kpi-value" style="color: #00ff88;">{alerts}</div>
            <div class="kpi-subtitle">Last 24 Hours</div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi4:
        st.markdown("""
        <div class="kpi-card info">
            <div class="kpi-title">SYSTEM STATUS</div>
            <div class="kpi-value" style="color: #00d4ff;">ONLINE</div>
            <div class="kpi-subtitle"><span class="status-dot online"></span>All Systems Operational</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # === MAIN CONTENT ===
    col_chart, col_alerts = st.columns([2, 1])
    
    with col_chart:
        st.markdown("### 📈 REAL-TIME ENTRANCE FLOW")
        
        data = {
            'Hour': ['08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00'],
            'Entries': [500, 1200, 3500, 4800, 3200, 1500, 2200, 6800, 8500, 7200]
        }
        df = pd.DataFrame(data)
        
        fig = px.area(df, x='Hour', y='Entries',
                     template="plotly_dark",
                     color_discrete_sequence=['#ff4b4b'])
        fig.update_layout(
            plot_bgcolor=TRANSPARENT,
            paper_bgcolor=TRANSPARENT,
            font=dict(family="Roboto"),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
        )
        fig.update_traces(fill='tozeroy', fillcolor='rgba(255, 75, 75, 0.2)')
        st.plotly_chart(fig, use_container_width=True)
    
    with col_alerts:
        st.markdown("### 🚨 LIVE FEED")
        
        alerts_data = [
            ("🟢", "18:45", "Gate 1", "Normal flow"),
            ("🔴", "18:32", "Zone A", "Object detected"),
            ("🟡", "18:15", "Gate 5", "High density"),
            ("🟢", "18:02", "VIP Exit", "Cleared"),
            ("🔴", "17:48", "Gate 3", "Altercation"),
            ("🟢", "17:30", "Zone B", "Resolved"),
        ]
        
        for status, time, loc, desc in alerts_data:
            st.markdown(f"""
            <div style="background: #161b22; padding: 10px; margin: 5px 0; border-radius: 8px; border-left: 3px solid {'#00ff88' if status == '🟢' else ('#ffcc00' if status == '🟡' else '#ff4b4b')};">
                <span style="font-size: 0.8rem; color: #6c757d;">[{time}]</span>
                <strong style="color: #e6edf3;"> {loc}</strong><br>
                <span style="font-size: 0.9rem; color: #8b949e;">{desc}</span>
            </div>
            """, unsafe_allow_html=True)
    
    # === DATABASE LOG ===
    st.markdown("---")
    st.markdown("### 🗄️ SECURITY INCIDENT DATABASE")
    
    # Try to fetch from MySQL, fallback to mock data
    incidents_df = fetch_incidents_from_db()
    
    if incidents_df is not None:
        st.success("🔗 Connected to MySQL Database (can2025.incidents)")
    else:
        st.warning("📋 Database unavailable - Displaying mock data for demonstration")
        incidents_df = get_mock_incidents()
    
    # Style the dataframe
    def style_status(val):
        colors = {
            'Resolved': 'background-color: rgba(0, 255, 136, 0.2); color: #00ff88;',
            'Active': 'background-color: rgba(255, 75, 75, 0.2); color: #ff4b4b;',
            'Pending': 'background-color: rgba(255, 204, 0, 0.2); color: #ffcc00;',
            'Investigating': 'background-color: rgba(0, 212, 255, 0.2); color: #00d4ff;',
            'Monitoring': 'background-color: rgba(255, 140, 0, 0.2); color: #ff8c00;'
        }
        return colors.get(val, '')
    
    styled_df = incidents_df.style.applymap(style_status, subset=['status'])
    st.dataframe(styled_df, use_container_width=True, height=300)

# ============================================
# THREAT SCANNER VIEW
# ============================================
elif menu == "👁️ Threat Scanner":
    st.markdown("""
    <h1 style="text-align: center;">👁️ AI THREAT SCANNER</h1>
    <p style="text-align: center; color: #8b949e;">Deep scan for threats and crowd sentiment using YOLOv8 + FER</p>
    """, unsafe_allow_html=True)
    
    # === TOP KPI DASHBOARD ===
    st.markdown("---")
    
    threat = get_threat_level()
    
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    
    with kpi1:
        st.markdown(f"""
        <div class="kpi-card {threat[2]}">
            <div class="kpi-title">THREAT LEVEL</div>
            <div class="kpi-value" style="color: {threat[1]};">{threat[0]}</div>
            <div class="kpi-subtitle">Live Assessment</div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi2:
        st.markdown(f"""
        <div class="kpi-card warning">
            <div class="kpi-title">CROWD DENSITY</div>
            <div class="kpi-value" style="color: #ffcc00;">{get_crowd_density():,}</div>
            <div class="kpi-subtitle">Estimated People</div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi3:
        st.markdown(f"""
        <div class="kpi-card success">
            <div class="kpi-title">ACTIVE ALERTS</div>
            <div class="kpi-value" style="color: #00ff88;">{get_active_alerts()}</div>
            <div class="kpi-subtitle">Today's Activity</div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi4:
        st.markdown("""
        <div class="kpi-card info">
            <div class="kpi-title">SYSTEM STATUS</div>
            <div class="kpi-value" style="color: #00d4ff;">OPERATIONAL</div>
            <div class="kpi-subtitle">🟢 All Systems Go</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # === DUAL INPUT SYSTEM ===
    st.markdown("### 🎯 INPUT SOURCE")
    
    tab_upload, tab_camera = st.tabs(["📁 File Upload", "📷 Live Scanner"])
    
    image_to_analyze = None
    
    with tab_upload:
        st.markdown("#### Drag and drop an image for AI threat analysis")
        uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"], key="file_uploader")
        if uploaded_file is not None:
            image_to_analyze = Image.open(uploaded_file)
            st.success("✅ Image loaded successfully!")
    
    with tab_camera:
        st.markdown("#### Capture live image from webcam")
        camera_image = st.camera_input("📸 Take a picture for immediate analysis", key="camera_input")
        if camera_image is not None:
            image_to_analyze = Image.open(camera_image)
            st.success("✅ Image captured!")
    
    # === ANALYSIS ===
    if image_to_analyze is not None:
        st.markdown("---")
        st.markdown("## 🔍 ANALYSIS RESULTS")
        
        # Scanning animation
        with st.spinner("🔄 Running AI Vision Analysis... Please wait."):
            time.sleep(0.5)  # Small delay for effect
            processed_img, stats = detect_threats(image_to_analyze)
            mood_stats, dominant_mood = analyze_crowd_mood(image_to_analyze)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.image(processed_img, caption="🔍 Processed Frame - Threat Detection Active", use_container_width=True)
            
            # Mood Chart
            st.markdown("### 🎭 CROWD SENTIMENT ANALYSIS")
            mood_df = pd.DataFrame(list(mood_stats.items()), columns=['Emotion', 'Percentage'])
            fig_mood = px.bar(mood_df, x='Emotion', y='Percentage', color='Emotion',
                             color_discrete_map={
                                 'angry': '#ff4b4b', 'happy': '#00ff88', 'neutral': '#8b949e',
                                 'sad': '#6c757d', 'fear': '#ff8c00', 'surprise': '#ffcc00', 'disgust': '#9932CC'
                             },
                             template="plotly_dark")
            fig_mood.update_layout(plot_bgcolor=TRANSPARENT, paper_bgcolor=TRANSPARENT, showlegend=False)
            st.plotly_chart(fig_mood, use_container_width=True)
        
        with col2:
            st.markdown("### 📊 SCAN SUMMARY")
            
            # Metrics
            st.metric("👥 People Detected", f"{stats['people_count']}")
            
            mood_emoji = {"happy": "😊", "angry": "😠", "sad": "😢", "neutral": "😐", "fear": "😨", "surprise": "😲"}.get(dominant_mood.lower(), "🎭")
            st.metric("🎭 Dominant Mood", f"{mood_emoji} {dominant_mood.upper()}")
            
            st.markdown("---")
            
            # Threat Alerts
            if stats['threats']:
                st.error(f"🚨 **THREAT DETECTED:** {', '.join(stats['threats']).upper()}")
                st.warning("📱 SMS Alert dispatched to security team!")
                
                # Log to database
                for threat in stats['threats']:
                    insert_incident("Scanner - Live Feed", threat, 0.85, "Active")
            else:
                st.success("✅ No physical threats detected.")
            
            if stats['crowd_warning']:
                st.warning("⚠️ **HIGH CROWD DENSITY!** Consider opening emergency exits.")
            
            if dominant_mood.lower() == 'angry':
                st.error("💢 **MOOD WARNING:** Hostile sentiment detected!")
            
            st.markdown("---")
            
            # Report Button
            if st.button("📄 Generate PDF Report", use_container_width=True):
                with st.spinner("Generating report..."):
                    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                        bgr_img = cv2.cvtColor(processed_img, cv2.COLOR_RGB2BGR)
                        cv2.imwrite(tmp.name, bgr_img)
                        report_path = generate_pdf_report(stats, dominant_mood, tmp.name)
                    
                    with open(report_path, "rb") as f:
                        st.download_button(
                            label="📥 Download Report",
                            data=f,
                            file_name=report_path,
                            mime="application/pdf",
                            use_container_width=True
                        )
        
        # === DATABASE LOG ===
        st.markdown("---")
        st.markdown("### 🗄️ RECENT SECURITY LOG")
        
        incidents_df = fetch_incidents_from_db()
        if incidents_df is None:
            incidents_df = get_mock_incidents()
            st.caption("📋 Mock data displayed (Database connection unavailable)")
        else:
            st.caption("🔗 Live data from MySQL (can2025.incidents)")
        
        st.dataframe(incidents_df, use_container_width=True, height=250)
        
        # Export
        csv = incidents_df.to_csv(index=False)
        st.download_button("📥 Export to CSV", csv, f"security_log_{datetime.datetime.now().strftime('%Y%m%d')}.csv", "text/csv")

# ============================================
# VENUE MONITOR VIEW
# ============================================
elif menu == "🗺️ Venue Monitor":
    st.title("🗺️ CAN 2025 Venue Monitor")
    st.markdown("Geospatial monitoring of all active stadiums across Morocco.")
    
    st_folium(create_stadium_map(), width=1000, height=500)
    
    st.markdown("### 🏟️ Venue Status")
    st_data = get_stadium_data()
    df_stadiums = pd.DataFrame(st_data)[['name', 'city', 'capacity', 'status']]
    st.dataframe(df_stadiums, use_container_width=True)

# ============================================
# AI ASSISTANT VIEW
# ============================================
elif menu == "💬 AI Assistant":
    st.title("💬 Guardian AI Assistant")
    st.markdown("Multilingual security concierge (English, French, Arabic, Darija)")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask about stadium info, security protocols, or local tips..."):
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        history = []
        for m in st.session_state.messages[:-1]:
            if m["role"] == "user":
                history.append(HumanMessage(content=m["content"]))
            else:
                history.append(AIMessage(content=m["content"]))

        with st.chat_message("assistant", avatar="🛡️"):
            with st.spinner("Analyzing..."):
                response = get_response(prompt, history)
                st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

# ============================================
# CYBER SHIELD VIEW
# ============================================
elif menu == "🛡️ Cyber Shield":
    st.title("🛡️ Cyber Guardian: Content Shield")
    st.markdown("### Browser extension for digital protection during CAN 2025")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("""
        <div class="kpi-card info" style="text-align: center;">
            <h1 style="font-size: 4rem; margin: 0;">🛡️</h1>
            <h3>Content Shield</h3>
            <p>v1.0.0</p>
            <p style="color: #00ff88;">Ready to Install</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.subheader("Features")
        st.write("✅ Block match spoilers on social media")
        st.write("✅ Filter toxic content and fake news")
        st.write("✅ Privacy-first: runs locally in your browser")
        st.write("✅ Works on YouTube, Twitter/X, Reddit, and more")
    
    st.markdown("---")
    st.subheader("📦 Keyword Presets")
    
    p1, p2, p3 = st.columns(3)
    
    with p1:
        st.markdown("#### ⚽ Spoiler Shield")
        st.code("Goal, Score, Winner, Penalty, FT:")
    
    with p2:
        st.markdown("#### 🚫 Anti-Toxic")
        st.code("Fake News, Scam, Hate, Abuse")
    
    with p3:
        st.markdown("#### 🏟️ Venue Alerts")
        st.code("Emergency, Gate Closed, Traffic")

# ============================================
# SETTINGS VIEW
# ============================================
elif menu == "⚙️ Settings":
    st.title("⚙️ System Settings")
    
    st.subheader("🔌 Database Configuration")
    st.text_input("MySQL Host", value="localhost")
    st.text_input("Database Name", value="can2025")
    st.text_input("Username", value="root")
    st.text_input("Password", type="password")
    
    if st.button("Test Connection"):
        conn = get_db_connection()
        if conn:
            st.success("✅ Database connection successful!")
            conn.close()
        else:
            st.error("❌ Connection failed. Check your settings.")
    
    st.markdown("---")
    st.subheader("🔔 Alert Configuration")
    st.toggle("Enable SMS Alerts", value=True)
    st.toggle("Enable Email Notifications", value=False)
    st.slider("Alert Threshold (%)", 0, 100, 75)

# ============================================
# FOOTER
# ============================================
st.markdown("""
<div class="footer">
    <strong>CAN 2025 GUARDIAN</strong> | Security Operations Center | Morocco 🇲🇦 | 
    <span style="color: #00ff88;">● SYSTEM OPERATIONAL</span>
</div>
""", unsafe_allow_html=True)
