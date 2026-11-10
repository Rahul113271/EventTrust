"""
Multi-Modal Visual Intelligence & Cross-Modal Consistency Engine
EventTrust (TrustChain) v2.5 Architecture

Powered by Google Gemini Multi-Modal Vision AI with Local Heuristic Fallback.
Analyzes uploaded photographic evidence using state-of-the-art semantic vision models
and evaluates Cross-Modal Consistency against Natural Language Processing (NLP) predictions.
"""

import os
import io
import json
import base64
import requests
from PIL import Image, ImageStat, ImageFilter
import numpy as np

# Load GEMINI_API_KEY from .env
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, '.env')

def _load_gemini_key():
    key = os.environ.get('GEMINI_API_KEY', '')
    if not key and os.path.exists(ENV_PATH):
        try:
            with open(ENV_PATH, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('GEMINI_API_KEY='):
                        key = line.split('=', 1)[1].strip().strip('"').strip("'")
                        break
        except Exception:
            pass
    return key

GEMINI_API_KEY = _load_gemini_key()
GEMINI_MODELS = ['gemini-2.5-flash', 'gemini-3.5-flash', 'gemini-2.5-flash-lite', 'gemini-flash-latest']

def _analyze_with_gemini(raw_bytes, mime_type='image/jpeg'):
    """
    Sends photographic evidence to Google Gemini Vision API for zero-shot semantic analysis.
    Distinguishes true crisis incidents from classrooms, artwork, memes, and routine scenes.
    """
    global GEMINI_API_KEY
    if not GEMINI_API_KEY:
        GEMINI_API_KEY = _load_gemini_key()
    if not GEMINI_API_KEY:
        return None

    b64_img = base64.b64encode(raw_bytes).decode('utf-8')
    prompt = (
        "Analyze this image for crisis/disaster emergency response (e.g., floods, structural collapse, wildfire, explosion, earthquake damage).\n"
        "Determine if this image shows an actual physical disaster/emergency incident or a normal non-crisis scene (or graphic/artwork/classroom/routine).\n"
        "Respond strictly in JSON format with these exact keys:\n"
        "{\n"
        '  "is_disaster": boolean,\n'
        '  "confidence": number (between 0.0 and 1.0 or 0 to 100),\n'
        '  "scene_summary": string (1-2 sentences explaining what is depicted),\n'
        '  "detected_cues": list of strings\n'
        "}"
    )

    payload = {
        'contents': [{
            'parts': [
                {'text': prompt},
                {'inline_data': {'mime_type': mime_type, 'data': b64_img}}
            ]
        }],
        'generationConfig': {
            'response_mime_type': 'application/json'
        }
    }

    for model_name in GEMINI_MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
        try:
            r = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=12)
            if r.status_code == 200:
                data = r.json()
                text = data['candidates'][0]['content']['parts'][0]['text']
                res = json.loads(text)
                
                is_disaster = bool(res.get('is_disaster', False))
                conf = float(res.get('confidence', 0.95))
                if conf <= 1.0:
                    conf = conf * 100.0
                conf = round(min(99.0, max(60.0, conf)), 1)
                
                scene_summary = res.get('scene_summary', 'Scene analyzed by Gemini Vision')
                cues = res.get('detected_cues', [])
                
                return {
                    'has_image': True,
                    'vision_class': 'Disaster Event' if is_disaster else 'Normal Event',
                    'vision_confidence': conf,
                    'scene_summary': scene_summary,
                    'detected_cues': [scene_summary] + [f"Cue: {c}" for c in cues],
                    'metrics': {
                        'engine': f'Google Gemini Vision ({model_name})',
                        'is_disaster': is_disaster,
                        'confidence': conf
                    }
                }
            elif r.status_code == 503:
                continue # High demand, try next model
            else:
                continue
        except Exception:
            continue

    return None


