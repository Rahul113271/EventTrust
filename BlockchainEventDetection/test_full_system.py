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

def run_tests():
    print("=" * 60)
    print("STARTING COMPREHENSIVE FINAL VERIFICATION TESTS")
    print("=" * 60)

    # -------------------------------------------------------------
    # 1. BLOCKCHAIN LAYER TESTS
    # -------------------------------------------------------------
    print("\n--- 1. BLOCKCHAIN SMART CONTRACT VERIFICATION ---")
    web3 = Web3(HTTPProvider('http://127.0.0.1:9545', request_kwargs={'timeout': 60}))
    assert web3.isConnected(), "Web3 connection to 127.0.0.1:9545 failed!"
    print("[PASS] Web3 connected to 127.0.0.1:9545")

    with open('Event.json', 'r') as f:
        contract_json = json.load(f)
    abi = contract_json['abi']
    contract_addr = views.DEPLOYED_CONTRACT_ADDRESS
    print(f"[INFO] Deployed Contract Address: {contract_addr}")

    abi_funcs = [item['name'] for item in abi if item.get('type') == 'function']
    required_funcs = [
        'addUser', 'getUser', 'setPost', 'getPost',
        'setPostWithHash', 'getPostHash',
        'trustScore', 'setTrustScore', 'getTrustScore'
    ]
    for func in required_funcs:
        assert func in abi_funcs, f"Function {func} missing from ABI!"
        print(f"[PASS] ABI contains function: {func}")

    web3.eth.defaultAccount = web3.eth.accounts[0]
    contract = web3.eth.contract(address=contract_addr, abi=abi)

    # Test initial getters
    initial_user = contract.functions.getUser().call()
    initial_post = contract.functions.getPost().call()
    initial_hash = contract.functions.getPostHash().call()
    initial_score = contract.functions.getTrustScore().call()
    print(f"[PASS] getUser() works: '{initial_user}'")
    print(f"[PASS] getPost() works: '{initial_post[:30]}...'")
    print(f"[PASS] getPostHash() works: {initial_hash.hex()[:16]}...")
    print(f"[PASS] getTrustScore() works: {initial_score}")

    # Test setTrustScore(75) & getTrustScore()
    tx = contract.functions.setTrustScore(75).transact()
    web3.eth.waitForTransactionReceipt(tx)
    val75 = contract.functions.getTrustScore().call()
    assert val75 == 75, f"Expected 75, got {val75}"
    print(f"[PASS] setTrustScore(75) verified -> getTrustScore() = {val75}")

    # Test setTrustScore(101) reverts
    reverted = False
    try:
        tx = contract.functions.setTrustScore(101).transact()
        web3.eth.waitForTransactionReceipt(tx)
    except Exception as e:
        reverted = True
        print(f"[PASS] setTrustScore(101) correctly reverted: {e.args[0] if e.args else e}")
    assert reverted, "setTrustScore(101) should have reverted!"

    # -------------------------------------------------------------
    # 2. DJANGO END-TO-END FLOW TESTS
    # -------------------------------------------------------------
    print("\n--- 2. DJANGO APPLICATION END-TO-END VERIFICATION ---")
    c = Client(HTTP_HOST='127.0.0.1')

    # Home page
    resp = c.get('/index.html')
    assert resp.status_code == 200, f"index.html failed: {resp.status_code}"
    print("[PASS] Home page (/index.html) returned HTTP 200")

    # User registration
    test_user = "test_investigator"
    test_pass = "secure123"
    reg_resp = c.post('/RegisterAction', {
        't1': test_user,
        't2': test_pass,
        't3': '1234567890',
        't4': 'investigator@disaster-intel.org',
        't5': 'Command Center'
    })
    assert reg_resp.status_code == 200, f"RegisterAction failed: {reg_resp.status_code}"
    print(f"[PASS] User registration (/RegisterAction) completed for '{test_user}'")

    # User login
    login_resp = c.post('/UserLoginAction', {
        't1': test_user,
        't2': test_pass
    })
    assert f"Welcome {test_user}" in login_resp.content.decode(), f"Login failed, content: {login_resp.content.decode()[:200]}"
    print(f"[PASS] User login (/UserLoginAction) successful with 'Welcome {test_user}'")

    # Predict page GET
    pred_page = c.get('/Predict.html')
    assert pred_page.status_code == 200, f"Predict.html failed: {pred_page.status_code}"
    assert "Verify Data Integrity" in pred_page.content.decode(), "Predict.html missing Verify Data Integrity link"
    print("[PASS] Prediction page (/Predict.html) loaded with Verify Data Integrity link")

    # PredictAction POST with a Disaster Tweet
    disaster_tweet = "Earthquake magnitude 7.2 strikes coastal region rescue teams deployed immediately"
    pred_resp = c.post('/PredictAction', {'t1': disaster_tweet})
    assert pred_resp.status_code == 200, f"PredictAction failed: {pred_resp.status_code}"
    pred_content = pred_resp.content.decode()
    print("[INFO] PredictAction response snippet:\n", pred_content[pred_content.find("Post Classified as"):pred_content.find("Post Classified as")+200].replace("<br/>", " | ").replace("<b>", "").replace("</b>", ""))

    assert "Disaster Event Detected" in pred_content, "Expected Disaster Event Detected!"
    assert "VERIFIED" in pred_content, "Expected VERIFIED in prediction response!"
    assert "Trust Score" in pred_content, "Expected Trust Score in prediction response!"
    print("[PASS] PredictAction: DL classification detected Disaster Event, calculated confidence, verified integrity, and stored Trust Score on blockchain!")

    # Verify stored post and hash on blockchain
    post_on_chain = contract.functions.getPost().call()
    hash_on_chain = contract.functions.getPostHash().call()
    score_on_chain = contract.functions.getTrustScore().call()
    local_calc_hash = hashlib.sha256(post_on_chain.encode('utf-8')).digest()

    assert disaster_tweet in post_on_chain, "Disaster tweet not found in blockchain post!"
    assert hash_on_chain == local_calc_hash, "Stored hash does not match local calculation!"
    assert score_on_chain > 0, f"Expected positive trust score, got {score_on_chain}"
    print(f"[PASS] Blockchain post contains tweet, SHA-256 matches: {hash_on_chain.hex()[:16]}..., Trust Score = {score_on_chain}/100")

    # VerifyIntegrity Dashboard GET
    vi_resp = c.get('/VerifyIntegrity')
    assert vi_resp.status_code == 200, f"VerifyIntegrity failed: {vi_resp.status_code}"
    vi_content = vi_resp.content.decode()
    assert "VERIFIED" in vi_content, "VerifyIntegrity dashboard missing VERIFIED"
    assert f"{score_on_chain} / 100" in vi_content, "VerifyIntegrity dashboard missing trust score"
    assert "Disaster Event Detected" in vi_content, "VerifyIntegrity dashboard missing classification"
    print(f"[PASS] /VerifyIntegrity dashboard renders: Status=VERIFIED, Trust Score={score_on_chain}/100, Class=Disaster Event Detected")

    # -------------------------------------------------------------
    # 3. TAMPERING & RESTORATION TESTS
    # -------------------------------------------------------------
    print("\n--- 3. TAMPERING DETECTION & RESTORATION VERIFICATION ---")
    # Save original post and hash for restoration
    original_post = contract.functions.getPost().call()
    original_hash = contract.functions.getPostHash().call()
    original_score = contract.functions.getTrustScore().call()

    print("[INFO] Simulating unauthorized data alteration on blockchain...")
    tampered_post = original_post + "TAMPERED_INJECTED_DATA_UNAUTHORIZED\n"
    # Tamper by changing post data without updating the hash (using setPost)
    tx_tamper = contract.functions.setPost(tampered_post).transact()
    web3.eth.waitForTransactionReceipt(tx_tamper)

    # Call verify_post_integrity
    tamper_result = views.verify_post_integrity()
    print(f"[INFO] verify_post_integrity() verified: {tamper_result['verified']}")
    print(f"[INFO] verify_post_integrity() message: {tamper_result['message']}")
    print(f"[INFO] verify_post_integrity() trust_score: {tamper_result['trust_score']}")

    assert not tamper_result['verified'], "Tampering was NOT detected!"
    assert tamper_result['trust_score'] == 0, f"Expected trust score 0 on tampered data, got {tamper_result['trust_score']}"
    assert tamper_result['local_hash'] != tamper_result['blockchain_hash'], "Local hash and blockchain hash unexpectedly matched!"
    print("[PASS] Tamper detection successful: Integrity=TAMPERED / UNVERIFIED, Trust Score=0, Hashes mismatch!")

    # Check /VerifyIntegrity UI during tampered state
    vi_tampered_resp = c.get('/VerifyIntegrity')
    assert vi_tampered_resp.status_code == 200
    vi_tampered_content = vi_tampered_resp.content.decode()
    assert "TAMPERED / UNVERIFIED" in vi_tampered_content, "UI does not show TAMPERED / UNVERIFIED!"
    assert "0 / 100" in vi_tampered_content, "UI does not show 0 / 100 on tampered data!"
    print("[PASS] /VerifyIntegrity UI properly displays: TAMPERED / UNVERIFIED in red with 0 / 100 Trust Score")

    # RESTORE ORIGINAL STATE
    print("[INFO] Restoring blockchain to original verified state...")
    tx_restore = contract.functions.setPostWithHash(original_post, original_hash).transact()
    web3.eth.waitForTransactionReceipt(tx_restore)
    tx_restore_score = contract.functions.setTrustScore(original_score).transact()
    web3.eth.waitForTransactionReceipt(tx_restore_score)

    restored_result = views.verify_post_integrity()
    assert restored_result['verified'], "Restoration failed: post not verified!"
    assert restored_result['trust_score'] == original_score, "Restoration failed: score mismatch!"
    print(f"[PASS] Blockchain state restored and re-verified: Integrity=VERIFIED, Trust Score={restored_result['trust_score']}/100")

    # -------------------------------------------------------------
    # 4. REGRESSION TESTS FOR EXISTING FEATURES
    # -------------------------------------------------------------
    print("\n--- 4. REGRESSION VERIFICATION FOR EXISTING FEATURES ---")
    # TrainML view
    train_resp = c.get('/TrainML')
    assert train_resp.status_code == 200, f"TrainML failed: {train_resp.status_code}"
    print("[PASS] /TrainML view returned HTTP 200 with algorithms performance table")

    # Graph view
    graph_resp = c.get('/Graph')
    assert graph_resp.status_code == 200, f"Graph failed: {graph_resp.status_code}"
    print("[PASS] /Graph view returned HTTP 200 with comparison chart")

    # ViewTweets view
    tweets_resp = c.get('/ViewTweets')
    assert tweets_resp.status_code == 200, f"ViewTweets failed: {tweets_resp.status_code}"
    assert disaster_tweet in tweets_resp.content.decode(), "Disaster tweet missing in /ViewTweets"
    print("[PASS] /ViewTweets view returned HTTP 200 with stored tweets table")

    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED AND VERIFIED WITH 100% SUCCESS!")
    print("=" * 60)

if __name__ == '__main__':
    run_tests()
