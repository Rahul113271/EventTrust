import os
import sys

# Ensure EventApp is importable
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from EventApp.supabase_client import test_connection, SUPABASE_URL, SUPABASE_KEY

def main():
    print("=" * 60)
    print("SUPABASE POSTGREST REST API CONNECTION TEST (NON-DESTRUCTIVE)")
    print("=" * 60)
    
    # Verify environment loading without exposing secret key
    if not SUPABASE_URL:
        print("[ERROR] SUPABASE_URL not found in .env")
        sys.exit(1)
    if not SUPABASE_KEY:
        print("[ERROR] SUPABASE_KEY not found in .env")
        sys.exit(1)
        
    print("[INFO] Supabase URL detected: {}".format(SUPABASE_URL))
    print("[INFO] Supabase API Key loaded: YES (length: {} chars, key hidden)".format(len(SUPABASE_KEY)))
    print("[INFO] Executing non-destructive GET request to public.users and public.events...")
    
    res = test_connection()
    
    print("-" * 60)
    print("TEST RESULTS:")
    print("HTTP Status for public.users : {}".format(res['users_status']))
    print("HTTP Status for public.events: {}".format(res['events_status']))
    
    if res['success']:
        print("[RESULT] SUPABASE CONNECTION SUCCESS")
        print("[INFO] Django can communicate securely with Supabase PostgreSQL tables.")
    else:
        print("[RESULT] SUPABASE CONNECTION FAILED")
        print("[ERROR DETAILS]: {}".format(res['error']))
        
    print("=" * 60)
    return 0 if res['success'] else 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
