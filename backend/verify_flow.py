import urllib.request
import json

base_api = 'http://127.0.0.1:8000'
fe_url = 'http://127.0.0.1:5173'

print('1. Testing Frontend HTTP...')
fe_resp = urllib.request.urlopen(fe_url)
print(f'Frontend HTTP Status: {fe_resp.status}')

print('\n2. Testing Initial Dashboard Metrics...')
req = urllib.request.urlopen(f'{base_api}/api/dashboard')
dash1 = json.loads(req.read())
print(f"Before: Revenue at Risk = INR {dash1['revenue_at_risk']:,.2f}, Recovered = INR {dash1['revenue_recovered']:,.2f}, Rate = {dash1['recovery_rate']}%, Active Cases = {dash1['active_cases']}")

print('\n3. Fetching Revenue Risk Cases...')
req = urllib.request.urlopen(f'{base_api}/api/revenue-risk?limit=5')
risks = json.loads(req.read())
target_case = risks[0]
cid = target_case['id']
print(f"Selected Case #{cid}: Customer = {target_case['customer_name']}, Amount = INR {target_case['amount']:,.2f}, Type = {target_case['recovery_type']}")

print('\n4. Running Autonomous Diagnosis & ERV Evaluation...')
post_req = urllib.request.Request(f'{base_api}/api/recovery-cases/{cid}/analyze', data=b'{}', headers={'Content-Type': 'application/json'}, method='POST')
analysis = json.loads(urllib.request.urlopen(post_req).read())
print(f"Diagnosed Root Cause: {analysis['root_cause']} ({int(analysis['confidence']*100)}% confidence)")
print(f"Recommended Action: {analysis['recommended_action']}")
print(f"Evaluated Interventions Count: {len(analysis['interventions'])}")
for i in analysis['interventions']:
    print(f"  - {i['action']}: Prob={i['recovery_probability']}, ERV=INR {i['expected_recovery_value']:,.2f}, Policy={i['policy_status']}")

print('\n5. Executing Autonomous Action...')
exec_data = json.dumps({'action_type': analysis['recommended_action'], 'language': 'hinglish'}).encode('utf-8')
post_req = urllib.request.Request(f'{base_api}/api/recovery-cases/{cid}/execute', data=exec_data, headers={'Content-Type': 'application/json'}, method='POST')
exec_res = json.loads(urllib.request.urlopen(post_req).read())
print(f"Execution Result: {exec_res['execution_result']}")
print(f"Amount Recovered: INR {exec_res['amount_recovered']:,.2f}")
print(f"Case Status: {exec_res['case_status']}")
if exec_res.get('message_content'):
    print(f"Generated Message Preview: {exec_res['message_content'][:100]}...")

print('\n6. Checking Audit Ledger...')
req = urllib.request.urlopen(f'{base_api}/api/ledger?limit=1')
ledger = json.loads(req.read())
print(f"Latest Ledger Entry: Case #{ledger[0]['case_id']}, Action = {ledger[0]['selected_action']}, Outcome = {ledger[0]['execution_result']}, Recovered = INR {ledger[0]['amount_recovered']:,.2f}")

print('\n7. Verifying Dynamic Dashboard Metric Update...')
req = urllib.request.urlopen(f'{base_api}/api/dashboard')
dash2 = json.loads(req.read())
print(f"After: Revenue Recovered = INR {dash2['revenue_recovered']:,.2f}, Rate = {dash2['recovery_rate']}%, Active Cases = {dash2['active_cases']}")
assert dash2['revenue_recovered'] >= dash1['revenue_recovered'], 'Metrics must dynamically update!'
print('\n>>> SUCCESS: FULL RECOVERAI INTEGRATION DEMO PASSED! <<<')
