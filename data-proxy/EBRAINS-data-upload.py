import os
import webbrowser
import sys
import subprocess
import pkg_resources
from time import sleep
import tkinter as tk

APIURL = "https://data-proxy.ebrains.eu/api/v1/buckets/"
token = None
bucket = None
headers = {}


def getfiles(folder):
    filelist = []

    for root, dirs, files in os.walk(folder):
        for name in files:
            if not name.startswith('._'):    # Ignore MacOS metadata files            
                fpath = os.path.join(root, name)
                cpath = os.path.realpath(__file__)
                if not fpath == cpath: filelist.append(fpath)

    filelist.sort()
    return(filelist)


def getobjlist(prefix):

    url = APIURL + bucket
    if prefix: url = url + "?prefix=" + prefix 
    if "?" in url:
        url = url + "&limit=0"
    else:
        url = url + "?limit=0"

    resp = rq.get(url=url,headers=headers)

    if resp.status_code == 200:

        objlist = []
        objects = resp.json()["objects"]
        for obj in objects:
            objlist.append(obj["name"])

        return(objlist)

    elif resp.status_code == 401:
        newtoken()
        objlist = getobjlist(bucket, token)
        return(objlist)

    else:
        print("Data proxy API error: " + resp.reason + " - " + bucket + "\n")
        raise SystemExit
    

def filesinbucket(prefix):

    url = APIURL + bucket + "/stat"

    resp = rq.get(url=url,headers=headers)

    if resp.status_code == 200:
        if resp.json()["objects_count"] > 0:
            if prefix:
                url = APIURL + bucket + "?prefix=" + prefix + "&limit=5"
                resp = rq.get(url=url,headers=headers)
                if len(resp.json()["objects"]) > 0:
                    return(True)
                else:
                    return(False)
            else:
                return(True)
        else:
            return(False)

    else:
        print("Data proxy API error: " + resp.reason + " - " + bucket + "\n")
        raise SystemExit


def newtoken():
    global token
    global headers

    print("---\nYour EBRAINS login token has expired. Please get a new token on the clipboard:")
    print(auth_url)
    sleep(3)
    webbrowser.open(auth_url)
    
    input('Press Enter once you have copied your EBRAINS authentication token to the clipboard.')
    token = root.clipboard_get()
    if not token.startswith('eyJ'): token = ''

    while not token:
        resp = input('No token found on the clipboard, please try again. Type Q to quit.')
        if resp.lower() == 'q':
            raise SystemExit
        else:
            token = root.clipboard_get()
            if not token.startswith('eyJ'): token = ''

    print("---")

    headers = {
        "accept": "application/json",
        "Authorization": "Bearer " + token
    }


def upload(url, content):

    obj = "/".join(url.split("/")[7:])
    print(" - " + obj, end=' ', flush=True)

    for i in range(3):    # Retry max. 3 times                
        resp = rq.put(url=url,headers=headers)

        if resp.status_code == 200: # HTTP 200 OK

            uploadurl = resp.json()["url"]
            resp = rq.put(uploadurl,content)

            if resp.status_code == 201: # HTTP 201 Created
                print("- Done.")
                break
            elif resp.status_code == 401: # HTTP 401 Unauthorized
                newtoken()

        elif resp.status_code == 401: # HTTP 401 Unauthorized
            newtoken()

    else:
        print("- Upload failed: " + str(resp.status_code) + " " + resp.reason)
            
            
def sendobj(obj, content, existing, skip):

    url = APIURL + bucket + "/" + obj

    if existing:
        if obj in existing:
            if not skip:           
                rq.delete(url=url,headers=headers)
                upload(url, content)
        else:
            upload(url, content)

    else:
        upload(url, content)


def tokenvalid(bucket, token):

    global headers

    url = APIURL + bucket + "/stat"
    headers = {
        "accept": "application/json",
        "Authorization": "Bearer " + token
    }

    resp = rq.get(url=url,headers=headers)

    if resp.status_code == 200:
        return(True)
    else:
        return(False)


def setup(package):

    installed = {pkg.key for pkg in pkg_resources.working_set}
    if not package in installed:
        print("Installing required packages...\n")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
        print("\nSetup done.\n---\n")
  
    return()


if __name__=='__main__':
    # Upload data to an EBRAINS bucket

    print("\nUpload data to an EBRAINS bucket\n---\n")

    setup("requests")
    import requests as rq

    auth_url = "https://lab.ebrains.eu/hub/oauth_login?next=https://lab.ebrains.eu/user-redirect/lab/tree/shared/Data%20Curation/EBRAINS-token.ipynb"
    print("Opening your browser for EBRAINS login. You can also copy-paste the following link:")
    print(auth_url)
    sleep(3)
    webbrowser.open(auth_url)

    input('\nPress Enter once you have copied your EBRAINS authentication token to the clipboard.')

    root = tk.Tk()
    root.withdraw()
    token = root.clipboard_get()
    if not token.startswith('eyJ'): token = ''

    while not token:
        resp = input('No token found on the clipboard, please try again. Type Q to quit.')
        if resp.lower() == 'q':
            raise SystemExit
        else:
            token = root.clipboard_get()
            if not token.startswith('eyJ'): token = ''
     
    # token = input("\nEBRAINS authentication token: ")
    bucket = input("Bucket name: ")
    if not(bucket or token): raise SystemExit
    if not tokenvalid(bucket, token):
        print("\nBucket not accessible with this token. Please get a new token and try again.")
        raise SystemExit

    print("\nFolder to upload\n---")
    print(" - Please note that only the contents of the folder will be uploaded, not the folder itself.")
    print(" - Empty subfolders are not supported by the EBRAINS storage and will be skipped.")
    print(" - If you choose the current folder, all files except this Python script will be uploaded.\n")
    folder = input("Data folder path (press Enter to use current folder): ")

    if not folder:
        folder = os.path.dirname(os.path.realpath(__file__))
        print("Current folder selected: " + folder)
    elif not os.path.exists(folder):
        print("Invalid folder path.\n")
        raise SystemExit

    print("Gathering list of files to be uploaded", end="... ", flush=True)
    filelist = getfiles(folder)
    print("Done.")

    print("\nDestination folder in the bucket\n---")
    prefix = input(" - If you wish to copy to an existing folder in the bucket, please specify its path.\n - If the folder does not exist, it will be created.\n\nBucket folder to copy to: ")
    prefix = prefix.strip().strip("/").replace("\\","/").replace("//","/")

    existing = []
    skip = False
    if filesinbucket(prefix):
        existing = getobjlist(prefix)
        print("\nExisting files in the bucket\n---")
        print("1. Overwrite existing files")
        print("2. Skip existing files\n---")
        skip = ''
        while not (skip=='1' or skip=='2'):
            skip = input("Choose 1 or 2: ")
        if skip == '2': skip = True

    cont = input("\n" + str(len(filelist)) + " files ready to be uploaded. Continue? (y/n): ")
    if cont != "y":
        print("Upload cancelled by user.\n")
        raise SystemExit
    else:
        print("\nUploading your files to the bucket " + bucket + ":\n---")
        for fname in filelist:
            with open(fname,"rb") as content:
                obj = os.path.relpath(fname,folder).replace("\\","/")
                if prefix: obj = prefix + "/" + obj
                sendobj(obj, content, existing, skip)

print('---\n')
