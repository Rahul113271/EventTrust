"""
Municipal Zone, Ward, and Geolocation Service for EventTrust
Supports city-wide spatial partitioning across Zones and Wards,
with default bounding coordinates for the metropolitan area (Mohan Babu University / Tirupati Metro).
"""

import json
import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCATIONS_FILE = os.path.join(BASE_DIR, 'event_locations.json')

# City Zones and Wards Configuration
CITY_ZONES = {
    "Zone 1 - Central Commercial": {
        "name": "Zone 1 - Central Commercial District",
        "center": [13.6350, 79.4200],
        "wards": ["Ward 01 - City Center", "Ward 02 - Market Square", "Ward 03 - Railway Hub", "Ward 04 - Bus Terminal", "Ward 05 - Financial District"],
        "default_lat": 13.6350,
        "default_lng": 79.4200,
        "color": "#38bdf8"
    },
    "Zone 2 - North Industrial": {
        "name": "Zone 2 - North Industrial Corridor",
        "center": [13.6550, 79.4300],
        "wards": ["Ward 06 - Logistics Park", "Ward 07 - Tech Valley", "Ward 08 - Heavy Industry", "Ward 09 - Substation North", "Ward 10 - North Ring Road"],
        "default_lat": 13.6550,
        "default_lng": 79.4300,
        "color": "#f59e0b"
    },
    "Zone 3 - South Education & Tech (MBU)": {
        "name": "Zone 3 - South Education & Tech Hub (MBU Campus)",
        "center": [13.6214, 79.2903],
        "wards": ["Ward 11 - University South", "Ward 12 - Nagapatla Village", "Ward 13 - Innovation Campus", "Ward 14 - Sree Sainath Nagar", "Ward 15 - Hillview Enclave"],
        "default_lat": 13.6214,
        "default_lng": 79.2903,
        "color": "#10b981"
    },
    "Zone 4 - East Residential": {
        "name": "Zone 4 - East Residential Sector",
        "center": [13.6250, 79.4450],
        "wards": ["Ward 16 - Green Meadows", "Ward 17 - East Lakefront", "Ward 18 - Sunrise Colony", "Ward 19 - Civic Gardens", "Ward 20 - Community Heights"],
        "default_lat": 13.6250,
        "default_lng": 79.4450,
        "color": "#a855f7"
    },
    "Zone 5 - West Riverfront": {
        "name": "Zone 5 - West Riverfront & Transit",
        "center": [13.6150, 79.4000],
        "wards": ["Ward 21 - Riverview", "Ward 22 - West Bypass", "Ward 23 - Heritage Quarters", "Ward 24 - Botanical Sector", "Ward 25 - Valley Gate"],
        "default_lat": 13.6150,
        "default_lng": 79.4000,
        "color": "#ec4899"
    }
}

DEFAULT_CITY_CENTER = [13.6288, 79.3500]

