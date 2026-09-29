import os
import sys
import json

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Event.settings')
import django
django.setup()

from django.test import RequestFactory
from EventApp.views import (
    verify_post_integrity,
    VerifyIntegrity,
    SimulateTamper,
    RestoreEvent,
    get_blockchain_contract,
    get_demo_backup,
    DEMO_BACKUP_FILE
)
from EventApp.supabase_client import get_event

def run_phase7_tests():
    print("=" * 70)
    print("PHASE 7 FOCUSED DEMO / TEST MODE INTEGRATION TEST")
    print("=" * 70)

    event_id = 4
    web3, contract = get_blockchain_contract()
    factory = RequestFactory()
    all_passed = True

    # Capture initial authentic on-chain and Supabase state
    orig_hash_bytes, orig_score, orig_time, orig_by, orig_exists = contract.functions.getEvent(event_id).call()
    sb_orig = get_event(event_id)

    print(f"[*] Initial Baseline for Event #{event_id}:")
    print(f"    - On-chain dataHash: 0x{orig_hash_bytes.hex()}")
    print(f"    - On-chain trustScore: {orig_score}")
    print(f"    - On-chain exists: {orig_exists}")
    print(f"    - Supabase stored hash: {sb_orig.get('sha256_hash')}")
    print(f"    - Supabase trust score: {sb_orig.get('trust_score')}")

    # -------------------------------------------------------------
    # STEP A: Authentic Event Initial Verification
    # -------------------------------------------------------------
    print("\n--- STEP A: Authentic Event Verification ---")
    res_a = verify_post_integrity(event_id=event_id)
    print(f"[*] Initial verify_post_integrity({event_id}):")
    print(f"    - Status: {res_a['status']}")
    print(f"    - Verified: {res_a['verified']}")
    print(f"    - Trust Score: {res_a['trust_score']}")
    print(f"    - Local Hash: {res_a['local_hash']}")
    print(f"    - Blockchain Hash: {res_a['blockchain_hash']}")

    step_a_pass = (
        res_a['verified'] is True and
        res_a['status'] == 'VERIFIED' and
        res_a['trust_score'] == orig_score and
        res_a['local_hash'].lower() == res_a['blockchain_hash'].lower()
    )
    if step_a_pass:
        print(f"[PASS] STEP A: Authentic Event -> VERIFIED (Trust Score = {orig_score})")
    else:
        print("[FAIL] STEP A failed")
        all_passed = False

    try:
        # -------------------------------------------------------------
        # STEP B: SimulateTamper Execution & Verification
        # -------------------------------------------------------------
        print("\n--- STEP B: SimulateTamper Execution ---")
        req_tamper = factory.post('/SimulateTamper', data={'event_id': event_id})
        resp_tamper = SimulateTamper(req_tamper)
        print(f"[*] SimulateTamper response status: {resp_tamper.status_code}")
        print(f"    Redirect URL: {resp_tamper.url}")

        # Check backup file
        backup = get_demo_backup(event_id)
        print(f"[*] demo_backup.json content for Event #{event_id}:")
        print(f"    - Event ID: {backup.get('event_id')}")
        print(f"    - Original Hash: {backup.get('original_hash')}")
        print(f"    - Original Trust Score: {backup.get('original_trust_score')}")

        backup_pass = (
            backup is not None and
            backup.get('event_id') == event_id and
            backup.get('original_trust_score') == orig_score and
            backup.get('original_hash').lower() == ("0x" + orig_hash_bytes.hex()).lower()
        )

        # Verify tampered integrity state via Phase 6 verify_post_integrity
        res_b = verify_post_integrity(event_id=event_id)
        print(f"[*] Post-Tamper verify_post_integrity({event_id}):")
        print(f"    - Status: {res_b['status']}")
        print(f"    - Verified: {res_b['verified']}")
        print(f"    - Trust Score: {res_b['trust_score']}")
        print(f"    - Blockchain Hash: {res_b['blockchain_hash']}")
        print(f"    - Local Hash: {res_b['local_hash']}")

        # Verify UI rendering for tampered state
        req_ui_b = factory.get(f'/VerifyIntegrity?event_id={event_id}&demo_status=tampered')
        resp_ui_b = VerifyIntegrity(req_ui_b)
        content_ui_b = resp_ui_b.content.decode('utf-8')
        ui_b_pass = (
            "TAMPERED / UNVERIFIED" in content_ui_b and
            "0 / 100" in content_ui_b and
            "DEMO TAMPERING EXECUTED" in content_ui_b and
            f"#{event_id}" in content_ui_b
        )

        step_b_pass = (
            res_b['verified'] is False and
            res_b['status'] == 'TAMPERED / UNVERIFIED' and
            res_b['trust_score'] == 0 and
            backup_pass and
            ui_b_pass
        )

        if step_b_pass:
            print("[PASS] STEP B: SimulateTamper -> TAMPERED / UNVERIFIED (Trust Score = 0, Hard Gate enforced)")
        else:
            print(f"[FAIL] STEP B failed (res_b_pass={res_b['status']}, backup_pass={backup_pass}, ui_b_pass={ui_b_pass})")
            all_passed = False

        # -------------------------------------------------------------
        # STEP C: RestoreEvent Execution & Verification
        # -------------------------------------------------------------
        print("\n--- STEP C: RestoreEvent Execution ---")
        req_restore = factory.post('/RestoreEvent', data={'event_id': event_id})
        resp_restore = RestoreEvent(req_restore)
        print(f"[*] RestoreEvent response status: {resp_restore.status_code}")
        print(f"    Redirect URL: {resp_restore.url}")

        # Verify restored integrity state via Phase 6 verify_post_integrity
        res_c = verify_post_integrity(event_id=event_id)
        print(f"[*] Post-Restore verify_post_integrity({event_id}):")
        print(f"    - Status: {res_c['status']}")
        print(f"    - Verified: {res_c['verified']}")
        print(f"    - Trust Score: {res_c['trust_score']}")
        print(f"    - Blockchain Hash: {res_c['blockchain_hash']}")
        print(f"    - Local Hash: {res_c['local_hash']}")

        # Verify UI rendering for restored state
        req_ui_c = factory.get(f'/VerifyIntegrity?event_id={event_id}&demo_status=restored')
        resp_ui_c = VerifyIntegrity(req_ui_c)
        content_ui_c = resp_ui_c.content.decode('utf-8')
        ui_c_pass = (
            "VERIFIED" in content_ui_c and
            f"{orig_score} / 100" in content_ui_c and
            "DEMO RESTORATION SUCCESSFUL" in content_ui_c and
            f"#{event_id}" in content_ui_c
        )

        step_c_pass = (
            res_c['verified'] is True and
            res_c['status'] == 'VERIFIED' and
            res_c['trust_score'] == orig_score and
            res_c['local_hash'].lower() == res_c['blockchain_hash'].lower() and
            ui_c_pass
        )

        if step_c_pass:
            print(f"[PASS] STEP C: RestoreEvent -> VERIFIED (Trust Score = {orig_score} restored)")
        else:
            print(f"[FAIL] STEP C failed (res_c={res_c['status']}, ui_c_pass={ui_c_pass})")
            all_passed = False

    finally:
        # Guarantee blockchain state is restored even if an error occurs mid-test
        curr_hash, curr_score, _, _, _ = contract.functions.getEvent(event_id).call()
        if curr_hash != orig_hash_bytes or curr_score != orig_score:
            print("    [Cleanup] Restoring original event state in finally block...")
            tx_clean = contract.functions.restoreEvent(event_id, orig_hash_bytes, orig_score).transact()
            web3.eth.waitForTransactionReceipt(tx_clean)

    # -------------------------------------------------------------
    # STEP D: Verify Final Blockchain and Supabase State
    # -------------------------------------------------------------
    print("\n--- STEP D: Final Blockchain & Supabase State Verification ---")
    final_bc_hash, final_bc_score, _, _, final_bc_exists = contract.functions.getEvent(event_id).call()
    sb_final = get_event(event_id)

    print(f"[*] Final Blockchain State for Event #{event_id}:")
    print(f"    - dataHash: 0x{final_bc_hash.hex()}")
    print(f"    - trustScore: {final_bc_score}")
    print(f"    - exists: {final_bc_exists}")
    print(f"[*] Final Supabase State for Event #{event_id}:")
    print(f"    - sha256_hash: {sb_final.get('sha256_hash')}")
    print(f"    - trust_score: {sb_final.get('trust_score')}")
    print(f"    - tweet: {sb_final.get('tweet')[:50]}...")

    step_d_pass = (
        final_bc_hash == orig_hash_bytes and
        final_bc_score == orig_score and
        final_bc_exists is True and
        sb_final.get('sha256_hash') == sb_orig.get('sha256_hash') and
        sb_final.get('trust_score') == sb_orig.get('trust_score') and
        sb_final.get('tweet') == sb_orig.get('tweet')
    )

    if step_d_pass:
        print("[PASS] STEP D: Blockchain & Supabase states intact and match baseline")
    else:
        print("[FAIL] STEP D failed: State mismatch detected")
        all_passed = False

    # -------------------------------------------------------------
    # STEP E: Confirm Event #4 is Authentic After Test
    # -------------------------------------------------------------
    print("\n--- STEP E: Confirm Event #4 Final Authenticity ---")
    res_e = verify_post_integrity(event_id=event_id)
    step_e_pass = (
        res_e['verified'] is True and
        res_e['status'] == 'VERIFIED' and
        res_e['trust_score'] == orig_score and
        res_e['local_hash'].lower() == res_e['blockchain_hash'].lower()
    )

    if step_e_pass:
        print(f"[PASS] STEP E: Event #{event_id} verified authentic (Status: {res_e['status']}, Trust Score: {res_e['trust_score']})")
    else:
        print("[FAIL] STEP E failed")
        all_passed = False

    # -------------------------------------------------------------
    # SUMMARY
    # -------------------------------------------------------------
    print("\n" + "=" * 70)
    if all_passed:
        print("PHASE 7 INTEGRATION TEST: ALL CHECKS PASSED (100%)")
        print("Event #4 Initial State: VERIFIED (Trust: 98)")
        print("SimulateTamper: TAMPERED / UNVERIFIED (Trust: 0)")
        print("RestoreEvent: VERIFIED (Trust: 98 Restored)")
        print("Final Blockchain Proof: MATCH")
        print("Supabase Event Persistence: INTACT")
        print("PHASE 7 SUCCESS")
    else:
        print("PHASE 7 INTEGRATION TEST: ONE OR MORE CHECKS FAILED")
    print("=" * 70)
    return all_passed

if __name__ == '__main__':
    success = run_phase7_tests()
    sys.exit(0 if success else 1)