def _analyze_image_heuristic(raw_bytes):
    """
    Local heuristic fallback when offline or API is unreachable.
    Inspects synthetic canvas, digital graphics, and photographic gradients.
    """
    img = Image.open(io.BytesIO(raw_bytes)).convert('RGB')
    img_thumb = img.resize((150, 150))
    img_np = np.array(img_thumb)
    total_pixels = 150 * 150

    r = img_np[:, :, 0].astype(float)
    g = img_np[:, :, 1].astype(float)
    b = img_np[:, :, 2].astype(float)

    black_bg = float(np.sum((r < 30) & (g < 30) & (b < 30))) / total_pixels
    white_bg = float(np.sum((r > 225) & (g > 225) & (b > 225))) / total_pixels

    quant = (img_np[:, :, 0] >> 3) * 1024 + (img_np[:, :, 1] >> 3) * 32 + (img_np[:, :, 2] >> 3)
    counts = np.bincount(quant.flatten())
    top_color_ratio = float(np.max(counts)) / total_pixels

    gray = img.convert('L')
    edges = gray.filter(ImageFilter.FIND_EDGES)
    edge_stat = ImageStat.Stat(edges)
    edge_variance = float(edge_stat.var[0]) if edge_stat.var else 0.0

    is_graphic_logo = (black_bg > 0.35) or (white_bg > 0.35) or (top_color_ratio > 0.30)
    is_illustration = (not is_graphic_logo) and (
        (white_bg > 0.20 and edge_variance > 800.0) or 
        (edge_variance > 1800.0 and top_color_ratio > 0.12)
    )

    if is_graphic_logo or is_illustration:
        desc = "Digital Graphic / Logo" if is_graphic_logo else "Digital Illustration / Diagram"
        return {
            'has_image': True,
            'vision_class': 'Normal Event',
            'vision_confidence': 96.0,
            'scene_summary': f'{desc} detected (non-photographic scene).',
            'detected_cues': [f'{desc} detected (synthetic canvas/sketch).'],
            'metrics': {'engine': 'Local Heuristic (Graphic Filter)'}
        }

    fire_mask = (r > 150) & (r > g * 1.20) & (r > b * 1.50) & ((r + g + b) > 260)
    fire_ratio = float(np.sum(fire_mask)) / total_pixels

    mud_mask = (r > 70) & (r < 170) & (g > 60) & (g < 150) & (b > 35) & (b < 120) & (abs(r - g) < 28) & (r >= b)
    storm_water = (r < 80) & (g < 95) & (b > 65) & (b < 125) & (b >= r)
    water_ratio = float(np.sum(mud_mask | storm_water)) / total_pixels

    is_disaster = (fire_ratio > 0.10) or (water_ratio > 0.18 and edge_variance > 350.0)
    cues = []
    if fire_ratio > 0.08:
        cues.append(f"Thermal combustion signature ({round(fire_ratio*100, 1)}% fire palette)")
    if water_ratio > 0.12:
        cues.append(f"Hydrological fluid dispersion ({round(water_ratio*100, 1)}% flood palette)")
    if not cues:
        cues.append("Routine environmental visual baseline")

    return {
        'has_image': True,
        'vision_class': 'Disaster Event' if is_disaster else 'Normal Event',
        'vision_confidence': 88.0,
        'scene_summary': 'Visual cues analyzed via local heuristic filter.',
        'detected_cues': cues,
        'metrics': {'engine': 'Local Heuristic Fallback'}
    }