def load_locations_db():
    """Load persistent event location records."""
    if os.path.exists(LOCATIONS_FILE):
        try:
            with open(LOCATIONS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print("[LocationService] Warning: Error reading locations file:", e)
    return {}

def save_locations_db(db):
    """Save persistent event location records."""
    try:
        with open(LOCATIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(db, f, indent=2)
    except Exception as e:
        print("[LocationService] Warning: Error writing locations file:", e)

def record_event_location(event_id, zone, ward, latitude, longitude, reporter="Anonymous"):
    """
    Store or update location metadata for an event.
    Falls back to zone defaults if specific coordinates are not provided.
    """
    db = load_locations_db()
    
    # Resolve fallback coordinates if invalid or empty
    lat_val = None
    lng_val = None
    try:
        if latitude and str(latitude).strip():
            lat_val = float(latitude)
    except Exception:
        pass

    try:
        if longitude and str(longitude).strip():
            lng_val = float(longitude)
    except Exception:
        pass

    # If coordinates are missing, derive from zone
    if (lat_val is None or lng_val is None) and zone:
        for z_key, z_meta in CITY_ZONES.items():
            if z_key.lower() in zone.lower() or zone.lower() in z_key.lower():
                lat_val = z_meta['default_lat']
                lng_val = z_meta['default_lng']
                break

    # Ultimate fallback to default city center with slight jitter based on event_id
    if lat_val is None or lng_val is None:
        jitter = (int(event_id or 1) % 10) * 0.003
        lat_val = DEFAULT_CITY_CENTER[0] + jitter
        lng_val = DEFAULT_CITY_CENTER[1] + jitter

    resolved_zone = zone if zone else "Zone 3 - South Education & Tech (MBU)"
    resolved_ward = ward if ward else "Ward 14 - Sree Sainath Nagar"

    db[str(event_id)] = {
        "event_id": int(event_id) if str(event_id).isdigit() else event_id,
        "zone": resolved_zone,
        "ward": resolved_ward,
        "latitude": round(lat_val, 6),
        "longitude": round(lng_val, 6),
        "reporter": reporter
    }
    save_locations_db(db)
    return db[str(event_id)]

def extract_location_from_text(tweet_text):
    """
    Extract location, zone, and ward if embedded in the tweet text.
    Format: [Zone: ... | Ward: ... | Loc: lat, lng]
    """
    meta = {
        "zone": None,
        "ward": None,
        "latitude": None,
        "longitude": None
    }
    if not tweet_text:
        return meta

    zone_match = re.search(r'\[Zone:\s*([^\|\]]+)', tweet_text, re.IGNORECASE)
    if zone_match:
        meta['zone'] = zone_match.group(1).strip()

    ward_match = re.search(r'Ward:\s*([^\|\]]+)', tweet_text, re.IGNORECASE)
    if ward_match:
        meta['ward'] = ward_match.group(1).strip()

    gps_match = re.search(r'(?:Loc|GPS):\s*([0-9\.\-]+)\s*,\s*([0-9\.\-]+)', tweet_text, re.IGNORECASE)
    if gps_match:
        try:
            meta['latitude'] = float(gps_match.group(1))
            meta['longitude'] = float(gps_match.group(2))
        except Exception:
            pass

    return meta

def get_event_location(event_id, tweet_text=None):
    """Get location for a specific event."""
    db = load_locations_db()
    if str(event_id) in db:
        return db[str(event_id)]

    # Try extracting from text
    extracted = extract_location_from_text(tweet_text)
    if extracted.get('latitude') and extracted.get('longitude'):
        return record_event_location(
            event_id=event_id,
            zone=extracted.get('zone'),
            ward=extracted.get('ward'),
            latitude=extracted.get('latitude'),
            longitude=extracted.get('longitude')
        )

    # Deterministic default location for existing events based on ID
    ev_num = int(event_id) if str(event_id).isdigit() else 1
    zone_keys = list(CITY_ZONES.keys())
    zone_idx = ev_num % len(zone_keys)
    assigned_zone = zone_keys[zone_idx]
    z_meta = CITY_ZONES[assigned_zone]
    
    # Slight coordinate offset so pins don't overlap completely
    lat_offset = ((ev_num * 7) % 20 - 10) * 0.002
    lng_offset = ((ev_num * 13) % 20 - 10) * 0.002
    
    ward_list = z_meta['wards']
    assigned_ward = ward_list[ev_num % len(ward_list)]

    return record_event_location(
        event_id=event_id,
        zone=assigned_zone,
        ward=assigned_ward,
        latitude=z_meta['default_lat'] + lat_offset,
        longitude=z_meta['default_lng'] + lng_offset,
        reporter="Field Volunteer"
    )

def enrich_events_with_locations(events_list):
    """Enrich a list of event objects with zone, ward, and coordinates."""
    if not events_list:
        return []
    
    enriched = []
    for ev in events_list:
        ev_copy = dict(ev)
        loc = get_event_location(ev.get('id'), ev.get('tweet', ''))
        ev_copy['zone'] = loc['zone']
        ev_copy['ward'] = loc['ward']
        ev_copy['latitude'] = loc['latitude']
        ev_copy['longitude'] = loc['longitude']
        ev_copy['reporter'] = loc.get('reporter', ev.get('username', 'Anonymous'))
        enriched.append(ev_copy)
    return enriched

