import os
import sys
import django
import json
import hashlib

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Event.settings')
django.setup()

from django.test import Client
from web3 import Web3, HTTPProvider
from EventApp import views
from EventApp.supabase_client import get_latest_event, get_event

def run_phase5_test():
    print("=" * 65)
    print("PHASE 5: TESTING PREDICTION -> SUPABASE -> ETHEREUM recordEvent FLOW")
    print("=" * 65)

    c = Client(HTTP_HOST='127.0.0.1')
    
    # 1. Set user context
    test_user = "disaster_chief_officer"
    views.username = test_user
    print(f"\n[STEP 1] Operating as user: '{test_user}'")

    # 2. Submit test disaster tweet
    test_tweet = "URGENT: Category 4 cyclone approaching coastline, mandatory evacuation ordered immediately"
    print(f"\n[STEP 2] Submitting event prediction via /PredictAction...")
    print(f"Tweet: '{test_tweet}'")

    resp = c.post('/PredictAction', {'t1': test_tweet})
    assert resp.status_code == 200, f"PredictAction failed with status {resp.status_code}"
    resp_text = resp.content.decode()
    
    print("\n[STEP 3] Verifying Web UI Response...")
    assert "Disaster Event Detected" in resp_text, "Expected 'Disaster Event Detected' in response"
    assert "VERIFIED" in resp_text, "Expected 'VERIFIED' in response"
    assert "Trust Score (Stored on Blockchain)" in resp_text, "Expected Trust Score in response"
    print("[PASS] Web response rendered correctly with Disaster Event Detected and Trust Score.")

    # 3. Query Supabase for the persisted event
    print("\n[STEP 4] Fetching latest event from Supabase PostgreSQL...")
    latest_event = get_latest_event()
    assert latest_event is not None, "Failed to retrieve event from Supabase!"
    
    event_id = latest_event.get('id')
    print(f"[INFO] Supabase Event ID: {event_id}")
    print(f"[INFO] Classification   : {latest_event.get('classification')}")
    print(f"[INFO] Confidence       : {latest_event.get('confidence')}%")
    print(f"[INFO] SHA-256 Hash     : {latest_event.get('sha256_hash')}")
    print(f"[INFO] Trust Score      : {latest_event.get('trust_score')}")
    print(f"[INFO] Blockchain Tx    : {latest_event.get('blockchain_tx_hash')}")

    assert latest_event.get('tweet') == test_tweet, "Tweet text in Supabase does not match submitted tweet!"
    assert latest_event.get('username') == test_user, "Username in Supabase does not match current user!"
    assert latest_event.get('blockchain_tx_hash') is not None, "blockchain_tx_hash was not updated in Supabase!"
    assert latest_event.get('blockchain_tx_hash').startswith("0x"), "Invalid blockchain_tx_hash format!"
    print("[PASS] Supabase event record verified with updated blockchain_tx_hash.")

    # 4. Query Ethereum Smart Contract using getEvent(event_id)
    print("\n[STEP 5] Querying Ethereum Smart Contract using getEvent(eventId)...")
    web3, contract = views.get_blockchain_contract()
    
    on_chain_event = contract.functions.getEvent(int(event_id)).call()
    on_chain_hash_bytes = on_chain_event[0]
    on_chain_score = on_chain_event[1]
    on_chain_timestamp = on_chain_event[2]
    on_chain_recorder = on_chain_event[3]
    on_chain_exists = on_chain_event[4]

    on_chain_hash_hex = on_chain_hash_bytes.hex().lower()
    supabase_hash = latest_event.get('sha256_hash').lower()

    print(f"On-Chain Event ID       : {event_id}")
    print(f"On-Chain Exists         : {on_chain_exists}")
    print(f"On-Chain Hash           : 0x{on_chain_hash_hex}")
    print(f"Supabase Stored Hash    : {supabase_hash}")
    print(f"On-Chain Trust Score    : {on_chain_score} / 100")
    print(f"On-Chain Timestamp      : {on_chain_timestamp}")
    print(f"On-Chain Recorder       : {on_chain_recorder}")

    assert on_chain_exists == True, f"Event {event_id} does not exist on-chain!"
    assert on_chain_hash_hex == supabase_hash, f"Hash mismatch between Ethereum ({on_chain_hash_hex}) and Supabase ({supabase_hash})!"
    assert on_chain_score == int(latest_event.get('trust_score')), f"Trust score mismatch!"
    print("[PASS] Ethereum getEvent(eventId) exactly matches Supabase record!")

    # 5. Test verifyEventHash on-chain helper
    print("\n[STEP 6] Testing smart contract verifyEventHash(eventId, testHash)...")
    is_match, verified_score = contract.functions.verifyEventHash(
        int(event_id),
        on_chain_hash_bytes
    ).call()
    assert is_match == True, "verifyEventHash failed to verify authentic hash!"
    assert verified_score == on_chain_score, "verifyEventHash score mismatch!"
    print(f"[PASS] verifyEventHash on-chain returns: isMatch={is_match}, trustScore={verified_score}")

    # 6. Verify totalEvents counter
    total_events = contract.functions.getEventCount().call()
    print(f"\n[STEP 7] Total events on Ethereum: {total_events}")
    assert total_events >= 1, "Total events counter should be >= 1"

    print("\n" + "=" * 65)
    print("PHASE 5 TEST PASSED: PREDICTION -> SUPABASE -> ETHEREUM recordEvent SUCCESS")
    print("=" * 65)
    return True

if __name__ == '__main__':
    ok = run_phase5_test()
    sys.exit(0 if ok else 1)
