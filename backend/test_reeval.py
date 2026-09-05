import urllib.request
import json

base_api = 'http://127.0.0.1:8000'
cid = 21

print("Re-evaluating Case #21 after first action...")
post_req = urllib.request.Request(f'{base_api}/api/recovery-cases/{cid}/analyze', data=b'{}', headers={'Content-Type': 'application/json'}, method='POST')
analysis = json.loads(urllib.request.urlopen(post_req).read())
print(f"Next Best Recommended Action: {analysis['recommended_action']}")

exec_data = json.dumps({'action_type': analysis['recommended_action'], 'language': 'hinglish'}).encode('utf-8')
post_req = urllib.request.Request(f'{base_api}/api/recovery-cases/{cid}/execute', data=exec_data, headers={'Content-Type': 'application/json'}, method='POST')
exec_res = json.loads(urllib.request.urlopen(post_req).read())
print(f"Second Step Result: {exec_res['execution_result']}")
print(f"Amount Recovered: INR {exec_res['amount_recovered']:,.2f}")
print(f"Case Status: {exec_res['case_status']}")

# Check updated dashboard
req = urllib.request.urlopen(f'{base_api}/api/dashboard')
dash = json.loads(req.read())
print(f"Dashboard Stats: Total Recovered = INR {dash['revenue_recovered']:,.2f}, Yield = {dash['recovery_rate']}%, Recovered Cases = {dash['recovered_cases']}")
