import folium
import pandas as pd

def get_stadium_data():
    """
    Returns data for the 6 main stadiums in Morocco for CAN 2025.
    """
    CAP_45K = "45,000"
    stadiums = [
        {"name": "Stade Mohammed V", "city": "Casablanca", "capacity": "67,000", "lat": 33.5828, "lon": -7.6483, "status": "Main Venue"},
        {"name": "Stade Moulay Abdellah", "city": "Rabat", "capacity": "65,000", "lat": 33.9592, "lon": -6.8458, "status": "High Security"},
        {"name": "Grand Stade de Tanger", "city": "Tangier", "capacity": CAP_45K, "lat": 35.7350, "lon": -5.8500, "status": "Active Monitoring"},
        {"name": "Grand Stade de Marrakech", "city": "Marrakech", "capacity": CAP_45K, "lat": 31.7058, "lon": -7.9814, "status": "Ready"},
        {"name": "Grand Stade d'Agadir", "city": "Agadir", "capacity": CAP_45K, "lat": 30.4180, "lon": -9.5350, "status": "Crowded"},
        {"name": "Complexe Sportif de Fès", "city": "Fez", "capacity": CAP_45K, "lat": 34.0044, "lon": -4.9669, "status": "Stable"}
    ]
    return stadiums

def create_stadium_map():
    """
    Creates a folium map centered on Morocco with markers for each stadium.
    """
    stadiums = get_stadium_data()
    m = folium.Map(location=[31.7917, -7.0926], zoom_start=6, tiles="CartoDB dark_matter")
    
    for s in stadiums:
        popup_html = f"""
        <div style="color: #ff4b4b; font-family: sans-serif;">
            <h4>{s['name']}</h4>
            <b>City:</b> {s['city']}<br>
            <b>Capacity:</b> {s['capacity']}<br>
            <b>Status:</b> {s['status']}
        </div>
        """
        folium.Marker(
            [s['lat'], s['lon']],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=s['name'],
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(m)
        
    return m
