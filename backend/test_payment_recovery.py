import urllib.request
import json

base_api = 'http://127.0.0.1:8000'

print('Finding a payment failure case...')
req = urllib.request.urlopen(f'{base_api}/api/revenue-risk?recovery_type=PAYMENT&status=PENDING&limit=10')
risks = json.loads(req.read())
target_case = [r for r in risks if r['amount'] < 50000][0]
cid = target_case['id']
print(f"Target Payment Case #{cid}: Customer = {target_case['customer_name']}, Amount = INR {target_case['amount']:,.2f}")

# Analyze
post_req = urllib.request.Request(f'{base_api}/api/recovery-cases/{cid}/analyze', data=b'{}', headers={'Content-Type': 'application/json'}, method='POST')
analysis = json.loads(urllib.request.urlopen(post_req).read())
print(f"Root Cause: {analysis['root_cause']}, Recommended: {analysis['recommended_action']}")

# Execute
exec_data = json.dumps({'action_type': analysis['recommended_action'], 'language': 'hinglish'}).encode('utf-8')
post_req = urllib.request.Request(f'{base_api}/api/recovery-cases/{cid}/execute', data=exec_data, headers={'Content-Type': 'application/json'}, method='POST')
exec_res = json.loads(urllib.request.urlopen(post_req).read())
print(f"Result: {exec_res['execution_result']}, Amount Recovered: INR {exec_res['amount_recovered']:,.2f}, Status: {exec_res['case_status']}")

# Dashboard metrics
req = urllib.request.urlopen(f'{base_api}/api/dashboard')
dash = json.loads(req.read())
print(f"Updated Dashboard: Total Recovered = INR {dash['revenue_recovered']:,.2f}, Recovery Yield = {dash['recovery_rate']}%, Recovered Cases = {dash['recovered_cases']}")
