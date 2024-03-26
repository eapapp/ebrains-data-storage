import requests as rq

APIURL = "https://data-proxy.ebrains.eu/api/v1/buckets/"

def getobjlist(url, headers, marker):

    if not "limit=" in url: url = url + "?limit=0"
    if marker: url = url + "&marker=" + marker

    resp = rq.get(url=url,headers=headers)

    if resp.status_code == 200:

        objlist = []
        objects = resp.json()["objects"]
        for obj in objects:
            objlist.append(obj["name"])

        if len(objects)==10000:
            marker = objlist[-1]
            nextpage = getobjlist(url, headers, marker)
            objlist.extend(nextpage)

        return(objlist)

    else:
        print("Data proxy API error: " + resp.reason + " - " + bucket + "\n")
        raise SystemExit
    
if __name__=='__main__':
    print("\nGet object list from an EBRAINS bucket\n---\n")
    token = input("\nEBRAINS authentication token: ")
    bucket = input("Bucket name: ")
    url = APIURL + bucket
    headers = {
        "accept": "application/json",
        "Authorization": "Bearer " + token
    }
    objlist = getobjlist(url, headers, "")
    with open(bucket + ".objlist","w") as objfile:
        for obj in objlist:
            objfile.write(obj + "\n")
