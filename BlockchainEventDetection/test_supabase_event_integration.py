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
from EventApp.supabase_client import get_latest_event

def run_integration_test():
    print("=" * 65)
    print("TESTING SUPABASE EVENT PERSISTENCE + BLOCKCHAIN INTEGRATION")
    print("=" * 65)

    c = Client(HTTP_HOST='127.0.0.1')
    
    # 1. Login user so session / username is defined
    test_user = "disaster_responder_1"
    print("\n[STEP 1] Logging in as user '{}'...".format(test_user))
    views.username = test_user
    
    # 2. Submit a Disaster Tweet through PredictAction
    test_tweet = "Major flood warning: river overflowing in low-lying residential sectors, rescue operations underway"
    print("\n[STEP 2] Submitting event prediction via /PredictAction...")
    print("Tweet text: '{}'".format(test_tweet))
    
    resp = c.post('/PredictAction', {'t1': test_tweet})
    assert resp.status_code == 200, "PredictAction returned HTTP {}".format(resp.status_code)
    resp_text = resp.content.decode()
    
    print("\n[STEP 3] Verifying Prediction Response...")
    assert "Disaster Event Detected" in resp_text, "Expected 'Disaster Event Detected' in response"
    assert "VERIFIED" in resp_text, "Expected 'VERIFIED' in response"
    assert "Trust Score (Stored on Blockchain)" in resp_text, "Expected Trust Score in response"
    print("[PASS] ML Prediction, Confidence, Blockchain transaction, and Trust Score verified!")

    # 3. Verify Blockchain Contract State
    print("\n[STEP 4] Verifying On-Chain Contract State...")
    web3, contract = views.get_blockchain_contract()
    chain_post = contract.functions.getPost().call()
    chain_hash = contract.functions.getPostHash().call()
    chain_score = contract.functions.getTrustScore().call()
    
    chain_hash_hex = chain_hash.hex()
    print("On-Chain Post Hash   : 0x{}".format(chain_hash_hex))
    print("On-Chain Trust Score : {} / 100".format(chain_score))
    assert test_tweet in chain_post, "Tweet not found in on-chain post!"
    assert chain_score > 0, "On-chain trust score is not positive!"
    print("[PASS] Smart contract verified on Truffle Develop.")

    # 4. Verify Supabase Persistence
    print("\n[STEP 5] Querying Supabase PostgreSQL for latest event row...")
    latest_event = get_latest_event()
    assert latest_event is not None, "Failed to retrieve latest event from Supabase!"
    
    print("\n--- SUPABASE EVENT RECORD FETCHED ---")
    print("Event ID           : {}".format(latest_event.get('id')))
    print("Username           : {}".format(latest_event.get('username')))
    print("Classification     : {}".format(latest_event.get('classification')))
    print("Confidence         : {}%".format(latest_event.get('confidence')))
    print("Event Date         : {}".format(latest_event.get('event_date')))
    print("SHA-256 Hash       : {}".format(latest_event.get('sha256_hash')))
    print("Trust Score        : {}".format(latest_event.get('trust_score')))
    print("Blockchain Tx Hash : {}".format(latest_event.get('blockchain_tx_hash')))
    print("Created At         : {}".format(latest_event.get('created_at')))
    print("-------------------------------------")

    # Match Tweet
    assert latest_event.get('tweet') == test_tweet, "Supabase tweet does not match submitted tweet!"
    print("[PASS] Tweet text matches in Supabase.")

    # Match Username
    assert latest_event.get('username') == test_user, "Supabase username mismatch!"
    print("[PASS] Username matches in Supabase.")

    # Match Classification
    assert latest_event.get('classification') == "Disaster Event Detected", "Supabase classification mismatch!"
    print("[PASS] Classification matches in Supabase.")

    # Match Trust Score
    assert int(latest_event.get('trust_score')) == chain_score, "Trust Score mismatch between Supabase and Blockchain!"
    print("[PASS] Trust Score in Supabase ({}) exactly matches Blockchain ({}).".format(latest_event.get('trust_score'), chain_score))

    # Match SHA-256 Hash
    # Supabase sha256_hash is 64 hex characters (without 0x prefix)
    expected_hash_clean = chain_hash_hex.lower()
    supabase_hash_clean = latest_event.get('sha256_hash', '').lower()
    assert supabase_hash_clean == expected_hash_clean, "SHA-256 mismatch! Supabase: {}, Blockchain: {}".format(supabase_hash_clean, expected_hash_clean)
    print("[PASS] SHA-256 in Supabase exactly matches Blockchain on-chain hash!")

    # Verify Blockchain Transaction Hash
    tx_hash = latest_event.get('blockchain_tx_hash')
    assert tx_hash is not None and tx_hash.startswith("0x") and len(tx_hash) == 66, "Invalid blockchain_tx_hash in Supabase: {}".format(tx_hash)
    print("[PASS] Real Ethereum Transaction Hash captured in Supabase: {}".format(tx_hash))

    # 5. Verify VerifyIntegrity Page
    print("\n[STEP 6] Testing /VerifyIntegrity Page...")
    vi_resp = c.get('/VerifyIntegrity')
    assert vi_resp.status_code == 200
    vi_text = vi_resp.content.decode()
    assert "VERIFIED" in vi_text
    assert "{} / 100".format(chain_score) in vi_text
    print("[PASS] /VerifyIntegrity displays Status=VERIFIED, Trust Score={}/100".format(chain_score))

    # 6. Test Tampering & Restore Demo
    print("\n[STEP 7] Testing Demo Tamper Mode & Restoration...")
    tamper_resp = c.post('/SimulateTamper')
    assert tamper_resp.status_code in [200, 302]
    
    vi_tampered = c.get('/VerifyIntegrity')
    assert "TAMPERED / UNVERIFIED" in vi_tampered.content.decode()
    assert "0 / 100" in vi_tampered.content.decode()
    print("[PASS] SimulateTamper correctly triggers TAMPERED / UNVERIFIED with Trust Score = 0 / 100")

    restore_resp = c.post('/RestoreEvent')
    assert restore_resp.status_code in [200, 302]
    
    vi_restored = c.get('/VerifyIntegrity')
    assert "VERIFIED" in vi_restored.content.decode()
    assert "{} / 100".format(chain_score) in vi_restored.content.decode()
    print("[PASS] RestoreEvent successfully restores authentic event: VERIFIED with Trust Score = {} / 100".format(chain_score))

    print("\n" + "=" * 65)
    print("ALL TESTS PASSED: SUPABASE EVENT PERSISTENCE SUCCESS")
    print("=" * 65)
    return True

if __name__ == '__main__':
    success = run_integration_test()
    sys.exit(0 if success else 1)
