import requests
r = requests.get("http://localhost:8000/circuitos/zf/ranking")
print(f"Status: {r.status_code}")
print(f"Body: {r.text[:2000]}")
