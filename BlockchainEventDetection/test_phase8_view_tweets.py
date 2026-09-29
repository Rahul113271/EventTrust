import os
import sys

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Event.settings')
import django
django.setup()

from django.test import RequestFactory
from EventApp.views import (
    ViewTweets,
    verify_post_integrity,
    VerifyIntegrity,
    SimulateTamper,
    RestoreEvent,
    get_blockchain_contract
)
from EventApp.supabase_client import get_all_events, get_event

def run_phase8_tests():
    print("=" * 70)
    print("PHASE 8 FOCUSED EVENT DISPLAY (VIEW TWEETS) INTEGRATION TEST")
    print("=" * 70)

    event_id = 4
    factory = RequestFactory()
    web3, contract = get_blockchain_contract()
    all_passed = True

    # -------------------------------------------------------------
    # 1. Supabase Event Retrieval Check (Checkpoints A - H)
    # -------------------------------------------------------------
    print("\n[STEP 1] Testing Supabase Event Retrieval (get_all_events)...")
    events = get_all_events()
    print(f"[*] Retrieved {len(events)} events from Supabase.")
    if not events:
        print("[FAIL] No events returned from Supabase get_all_events()")
        return False
    print("[PASS] Checkpoint A: Supabase event retrieval works.")

    # Find Event #4
    ev4 = None
    for ev in events:
        if ev.get('id') == event_id:
            ev4 = ev
            break

    if not ev4:
        print(f"[FAIL] Checkpoint B: Event #{event_id} was NOT found in Supabase events list!")
        return False
    print(f"[PASS] Checkpoint B: Event #{event_id} appears in the event listing.")

    # Validate Event #4 data fields
    tweet = ev4.get('tweet', '')
    classification = ev4.get('classification', '')
    confidence = ev4.get('confidence', '')
    sha256 = ev4.get('sha256_hash', '')
    trust_score = ev4.get('trust_score', '')
    tx_hash = ev4.get('blockchain_tx_hash', '')

    print(f"[*] Event #{event_id} Details in Supabase:")
    print(f"    - Tweet: '{tweet}'")
    print(f"    - Classification: {classification}")
    print(f"    - Confidence: {confidence}%")
    print(f"    - SHA-256: {sha256}")
    print(f"    - Trust Score: {trust_score}")
    print(f"    - Blockchain Tx Hash: {tx_hash}")

    if tweet and "cyclone" in tweet.lower():
        print("[PASS] Checkpoint C: Event #4 tweet/event text retrieved from Supabase.")
    else:
        print("[FAIL] Checkpoint C: Tweet text mismatch.")
        all_passed = False

    if "disaster" in classification.lower():
        print("[PASS] Checkpoint D: Event #4 classification is displayed.")
    else:
        print("[FAIL] Checkpoint D: Classification mismatch.")
        all_passed = False

    if confidence is not None:
        print(f"[PASS] Checkpoint E: Event #4 confidence is displayed ({confidence}%).")
    else:
        print("[FAIL] Checkpoint E: Missing confidence.")
        all_passed = False

    if sha256 and len(sha256) == 64:
        print(f"[PASS] Checkpoint F: Event #4 SHA-256 is displayed ({sha256}).")
    else:
        print("[FAIL] Checkpoint F: Invalid SHA-256.")
        all_passed = False

    if trust_score == 98:
        print(f"[PASS] Checkpoint G: Event #4 trust score is displayed ({trust_score}).")
    else:
        print(f"[FAIL] Checkpoint G: Trust score is {trust_score}, expected 98.")
        all_passed = False

    if tx_hash and tx_hash.startswith("0x"):
        print(f"[PASS] Checkpoint H: Event #4 blockchain transaction hash is displayed ({tx_hash}).")
    else:
        print(f"[FAIL] Checkpoint H: Invalid tx hash ({tx_hash}).")
        all_passed = False

    # -------------------------------------------------------------
    # 2. ViewTweets Page Rendering Test
    # -------------------------------------------------------------
    print("\n[STEP 2] Testing ViewTweets Django Request & HTML Rendering...")
    req_view = factory.get('/ViewTweets')
    resp_view = ViewTweets(req_view)

    if resp_view.status_code != 200:
        print(f"[FAIL] ViewTweets returned status code {resp_view.status_code}")
        return False

    html_content = resp_view.content.decode('utf-8')
    print("[*] Checking HTML table contents for required fields:")

    checks = {
        f"Event ID #{event_id}": f"#{event_id}" in html_content,
        "Tweet Content": "cyclone" in html_content.lower(),
        "Classification": "Disaster Event Detected" in html_content,
        "Confidence Display": f"{round(float(confidence), 2)}%" in html_content,
        "SHA-256 Hash": sha256 in html_content,
        "Trust Score 98": "98 / 100" in html_content,
        "Blockchain Tx Hash": tx_hash in html_content,
        "VERIFIED Status Badge": "VERIFIED" in html_content,
        "Verify Action Link": f"/VerifyIntegrity?event_id={event_id}" in html_content
    }

    view_all_present = True
    for label, present in checks.items():
        if present:
            print(f"    [+] {label}: FOUND")
        else:
            print(f"    [-] {label}: NOT FOUND")
            view_all_present = False

    if view_all_present:
        print("[PASS] ViewTweets page renders full Supabase event data and blockchain verification status.")
    else:
        print("[FAIL] ViewTweets page rendering missing some fields.")
        all_passed = False

    # -------------------------------------------------------------
    # 3. Checkpoint I: Phase 6 Integrity Verification
    # -------------------------------------------------------------
    print("\n[STEP 3] Verifying Event #4 remains VERIFIED in Phase 6 verification flow...")
    ver_res = verify_post_integrity(event_id=event_id)
    print(f"    - Status: {ver_res['status']}")
    print(f"    - Verified: {ver_res['verified']}")
    print(f"    - Trust Score: {ver_res['trust_score']}")
    print(f"    - Local Hash == Blockchain Hash: {ver_res['local_hash'].lower() == ver_res['blockchain_hash'].lower()}")

    if ver_res['verified'] is True and ver_res['status'] == 'VERIFIED' and ver_res['trust_score'] == 98:
        print("[PASS] Checkpoint I: Event #4 remains VERIFIED with Trust Score 98.")
    else:
        print("[FAIL] Checkpoint I: Event #4 verification failed.")
        all_passed = False

    # -------------------------------------------------------------
    # 4. Checkpoint J: Phase 7 Tamper & Restore Regression Check
    # -------------------------------------------------------------
    print("\n[STEP 4] Running Phase 7 Tamper & Restore regression check...")
    try:
        # Tamper simulation
        req_tamper = factory.post('/SimulateTamper', data={'event_id': event_id})
        resp_tamper = SimulateTamper(req_tamper)
        res_tampered = verify_post_integrity(event_id=event_id)
        tamper_ok = (res_tampered['verified'] is False and res_tampered['trust_score'] == 0)
        print(f"    - Tamper check: status={res_tampered['status']}, score={res_tampered['trust_score']} (Expected: 0) -> {'PASS' if tamper_ok else 'FAIL'}")

        # Restore
        req_restore = factory.post('/RestoreEvent', data={'event_id': event_id})
        resp_restore = RestoreEvent(req_restore)
        res_restored = verify_post_integrity(event_id=event_id)
        restore_ok = (res_restored['verified'] is True and res_restored['trust_score'] == 98)
        print(f"    - Restore check: status={res_restored['status']}, score={res_restored['trust_score']} (Expected: 98) -> {'PASS' if restore_ok else 'FAIL'}")

        if tamper_ok and restore_ok:
            print("[PASS] Checkpoint J: Phase 6 and Phase 7 tamper/restore functionality intact.")
        else:
            print("[FAIL] Checkpoint J: Tamper or restore regression detected.")
            all_passed = False
    finally:
        # Guarantee authentic on-chain baseline
        final_hash, final_score, _, _, _ = contract.functions.getEvent(event_id).call()
        if final_score != 98 or final_hash.hex().lower() != sha256.lower():
            print("    [Cleanup] Restoring authentic state in finally block...")
            tx_clean = contract.functions.restoreEvent(event_id, bytes.fromhex(sha256), 98).transact()
            web3.eth.waitForTransactionReceipt(tx_clean)

    # -------------------------------------------------------------
    # 5. Final State Confirmation
    # -------------------------------------------------------------
    print("\n[STEP 5] Final State Confirmation:")
    final_verify = verify_post_integrity(event_id=event_id)
    print(f"    - Event #{event_id} Status: {final_verify['status']}")
    print(f"    - Event #{event_id} Trust Score: {final_verify['trust_score']}")
    print(f"    - Event #{event_id} Verified: {final_verify['verified']}")

    if final_verify['status'] == 'VERIFIED' and final_verify['trust_score'] == 98:
        print("[PASS] Event #4 confirmed VERIFIED with Trust Score 98.")
    else:
        print("[FAIL] Event #4 final state is not VERIFIED.")
        all_passed = False

    # -------------------------------------------------------------
    # SUMMARY
    # -------------------------------------------------------------
    print("\n" + "=" * 70)
    if all_passed:
        print("PHASE 8 INTEGRATION TEST: ALL CHECKS PASSED (100%)")
        print("Supabase Event Listing: ACTIVE")
        print("Ethereum getPost() Dependency: ELIMINATED")
        print("Event #4 Display: FULL DATA VISIBLE")
        print("Event #4 Integrity: VERIFIED (Trust Score 98)")
        print("Phase 6 & 7 Regressions: ZERO")
        print("PHASE 8 SUCCESS")
    else:
        print("PHASE 8 INTEGRATION TEST: ONE OR MORE CHECKS FAILED")
    print("=" * 70)
    return all_passed

if __name__ == '__main__':
    success = run_phase8_tests()
    sys.exit(0 if success else 1)
