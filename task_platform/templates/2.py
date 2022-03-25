import requests
r=requests.get("http://localhost/web100.php")
r.encoding="unicode"
print(r.text)