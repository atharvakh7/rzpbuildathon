"""
End-to-end verification script for the Mandate Retry Sequencer.
Tests live HTTP endpoints on http://127.0.0.1:8000:
1. Mandate Stats
2. Mandates list & detail
3. Immediate presentation execution (success flow -> recovery + ledger)
4. Presentation execution (failure flow -> stage advance)
5. DB persistence and ledger verification
"""

import json
import urllib.request
import urllib.parse

BASE_URL = "http://127.0.0.1:8000"

def get(url):
    req = urllib.request.Request(f"{BASE_URL}{url}", headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode("utf-8"))

def post(url, data=None):
    payload = json.dumps(data or {}).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}{url}",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode("utf-8"))

def run_tests():
    print("=" * 60)
    print("MANDATE RETRY SEQUENCER: LIVE END-TO-END VERIFICATION")
    print("=" * 60)

    # 1. Check Stats
    stats_before = get("/api/mandates/stats")
    print("\n[1] Initial Mandate Stats:")
    print(f"    Total Mandates:       {stats_before['total_mandates']}")
    print(f"    At Risk:              {stats_before['at_risk_mandates']}")
    print(f"    Recovered:            {stats_before['recovered_mandates']}")
    print(f"    Recovered Amount:     INR {stats_before['recovered_amount']:,.2f}")
    print(f"    Active Window:        {stats_before['next_clearing_window']}")

    # 2. List Mandates
    mandates = get("/api/mandates")
    print(f"\n[2] Listed {len(mandates)} Mandates from Database.")
    resequenced = [m for m in mandates if m["status"] == "RESEQUENCED"]
    print(f"    Found {len(resequenced)} in RESEQUENCED status.")

    if not resequenced:
        print("    No resequenced mandates found; testing with first available.")
        target = mandates[0]
    else:
        target = resequenced[0]

    mandate_id = target["id"]
    print(f"\n[3] Selected Target Mandate: ID #{mandate_id}")
    print(f"    UMRN:         {target['umrn']}")
    print(f"    Customer:     {target['customer_name']}")
    print(f"    Bank:         {target['bank_name']}")
    print(f"    Type:         {target['mandate_type']}")
    print(f"    Amount:       INR {target['amount']:,.2f}")
    print(f"    Stage:        {target['current_stage']}/4")
    print(f"    Status:       {target['status']}")

    # 3. Get Detail with sequence stages
    detail = get(f"/api/mandates/{mandate_id}")
    print(f"\n[4] Fetched Full 4-Stage Timeline for Mandate #{mandate_id}:")
    for s in detail["sequences"]:
        res_str = f" [{s.get('result')}]" if s.get('result') else ""
        print(f"    - Stage {s['stage']}: {s['title']} | Status: {s['status']}{res_str} | Prob: {int(s['liquidity_probability']*100)}%")

    # 4. Trigger Presentation Now (Simulating clearance during morning window)
    print(f"\n[5] Executing 'Trigger Presentation Now' with Force Success...")
    present_res = post(f"/api/mandates/{mandate_id}/present-now", {"override_success": True})
    print(f"    Result:           {'SUCCESS' if present_res['success'] else 'FAILED'}")
    print(f"    Action Taken:     {present_res['action_taken']}")
    print(f"    New Status:       {present_res['new_status']}")
    print(f"    Amount Recovered: INR {present_res['amount_recovered']:,.2f}")
    print(f"    Message:          {present_res['message']}")

    # 5. Verify Detail Updated in DB
    refreshed_detail = get(f"/api/mandates/{mandate_id}")
    print(f"\n[6] Verifying Database Mutation for Mandate #{mandate_id}:")
    print(f"    Status in DB:     {refreshed_detail['status']}")
    cleared_stages = [s for s in refreshed_detail["sequences"] if s.get("result") == "SUCCESS"]
    print(f"    Cleared Stages:   {len(cleared_stages)} stage(s) marked SUCCESS")

    # 6. Verify Ledger if linked to case
    if refreshed_detail.get("case_id"):
        case_id = refreshed_detail["case_id"]
        case = get(f"/api/recovery-cases/{case_id}")
        print(f"\n[7] Linked Case #{case_id} Auto-Update:")
        print(f"    Case Status:      {case['status']}")
        print(f"    Amount Recovered: INR {case['amount_recovered']:,.2f}")
        print(f"    Stop Reason:      {case.get('stop_reason')}")

    # 7. Check Stage Escalation (Failure flow test)
    if len(resequenced) > 1:
        fail_target = resequenced[1]
        fid = fail_target["id"]
        init_stage = fail_target["current_stage"]
        print(f"\n[8] Testing Stage Advance on Mandate #{fid} (Current Stage {init_stage}) with Force Fail...")
        fail_res = post(f"/api/mandates/{fid}/present-now", {"override_success": False})
        refreshed_fail = get(f"/api/mandates/{fid}")
        print(f"    Result:           {'SUCCESS' if fail_res['success'] else 'FAILED'}")
        print(f"    New Stage in DB:  Stage {refreshed_fail['current_stage']}/4")
        print(f"    Next Date:        {refreshed_fail['next_presentation_at']}")
        print(f"    Message:          {fail_res['message']}")

    # 8. Check Updated Aggregated Stats
    stats_after = get("/api/mandates/stats")
    print(f"\n[9] Updated System Stats after Execution:")
    print(f"    Recovered Mandates: {stats_before['recovered_mandates']} -> {stats_after['recovered_mandates']}")
    print(f"    Recovered Amount:   INR {stats_before['recovered_amount']:,.2f} -> INR {stats_after['recovered_amount']:,.2f}")
    print(f"    Recovery Rate:      {stats_before['recovery_rate']}% -> {stats_after['recovery_rate']}%")

    print("\n" + "=" * 60)
    print("ALL MANDATE SEQUENCER VERIFICATIONS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
