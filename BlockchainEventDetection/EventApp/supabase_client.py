import os
import requests

# Base directory for loading .env safely without external dependencies
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, '.env')

def _load_env_config():
    """Load SUPABASE_URL, SUPABASE_KEY, and optional SUPABASE_SERVICE_ROLE_KEY from .env file securely."""
    config = {
        'SUPABASE_URL': os.environ.get('SUPABASE_URL', ''),
        'SUPABASE_KEY': os.environ.get('SUPABASE_KEY', ''),
        'SUPABASE_SERVICE_ROLE_KEY': os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')
    }
    if os.path.exists(ENV_PATH):
        try:
            with open(ENV_PATH, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        k, v = line.split('=', 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k in config and not config[k]:
                            config[k] = v
        except Exception as e:
            print("[Supabase Client] Warning: Error reading .env file:", e)
    return config

_ENV = _load_env_config()
SUPABASE_URL = _ENV.get('SUPABASE_URL', '').rstrip('/')
SUPABASE_KEY = _ENV.get('SUPABASE_KEY', '')
SUPABASE_SERVICE_ROLE_KEY = _ENV.get('SUPABASE_SERVICE_ROLE_KEY', '')
TIMEOUT_SECONDS = 5

def _get_storage_key():
    """Return service_role key if available for backend uploads, otherwise publishable key."""
    global SUPABASE_SERVICE_ROLE_KEY
    if not SUPABASE_SERVICE_ROLE_KEY:
        cfg = _load_env_config()
        if cfg.get('SUPABASE_SERVICE_ROLE_KEY'):
            SUPABASE_SERVICE_ROLE_KEY = cfg['SUPABASE_SERVICE_ROLE_KEY']
    return SUPABASE_SERVICE_ROLE_KEY if SUPABASE_SERVICE_ROLE_KEY else SUPABASE_KEY

def _get_headers():
    """Generate headers required for Supabase PostgREST REST API."""
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": "Bearer {}".format(SUPABASE_KEY),
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

def test_connection():
    """
    Non-destructive health-check.
    Tests GET access to public.users and public.events endpoints.
    Does not insert, update, or delete any records.
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        return {
            'success': False,
            'users_status': None,
            'events_status': None,
            'error': 'Missing SUPABASE_URL or SUPABASE_KEY in .env configuration.'
        }
    
    headers = _get_headers()
    res = {
        'success': False,
        'users_status': None,
        'events_status': None,
        'error': None
    }
    
    try:
        # Test GET on users
        users_url = "{}/rest/v1/users?select=id&limit=1".format(SUPABASE_URL)
        r_users = requests.get(users_url, headers=headers, timeout=TIMEOUT_SECONDS)
        res['users_status'] = r_users.status_code
        
        # Test GET on events
        events_url = "{}/rest/v1/events?select=id&limit=1".format(SUPABASE_URL)
        r_events = requests.get(events_url, headers=headers, timeout=TIMEOUT_SECONDS)
        res['events_status'] = r_events.status_code
        
        if (200 <= r_users.status_code < 300) and (200 <= r_events.status_code < 300):
            res['success'] = True
        else:
            errors = []
            if not (200 <= r_users.status_code < 300):
                errors.append("Users endpoint returned HTTP {}".format(r_users.status_code))
            if not (200 <= r_events.status_code < 300):
                errors.append("Events endpoint returned HTTP {}".format(r_events.status_code))
            res['error'] = "; ".join(errors)
            
    except requests.exceptions.Timeout:
        res['error'] = "Connection timed out after {} seconds.".format(TIMEOUT_SECONDS)
    except requests.exceptions.RequestException as e:
        res['error'] = "Request error: {}".format(str(e))
    except Exception as e:
        res['error'] = "Unexpected error: {}".format(str(e))
        
    return res

def insert_user(username, email=None, contact=None, address=None):
    """
    Insert a user profile into public.users.
    Plaintext passwords are NOT accepted or stored.
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        return {'success': False, 'error': 'Missing Supabase credentials.'}
    
    payload = {'username': username}
    if email:
        payload['email'] = email
    if contact:
        payload['contact'] = contact
    if address:
        payload['address'] = address
        
    url = "{}/rest/v1/users".format(SUPABASE_URL)
    headers = _get_headers()
    
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=TIMEOUT_SECONDS)
        if 200 <= r.status_code < 300:
            data = r.json()
            return {'success': True, 'data': data[0] if isinstance(data, list) and data else data}
        else:
            return {'success': False, 'status_code': r.status_code, 'error': r.text}
    except requests.exceptions.RequestException as e:
        return {'success': False, 'error': str(e)}

def upload_event_image(file_data, filename, content_type='image/jpeg', bucket_name='event-images'):
    """
    Upload an event image to Supabase Storage bucket 'event-images'.
    Parameters:
      - file_data: bytes or file-like object
      - filename: unique object key (e.g. evt_abc123_photo.jpg)
      - content_type: MIME type (e.g. 'image/jpeg', 'image/png', 'image/webp')
      - bucket_name: Supabase Storage bucket name (default: 'event-images')
    Returns:
      dict with {'success': True, 'image_url': '...', 'image_path': '...'} or {'success': False, 'error': '...'}
    """
    if not SUPABASE_URL:
        return {'success': False, 'error': 'Missing SUPABASE_URL configuration.'}

    storage_key = _get_storage_key()
    if not storage_key:
        return {'success': False, 'error': 'Missing Supabase API key.'}

    url = "{}/storage/v1/object/{}/{}".format(SUPABASE_URL, bucket_name, filename)
    headers = {
        "apikey": storage_key,
        "Authorization": "Bearer {}".format(storage_key),
        "Content-Type": content_type,
        "x-upsert": "true"
    }

    try:
        if hasattr(file_data, 'seek'):
            try:
                file_data.seek(0)
            except Exception:
                pass
        if hasattr(file_data, 'read'):
            payload = file_data.read()
        else:
            payload = file_data

        r = requests.post(url, headers=headers, data=payload, timeout=10)
        if 200 <= r.status_code < 300:
            public_url = "{}/storage/v1/object/public/{}/{}".format(SUPABASE_URL, bucket_name, filename)
            return {
                'success': True,
                'image_url': public_url,
                'image_path': "{}/{}".format(bucket_name, filename)
            }
        else:
            return {
                'success': False,
                'status_code': r.status_code,
                'error': "Storage upload failed (HTTP {}): {}".format(r.status_code, r.text)
            }
    except requests.exceptions.RequestException as e:
        return {'success': False, 'error': "Network error during image upload: {}".format(str(e))}
    except Exception as e:
        return {'success': False, 'error': "Unexpected error during image upload: {}".format(str(e))}

def insert_event(username, tweet, classification, confidence, event_date, sha256_hash, trust_score, blockchain_tx_hash=None, user_id=None, image_url=None):
    """
    Insert a structured event record into public.events.
    Stores application metadata, ML predictions, blockchain transaction references,
    and optional image_url in Supabase Storage.
    Existing calls without image_url continue working seamlessly.
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        return {'success': False, 'error': 'Missing Supabase credentials.'}
        
    # Clean sha256_hash to strictly fit VARCHAR(64)
    clean_sha = str(sha256_hash)
    if clean_sha.startswith('0x'):
        clean_sha = clean_sha[2:]
    clean_sha = clean_sha[:64]

    payload = {
        'username': username,
        'tweet': tweet,
        'classification': classification,
        'confidence': round(float(confidence), 2),
        'event_date': str(event_date),
        'sha256_hash': clean_sha,
        'trust_score': int(trust_score)
    }
    if blockchain_tx_hash:
        payload['blockchain_tx_hash'] = str(blockchain_tx_hash)[:66]
    if user_id is not None:
        payload['user_id'] = user_id
    if image_url:
        payload['image_url'] = str(image_url)
        
    url = "{}/rest/v1/events".format(SUPABASE_URL)
    headers = _get_headers()
    
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=TIMEOUT_SECONDS)
        if 200 <= r.status_code < 300:
            data = r.json()
            return {'success': True, 'data': data[0] if isinstance(data, list) and data else data}
        else:
            return {'success': False, 'status_code': r.status_code, 'error': r.text}
    except requests.exceptions.RequestException as e:
        return {'success': False, 'error': str(e)}

def get_latest_event():
    """Fetch the latest event record ordered by created_at descending."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
        
    url = "{}/rest/v1/events?order=created_at.desc&limit=1".format(SUPABASE_URL)
    headers = _get_headers()
    
    try:
        r = requests.get(url, headers=headers, timeout=TIMEOUT_SECONDS)
        if 200 <= r.status_code < 300:
            data = r.json()
            if isinstance(data, list) and len(data) > 0:
                return data[0]
        return None
    except Exception as e:
        print("[Supabase Client] Error fetching latest event:", e)
        return None

def get_event(event_id):
    """Fetch a specific event record by ID."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
        
    url = "{}/rest/v1/events?id=eq.{}&limit=1".format(SUPABASE_URL, event_id)
    headers = _get_headers()
    
    try:
        r = requests.get(url, headers=headers, timeout=TIMEOUT_SECONDS)
        if 200 <= r.status_code < 300:
            data = r.json()
            if isinstance(data, list) and len(data) > 0:
                return data[0]
        return None
    except Exception as e:
        print("[Supabase Client] Error fetching event {}:".format(event_id), e)
        return None

def get_all_events():
    """Fetch all events ordered by created_at descending."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return []
    url = "{}/rest/v1/events?order=created_at.desc".format(SUPABASE_URL)
    headers = _get_headers()
    try:
        r = requests.get(url, headers=headers, timeout=TIMEOUT_SECONDS)
        if 200 <= r.status_code < 300:
            data = r.json()
            if isinstance(data, list):
                return data
        return []
    except Exception as e:
        print("[Supabase Client] Error fetching all events:", e)
        return []

def update_event_tx_hash(event_id, blockchain_tx_hash):
    """Update an existing event record with its Ethereum transaction hash."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return {'success': False, 'error': 'Missing Supabase credentials.'}
    url = "{}/rest/v1/events?id=eq.{}".format(SUPABASE_URL, event_id)
    headers = _get_headers()
    payload = {'blockchain_tx_hash': str(blockchain_tx_hash)[:66]}
    try:
        r = requests.patch(url, headers=headers, json=payload, timeout=TIMEOUT_SECONDS)
        if 200 <= r.status_code < 300:
            return {'success': True}
        return {'success': False, 'status_code': r.status_code, 'error': r.text}
    except Exception as e:
        return {'success': False, 'error': str(e)}