def analyze_image_evidence(image_bytes_or_file):
    """
    Main entrypoint for image analysis.
    Uses Google Gemini Multi-Modal Vision first, falling back to local heuristics if offline.
    """
    if not image_bytes_or_file:
        return {
            'has_image': False,
            'vision_class': 'No Visual Attachment',
            'vision_confidence': 0.0,
            'scene_summary': 'Text-only incident report (no image provided)',
            'detected_cues': ['Text-only incident report (no image provided)'],
            'metrics': {'engine': 'None'}
        }

    try:
        if hasattr(image_bytes_or_file, 'seek'):
            image_bytes_or_file.seek(0)
        if hasattr(image_bytes_or_file, 'read'):
            raw_bytes = image_bytes_or_file.read()
            if hasattr(image_bytes_or_file, 'seek'):
                image_bytes_or_file.seek(0)
        else:
            raw_bytes = image_bytes_or_file

        # Try Google Gemini Vision AI
        gemini_res = _analyze_with_gemini(raw_bytes)
        if gemini_res:
            return gemini_res

        # Fallback to local heuristic
        return _analyze_image_heuristic(raw_bytes)

    except Exception as e:
        return {
            'has_image': True,
            'vision_class': 'Normal Event',
            'vision_confidence': 60.0,
            'scene_summary': f'Vision inspection notice: {str(e)}',
            'detected_cues': [f'Inspection notice: {str(e)}'],
            'metrics': {'engine': 'Error Handler'}
        }


def evaluate_cross_modal_consistency(text_classification, text_confidence, vision_result):
    """
    Evaluates Cross-Modal Agreement between NLP text classifier and Vision stream.
    Detects mismatched images (e.g. disaster text with a logo, artwork, or peaceful photo)
    and computes the Multi-Modal Explainable Trust adjustment.
    """
    if not vision_result.get('has_image'):
        return {
            'status': 'TEXT_ONLY',
            'badge': 'TEXT STREAM ONLY',
            'badge_color': '#3b82f6', # Blue
            'score_adjustment': 0,
            'explanation': 'Report validated via Natural Language Processing & cryptographic proof (no image attached).'
        }

    vision_class = vision_result.get('vision_class')
    text_is_disaster = ('disaster' in text_classification.lower())
    vision_is_disaster = ('disaster' in str(vision_class).lower())
    summary = vision_result.get('scene_summary', '')
    engine = vision_result.get('metrics', {}).get('engine', 'Vision AI')

    if text_is_disaster and vision_is_disaster:
        # Cross-Modal Synergy
        return {
            'status': 'SYNERGY_CONFIRMED',
            'badge': 'MULTI-MODAL VERIFIED',
            'badge_color': '#10b981', # Emerald Green
            'score_adjustment': 10,
            'explanation': f'Dual-Stream Synergy: Both Deep Learning NLP text and {engine} independently corroborate disaster incident evidence (+10 pts bonus). Scene: {summary}'
        }
    elif not text_is_disaster and not vision_is_disaster:
        # Both agree normal
        return {
            'status': 'NORMAL_CORROBORATED',
            'badge': 'ROUTINE CORROBORATED',
            'badge_color': '#06b6d4', # Cyan
            'score_adjustment': 5,
            'explanation': f'Dual-Stream Consistency: Both text and image confirm a routine, non-crisis baseline event (+5 pts). Scene: {summary}'
        }
    elif text_is_disaster and not vision_is_disaster:
        # DISCREPANCY: Text claims disaster, image is a classroom, logo, artwork, or peaceful photo
        return {
            'status': 'MEDIA_MISMATCH',
            'badge': 'MISINFORMATION ALERT (MEDIA MISMATCH)',
            'badge_color': '#ef4444', # Red
            'score_adjustment': -40,
            'explanation': f'Cross-Modal Conflict: Text claims Disaster Event, but {engine} confirms a non-disaster scene: "{summary}". High risk of fabricated alarm or irrelevant media (-40 pts penalty).'
        }
    else:
        # Text normal, image shows disaster
        return {
            'status': 'UNANNOUNCED_HAZARD',
            'badge': 'UNANNOUNCED VISUAL HAZARD',
            'badge_color': '#f59e0b', # Amber
            'score_adjustment': -15,
            'explanation': f'Discrepancy: Uploaded image exhibits disaster damage signatures not corroborated by the submitted text: "{summary}" (-15 pts).'
        }
