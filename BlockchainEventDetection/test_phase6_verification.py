import os
import sys
import json

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Event.settings')
import django
django.setup()

from django.test import RequestFactory
from EventApp.views import verify_post_integrity, VerifyIntegrity, get_blockchain_contract
from EventApp.supabase_client import get_event, get_latest_event

def run_phase6_tests():
    print("=" * 70)
    print("PHASE 6 FOCUSED VERIFICATION TEST SUITE")
    print("=" * 70)

    web3, contract = get_blockchain_contract()
    factory = RequestFactory()
    all_passed = True

    # -------------------------------------------------------------
    # TEST A: Authentic Event Verification (Event ID = 4)
    # -------------------------------------------------------------
    print("\n--- TEST A: Authentic Event Verification ---")
    event_id = 4
    
    # Check Supabase event 4
    sb_event = get_event(event_id)
    if not sb_event:
        print(f"[FAIL] Could not retrieve Event #{event_id} from Supabase")
        return False
    print(f"[*] Supabase Event #{event_id} found:")
    print(f"    - Tweet: '{sb_event.get('tweet')}'")
    print(f"    - Classification: {sb_event.get('classification')}")
    print(f"    - Stored SHA-256: {sb_event.get('sha256_hash')}")
    print(f"    - Trust Score: {sb_event.get('trust_score')}")

    # Query blockchain getEvent(4)
    bc_hash, bc_score, bc_time, bc_by, bc_exists = contract.functions.getEvent(event_id).call()
    print(f"[*] Blockchain getEvent({event_id}):")
    print(f"    - Exists: {bc_exists}")
    print(f"    - dataHash: 0x{bc_hash.hex()}")
    print(f"    - trustScore: {bc_score}")
    print(f"    - recordedBy: {bc_by}")

    # Run verify_post_integrity(event_id=4)
    result_a = verify_post_integrity(event_id=event_id)
    print(f"[*] verify_post_integrity({event_id}) Result:")
    print(f"    - Status: {result_a['status']}")
    print(f"    - Verified: {result_a['verified']}")
    print(f"    - Trust Score: {result_a['trust_score']}")
    print(f"    - Local Hash: {result_a['local_hash']}")
    print(f"    - Blockchain Hash: {result_a['blockchain_hash']}")
    print(f"    - Message: {result_a['message']}")

    # Assertions for Test A
    test_a_pass = (
        result_a['verified'] is True and
        result_a['status'] == 'VERIFIED' and
        result_a['trust_score'] == 98 and
        result_a['local_hash'].lower() == result_a['blockchain_hash'].lower() and
        sb_event.get('sha256_hash').lower() == bc_hash.hex().lower()
    )
    
    # Test VerifyIntegrity view with event_id=4
    req_a = factory.get(f'/VerifyIntegrity?event_id={event_id}')
    resp_a = VerifyIntegrity(req_a)
    content_a = resp_a.content.decode('utf-8')
    view_a_pass = (resp_a.status_code == 200 and "VERIFIED" in content_a and f"#{event_id}" in content_a)

    if test_a_pass and view_a_pass:
        print("[PASS] TEST A: Authentic Event Verification -> VERIFIED (Trust Score = 98)")
    else:
        print(f"[FAIL] TEST A failed (test_a_pass={test_a_pass}, view_a_pass={view_a_pass})")
        all_passed = False

    # -------------------------------------------------------------
    # TEST B: Non-existent Event ID
    # -------------------------------------------------------------
    print("\n--- TEST B: Non-existent Event ID Verification ---")
    non_existent_id = 999999
    
    result_b = verify_post_integrity(event_id=non_existent_id)
    print(f"[*] verify_post_integrity({non_existent_id}) Result:")
    print(f"    - Status: {result_b['status']}")
    print(f"    - Verified: {result_b['verified']}")
    print(f"    - Trust Score: {result_b['trust_score']}")
    print(f"    - Exists: {result_b['exists']}")
    print(f"    - Message: {result_b['message']}")

    # Assertions for Test B
    test_b_pass = (
        result_b['verified'] is False and
        result_b['status'] == 'NOT ANCHORED / UNVERIFIED' and
        result_b['trust_score'] == 0 and
        result_b['exists'] is False
    )

    req_b = factory.get(f'/VerifyIntegrity?event_id={non_existent_id}')
    resp_b = VerifyIntegrity(req_b)
    content_b = resp_b.content.decode('utf-8')
    view_b_pass = (resp_b.status_code == 200 and "NOT ANCHORED / UNVERIFIED" in content_b and "0 / 100" in content_b)

    if test_b_pass and view_b_pass:
        print("[PASS] TEST B: Non-existent Event ID -> NOT ANCHORED / UNVERIFIED (Trust Score = 0)")
    else:
        print(f"[FAIL] TEST B failed (test_b_pass={test_b_pass}, view_b_pass={view_b_pass})")
        all_passed = False

    # -------------------------------------------------------------
    # TEST C: Controlled Hash Mismatch & Restoration
    # -------------------------------------------------------------
    print("\n--- TEST C: Controlled Hash Mismatch & Restoration ---")
    
    # Part C1: Payload / Database Tamper Simulation (Off-chain mismatch)
    print("\n[*] Sub-test C1: Off-chain Payload Mismatch (Tampered Tweet)")
    tampered_payload = dict(sb_event)
    tampered_payload['tweet'] = "TAMPERED: Fabricated disaster report text."
    result_c1 = verify_post_integrity(event_id=event_id, custom_event=tampered_payload)
    print(f"    - Status: {result_c1['status']}")
    print(f"    - Verified: {result_c1['verified']}")
    print(f"    - Trust Score: {result_c1['trust_score']}")
    print(f"    - Local Hash: {result_c1['local_hash']}")
    print(f"    - Blockchain Hash: {result_c1['blockchain_hash']}")

    test_c1_pass = (
        result_c1['verified'] is False and
        result_c1['status'] == 'TAMPERED / UNVERIFIED' and
        result_c1['trust_score'] == 0 and
        result_c1['local_hash'] != result_c1['blockchain_hash']
    )
    if test_c1_pass:
        print("[PASS] Sub-test C1: Off-chain Tampered Tweet -> TAMPERED / UNVERIFIED (Trust Score = 0)")
    else:
        print("[FAIL] Sub-test C1 failed")
        all_passed = False

    # Part C2: On-chain Tamper Simulation with Guaranteed Restoration
    print("\n[*] Sub-test C2: On-chain Hash Tamper & Restoration Round-trip")
    orig_hash, orig_score, _, _, _ = contract.functions.getEvent(event_id).call()
    tampered_hash_bytes = bytes.fromhex("deadbeef" * 8)
    
    try:
        print(f"    -> Calling simulateEventTampering({event_id}, 0x{tampered_hash_bytes.hex()})")
        tx_tamper = contract.functions.simulateEventTampering(event_id, tampered_hash_bytes).transact()
        web3.eth.waitForTransactionReceipt(tx_tamper)
        
        # Verify tampered status
        result_c2 = verify_post_integrity(event_id=event_id)
        print(f"    - Tampered Status: {result_c2['status']}")
        print(f"    - Tampered Verified: {result_c2['verified']}")
        print(f"    - Tampered Trust Score: {result_c2['trust_score']}")
        print(f"    - Tampered Blockchain Hash: {result_c2['blockchain_hash']}")
        
        test_c2_tamper_pass = (
            result_c2['verified'] is False and
            result_c2['status'] == 'TAMPERED / UNVERIFIED' and
            result_c2['trust_score'] == 0
        )
        if test_c2_tamper_pass:
            print("[PASS] On-chain Tamper Detection -> TAMPERED / UNVERIFIED (Trust Score = 0)")
        else:
            print("[FAIL] On-chain Tamper Detection failed")
            all_passed = False

    finally:
        # ALWAYS restore original event state on blockchain
        print(f"    -> Restoring original event state: score={orig_score}, hash=0x{orig_hash.hex()[:16]}...")
        tx_restore = contract.functions.restoreEvent(event_id, orig_hash, orig_score).transact()
        web3.eth.waitForTransactionReceipt(tx_restore)
        print("    -> Restoration transaction mined successfully.")

    # Verify post-restoration authentic state
    result_restored = verify_post_integrity(event_id=event_id)
    print(f"    - Post-Restoration Status: {result_restored['status']}")
    print(f"    - Post-Restoration Verified: {result_restored['verified']}")
    print(f"    - Post-Restoration Trust Score: {result_restored['trust_score']}")
    
    test_c2_restore_pass = (
        result_restored['verified'] is True and
        result_restored['status'] == 'VERIFIED' and
        result_restored['trust_score'] == orig_score
    )
    if test_c2_restore_pass:
        print("[PASS] Post-Restoration Integrity -> VERIFIED (Trust Score Restored to 98)")
    else:
        print("[FAIL] Post-Restoration check failed")
        all_passed = False

    # -------------------------------------------------------------
    # FINAL SUMMARY
    # -------------------------------------------------------------
    print("\n" + "=" * 70)
    if all_passed:
        print("PHASE 6 VERIFICATION SUITE: ALL TESTS PASSED (100%)")
        print("Authentic Event (ID 4): VERIFIED | Trust Score: 98")
        print("Non-existent Event (ID 999999): NOT ANCHORED / UNVERIFIED | Trust Score: 0")
        print("Tampered Event: TAMPERED / UNVERIFIED | Trust Score: 0")
        print("Restored Event: VERIFIED | Trust Score: 98 (Blockchain intact)")
    else:
        print("PHASE 6 VERIFICATION SUITE: ONE OR MORE TESTS FAILED")
    print("=" * 70)
    return all_passed

if __name__ == '__main__':
    success = run_phase6_tests()
    sys.exit(0 if success else 1)
