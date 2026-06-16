import get_data_proxy_objlist as dp
import requests as rq

APIURL = "https://data-proxy.ebrains.eu/api/v1/buckets/"
headers = {}

def delete(obj):
    # Delete an object from a data proxy bucket
    url = APIURL + bucket + "/" + obj
    rq.delete(url=url, headers=headers)


if __name__=='__main__':

    print("\nDelete all files from an EBRAINS bucket\n---")

    token = input("EBRAINS auth token: ")
    bucket = input("Bucket name: ")
    url = APIURL + bucket
    
    headers = {
        "accept": "application/json",
        "Authorization": "Bearer " + token
    }
    objlist = dp.getobjlist(url, headers, "")
    
    print("---")
    print("\nFound", len(objlist), "files.")
    ok = input("\nProceed to deleting all these files? (y/n) ")

    if ok.strip() == "y":
        print("")
        for obj in objlist:
            print(" - Deleting file " + obj + "... ", flush=True, end='')
            delete(obj)
            print("Done.")
        print("")
