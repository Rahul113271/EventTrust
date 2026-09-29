import os
import sys
import io
import time
import requests

# Setup Django test environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Event.settings')
import django
django.setup()

from django.test import RequestFactory
from django.core.files.uploadedfile import SimpleUploadedFile
from EventApp.views import (
    PredictAction,
    ViewTweets,
    VerifyIntegrity,
    SimulateTamper,
    RestoreEvent,
    get_blockchain_contract,
    verify_post_integrity
)
from EventApp.supabase_client import (
    get_event,
    get_latest_event,
    get_all_events,
    upload_event_image,
    insert_event,
    test_connection
)

# Minimal valid 1x1 PNG bytes
MINIMAL_PNG_BYTES = (
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
    b'\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc`\x00\x00\x00'
    b'\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82'
)

# Minimal valid 1x1 JPEG bytes
MINIMAL_JPG_BYTES = (
    b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00'
    b'\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19'
    b'\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' \",#\x1c\x1c(7),01444\x1f\'9'
    b'=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00'
    b'\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03'
    b'\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9'
)

def run_phase10_tests():
    print("=" * 75)
    print("PHASE 10 — OPTIONAL EVENT IMAGE UPLOAD VERIFICATION SUITE")
    print("=" * 75)

    factory = RequestFactory()
    web3, contract = get_blockchain_contract()
    results = {}
    all_passed = True

    # =========================================================================
    # TEST A: Django system check passes
    # =========================================================================
    print("\n--- TEST A: Django System Check ---")
    try:
        from django.core.management import call_command
        call_command('check')
        print("[PASS] TEST A: Django system check passed with 0 errors.")
        results['Test A'] = 'PASS'
    except Exception as e:
        print(f"[FAIL] TEST A: Django check failed: {e}")
        results['Test A'] = f'FAIL: {e}'
        all_passed = False

    # =========================================================================
    # TEST B: Existing event flow without an image still works
    # =========================================================================
    print("\n--- TEST B: Existing Event Flow Without Image ---")
    no_img_event_id = None
    try:
        text_b = "PHASE 10 TEST: Standard traffic flow smoothly moving across city center with clear weather conditions."
        req_b = factory.post('/PredictAction', data={'t1': text_b})
        resp_b = PredictAction(req_b)
        content_b = resp_b.content.decode('utf-8')
        latest_b = get_latest_event()
        no_img_event_id = latest_b.get('id') if latest_b else None

        ev4 = get_event(4)
        ev5 = get_event(5)

        cond_b = (
            resp_b.status_code == 200 and
            ("Event Detected" in content_b or "Event Anchored" in content_b) and
            latest_b and
            latest_b.get('blockchain_tx_hash') and
            ev4 and ev4.get('id') == 4 and
            ev5 and ev5.get('id') == 5
        )

        if cond_b:
            print(f"[*] Created Event #{no_img_event_id} without image. Tx: {latest_b.get('blockchain_tx_hash')}")
            print(f"[*] Verified Event #4 (Trust: {ev4.get('trust_score')}) and Event #5 (Trust: {ev5.get('trust_score')}) intact.")
            print("[PASS] TEST B: Existing event flow without image operates successfully.")
            results['Test B'] = 'PASS'
        else:
            print(f"[FAIL] TEST B: Submission without image failed. Status: {resp_b.status_code}")
            results['Test B'] = 'FAIL'
            all_passed = False
    except Exception as e:
        print(f"[FAIL] TEST B: Exception during test: {e}")
        results['Test B'] = f'FAIL: {e}'
        all_passed = False

    # =========================================================================
    # TEST C: Valid JPG/PNG/WEBP image is accepted
    # =========================================================================
    print("\n--- TEST C: Valid Image Upload Accepted ---")
    img_event_id = None
    uploaded_image_url = None
    try:
        valid_jpg = SimpleUploadedFile(
            "disaster_report.jpg",
            MINIMAL_JPG_BYTES,
            content_type="image/jpeg"
        )
        text_c = "EMERGENCY ALERT: Severe flash flood inundating low lying sectors with rising waters."
        req_c = factory.post('/PredictAction', data={
            't1': text_c,
            'event_image': valid_jpg
        })
        resp_c = PredictAction(req_c)
        content_c = resp_c.content.decode('utf-8')
        latest_c = get_latest_event()

        if resp_c.status_code == 200 and latest_c and latest_c.get('image_url'):
            img_event_id = latest_c.get('id')
            uploaded_image_url = latest_c.get('image_url')
            print(f"[*] Created Event #{img_event_id} with attached image.")
            print(f"[*] image_url: {uploaded_image_url}")
            print("[PASS] TEST C: Valid JPG image accepted and associated with event.")
            results['Test C'] = 'PASS'
        else:
            print(f"[FAIL] TEST C: Image upload was not accepted. Response status: {resp_c.status_code}")
            results['Test C'] = 'FAIL'
            all_passed = False
    except Exception as e:
        print(f"[FAIL] TEST C: Exception during test: {e}")
        results['Test C'] = f'FAIL: {e}'
        all_passed = False

    # =========================================================================
    # TEST D: Invalid file type is rejected
    # =========================================================================
    print("\n--- TEST D: Invalid File Type Rejection ---")
    try:
        invalid_file = SimpleUploadedFile(
            "malicious_script.exe",
            b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff",
            content_type="application/octet-stream"
        )
        req_d = factory.post('/PredictAction', data={
            't1': 'Attempting executable upload injection test.',
            'event_image': invalid_file
        })
        resp_d = PredictAction(req_d)
        content_d = resp_d.content.decode('utf-8')

        if "Invalid file format" in content_d or "Only JPG, JPEG, PNG, and WEBP" in content_d:
            print("[PASS] TEST D: Executable file upload rejected safely with validation message.")
            results['Test D'] = 'PASS'
        else:
            print(f"[FAIL] TEST D: Expected invalid file rejection but got: {content_d[:200]}")
            results['Test D'] = 'FAIL'
            all_passed = False
    except Exception as e:
        print(f"[FAIL] TEST D: Exception during test: {e}")
        results['Test D'] = f'FAIL: {e}'
        all_passed = False

    # =========================================================================
    # TEST E: Image larger than 5 MB is rejected
    # =========================================================================
    print("\n--- TEST E: Oversized Image (>5MB) Rejection ---")
    try:
        oversized_data = b'0' * (5 * 1024 * 1024 + 200 * 1024)  # 5.2 MB
        oversized_file = SimpleUploadedFile(
            "huge_photo.jpg",
            oversized_data,
            content_type="image/jpeg"
        )
        req_e = factory.post('/PredictAction', data={
            't1': 'Attempting oversized 5.2 MB image submission.',
            'event_image': oversized_file
        })
        resp_e = PredictAction(req_e)
        content_e = resp_e.content.decode('utf-8')

        if "exceeds the maximum 5 MB limit" in content_e or "under 5 MB" in content_e:
            print("[PASS] TEST E: Oversized file (>5MB) rejected safely with validation message.")
            results['Test E'] = 'PASS'
        else:
            print(f"[FAIL] TEST E: Expected 5 MB rejection but got: {content_e[:200]}")
            results['Test E'] = 'FAIL'
            all_passed = False
    except Exception as e:
        print(f"[FAIL] TEST E: Exception during test: {e}")
        results['Test E'] = f'FAIL: {e}'
        all_passed = False

    # =========================================================================
    # TEST F: Image is uploaded through Django to Supabase Storage
    # =========================================================================
    print("\n--- TEST F: Image Upload Through Django to Storage ---")
    if uploaded_image_url:
        try:
            head_resp = requests.head(uploaded_image_url, timeout=5)
            if head_resp.status_code not in (200, 304):
                head_resp = requests.get(uploaded_image_url, timeout=5)
            
            print(f"[*] Storage accessibility check ({uploaded_image_url}): HTTP {head_resp.status_code}")
            if head_resp.status_code in (200, 206, 304):
                print("[PASS] TEST F: Image uploaded through Django is accessible in Supabase Storage.")
                results['Test F'] = 'PASS'
            else:
                print(f"[FAIL] TEST F: Image URL returned HTTP {head_resp.status_code}")
                results['Test F'] = f'FAIL: HTTP {head_resp.status_code}'
                all_passed = False
        except Exception as e:
            print(f"[FAIL] TEST F: Exception accessing image URL: {e}")
            results['Test F'] = f'FAIL: {e}'
            all_passed = False
    else:
        print("[FAIL] TEST F: No uploaded image URL available to verify.")
        results['Test F'] = 'FAIL'
        all_passed = False

    # =========================================================================
    # TEST G: events.image_url is populated for an image event
    # =========================================================================
    print("\n--- TEST G: events.image_url Populated for Image Event ---")
    if img_event_id:
        try:
            ev_g = get_event(img_event_id)
            img_val_g = ev_g.get('image_url') if ev_g else None
            if img_val_g and "event-images" in img_val_g:
                print(f"[*] Supabase Event #{img_event_id} image_url: {img_val_g}")
                print("[PASS] TEST G: events.image_url is correctly populated in Supabase.")
                results['Test G'] = 'PASS'
            else:
                print(f"[FAIL] TEST G: image_url is missing or invalid: {img_val_g}")
                results['Test G'] = 'FAIL'
                all_passed = False
        except Exception as e:
            print(f"[FAIL] TEST G: Exception checking event image_url: {e}")
            results['Test G'] = f'FAIL: {e}'
            all_passed = False
    else:
        print("[FAIL] TEST G: No test image event ID available.")
        results['Test G'] = 'FAIL'
        all_passed = False

    # =========================================================================
    # TEST H: An event without an image has image_url = NULL
    # =========================================================================
    print("\n--- TEST H: Event Without Image Has image_url = NULL ---")
    try:
        ev4 = get_event(4)
        ev5 = get_event(5)
        ev_no_img = get_event(no_img_event_id) if no_img_event_id else None

        ev4_null = ev4 and ev4.get('image_url') is None
        ev5_null = ev5 and ev5.get('image_url') is None
        new_null = ev_no_img and ev_no_img.get('image_url') is None

        print(f"[*] Event #4 image_url: {ev4.get('image_url')} (is None: {ev4_null})")
        print(f"[*] Event #5 image_url: {ev5.get('image_url')} (is None: {ev5_null})")
        if ev_no_img:
            print(f"[*] Event #{no_img_event_id} image_url: {ev_no_img.get('image_url')} (is None: {new_null})")

        if ev4_null and ev5_null and (new_null or no_img_event_id is None):
            print("[PASS] TEST H: Events without images correctly retain image_url = NULL.")
            results['Test H'] = 'PASS'
        else:
            print("[FAIL] TEST H: Non-image event has unexpected non-null image_url.")
            results['Test H'] = 'FAIL'
            all_passed = False
    except Exception as e:
        print(f"[FAIL] TEST H: Exception in Test H: {e}")
        results['Test H'] = f'FAIL: {e}'
        all_passed = False

    # =========================================================================
    # TEST I: Existing SHA-256 formula remains unchanged
    # =========================================================================
    print("\n--- TEST I: Existing SHA-256 Formula Unchanged ---")
    try:
        import hashlib
        target_ev = get_event(img_event_id) if img_event_id else get_event(4)
        u = target_ev.get('username')
        t = target_ev.get('tweet')
        d = str(target_ev.get('event_date'))
        c = target_ev.get('classification')
        expected_raw = f"{u}${t}${d}${c}\n"
        expected_hash = hashlib.sha256(expected_raw.encode('utf-8')).hexdigest().lower()
        actual_hash = str(target_ev.get('sha256_hash')).lower().replace('0x', '')

        hash_matches = (expected_hash == actual_hash)
        print(f"[*] Raw input payload (excludes image): '{expected_raw.strip()}'")
        print(f"[*] Expected SHA-256: {expected_hash}")
        print(f"[*] Stored SHA-256:   {actual_hash}")

        if hash_matches:
            print("[PASS] TEST I: Existing SHA-256 formula strictly unchanged and verified.")
            results['Test I'] = 'PASS'
        else:
            print("[FAIL] TEST I: SHA-256 hash mismatch.")
            results['Test I'] = 'FAIL'
            all_passed = False
    except Exception as e:
        print(f"[FAIL] TEST I: Exception checking SHA-256: {e}")
        results['Test I'] = f'FAIL: {e}'
        all_passed = False

    # =========================================================================
    # TEST J: Existing blockchain anchoring still works
    # =========================================================================
    print("\n--- TEST J: Existing Blockchain Anchoring ---")
    try:
        anchor_id = img_event_id or no_img_event_id or 4
        ev_j = get_event(anchor_id)
        bc_hash, bc_score, ts, rec_by, exists = contract.functions.getEvent(int(anchor_id)).call()
        sb_hash = ev_j.get('sha256_hash').lower().replace('0x', '')
        bc_hash_clean = bc_hash.hex().lower()

        anchored_ok = (
            exists is True and
            bc_hash_clean == sb_hash and
            bc_score == ev_j.get('trust_score') and
            ev_j.get('blockchain_tx_hash') is not None
        )

        print(f"[*] Ethereum getEvent({anchor_id}): exists={exists}, dataHash=0x{bc_hash_clean}, trustScore={bc_score}")
        print(f"[*] Supabase Event #{anchor_id}: sha256={sb_hash}, trustScore={ev_j.get('trust_score')}, tx={ev_j.get('blockchain_tx_hash')}")

        if anchored_ok:
            print(f"[PASS] TEST J: Event #{anchor_id} blockchain anchoring successfully verified on Ethereum.")
            results['Test J'] = 'PASS'
        else:
            print("[FAIL] TEST J: Blockchain anchoring verification mismatch.")
            results['Test J'] = 'FAIL'
            all_passed = False
    except Exception as e:
        print(f"[FAIL] TEST J: Exception checking blockchain anchoring: {e}")
        results['Test J'] = f'FAIL: {e}'
        all_passed = False

    # =========================================================================
    # TEST K: Existing integrity verification still works
    # =========================================================================
    print("\n--- TEST K: Existing Integrity Verification ---")
    try:
        check_id = img_event_id or no_img_event_id or 4
        res_k = verify_post_integrity(event_id=check_id)
        req_k = factory.get(f'/VerifyIntegrity?event_id={check_id}')
        resp_k = VerifyIntegrity(req_k)
        html_k = resp_k.content.decode('utf-8')

        integrity_ok = (
            res_k['verified'] is True and
            res_k['status'] == 'VERIFIED' and
            resp_k.status_code == 200 and
            "VERIFIED" in html_k
        )

        print(f"[*] verify_post_integrity({check_id}) -> Verified: {res_k['verified']}, Status: {res_k['status']}, Score: {res_k['trust_score']}")
        if integrity_ok:
            print(f"[PASS] TEST K: Integrity verification confirmed VERIFIED for Event #{check_id}.")
            results['Test K'] = 'PASS'
        else:
            print(f"[FAIL] TEST K: Integrity check returned unverified.")
            results['Test K'] = 'FAIL'
            all_passed = False
    except Exception as e:
        print(f"[FAIL] TEST K: Exception checking integrity verification: {e}")
        results['Test K'] = f'FAIL: {e}'
        all_passed = False

    # =========================================================================
    # TEST L: Existing Phase 5–9 functionality is not broken
    # =========================================================================
    print("\n--- TEST L: Existing Phase 5–9 Functionality Preserved ---")
    try:
        # 1. Check Event #4 remains VERIFIED with 98 / 100
        ev4_final = get_event(4)
        h4, s4, _, _, ex4 = contract.functions.getEvent(4).call()
        sb4_sha = ev4_final.get('sha256_hash').lower().replace('0x', '')
        bc4_sha = h4.hex().lower()

        ev4_intact = (
            ex4 is True and
            s4 == 98 and
            ev4_final.get('trust_score') == 98 and
            bc4_sha == sb4_sha and
            ev4_final.get('image_url') is None
        )

        # 2. Check Tamper simulation & restoration on a test event
        test_tamp_id = img_event_id or no_img_event_id
        tamper_pass = True
        restore_pass = True
        if test_tamp_id:
            req_tamp = factory.post('/SimulateTamper', data={'event_id': test_tamp_id})
            resp_tamp = SimulateTamper(req_tamp)
            ver_tamp = verify_post_integrity(event_id=test_tamp_id)
            tamper_pass = (resp_tamp.status_code in (200, 302) and ver_tamp.get('trust_score') == 0)

            req_rest = factory.post('/RestoreEvent', data={'event_id': test_tamp_id})
            resp_rest = RestoreEvent(req_rest)
            ver_rest = verify_post_integrity(event_id=test_tamp_id)
            restore_pass = (resp_rest.status_code in (200, 302) and ver_rest.get('verified') is True)

        # 3. Check ViewTweets renders table with fallback for legacy events
        req_vt = factory.get('/ViewTweets')
        resp_vt = ViewTweets(req_vt)
        html_vt = resp_vt.content.decode('utf-8')
        vt_ok = (resp_vt.status_code == 200 and "No image" in html_vt and "#4" in html_vt)

        phase_all_ok = ev4_intact and tamper_pass and restore_pass and vt_ok

        print(f"[*] Event #4 Intact: {ev4_intact} (Score: {s4}/100, Verified: {bc4_sha == sb4_sha})")
        print(f"[*] Tamper Simulation on #{test_tamp_id}: {tamper_pass}")
        print(f"[*] Restoration on #{test_tamp_id}: {restore_pass}")
        print(f"[*] ViewTweets Rendering: {vt_ok}")

        if phase_all_ok:
            print("[PASS] TEST L: All existing Phase 5–9 features operate normally without regression.")
            results['Test L'] = 'PASS'
        else:
            print("[FAIL] TEST L: Regression detected in Phase 5–9 functionality.")
            results['Test L'] = 'FAIL'
            all_passed = False
    except Exception as e:
        print(f"[FAIL] TEST L: Exception checking Phase 5–9 regression: {e}")
        results['Test L'] = f'FAIL: {e}'
        all_passed = False

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("\n" + "=" * 75)
    print("PHASE 10 TEST RESULTS (A – L)")
    print("=" * 75)
    for test_key, outcome in results.items():
        print(f"{test_key:10} : {outcome}")
    print("=" * 75)
    print(f"OVERALL STATUS: {'ALL TESTS PASSED (12/12)' if all_passed else 'SOME TESTS FAILED'}")
    print("=" * 75)
    return all_passed

if __name__ == '__main__':
    success = run_phase10_tests()
    sys.exit(0 if success else 1)
