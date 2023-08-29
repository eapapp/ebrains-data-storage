import os
import webbrowser
import sys
import subprocess
import pkg_resources
import argparse
from time import sleep, perf_counter



auth_url = "https://lab.ebrains.eu/hub/oauth_login?next=https://lab.ebrains.eu/user-redirect/lab/tree/shared/Data%20Curation/EBRAINS-token.ipynb"
# If you wish to use the non-interactive CLI, you still need to acquire a token from this jupyterlab instance.

APIURL = "https://data-proxy.ebrains.eu/api/v1/buckets/"
token = None
bucket = None
headers = {}

folder = None
prefix = None

parser = argparse.ArgumentParser(description="Command line interface to upload data to eBrains")
parser.add_argument("-f", "--folder", default=".", help="The directory, the CONTENTS OF WHICH, shall be uploaded")
parser.add_argument("-p", "--prefix", default="", help="Prefix within the bucket to use")
parser.add_argument("-t", "--token", default=None, help="The api token to authorise your upload")
parser.add_argument("-b", "--bucket", default=None, help="The bucket to which your data shall be uploaded")
parser.add_argument("-o", "--overwrite", action="store_true", help="overwrite existing files in the bucket, mutually exclusive with `-s`")
parser.add_argument("-s", "--skip", action="store_false", dest="overwrite", help="Skip existing files in the bucket, mutually exclusive with `-o`")
parser.add_argument("-v", "--verbose", action="store_true", help="Display debugging information")



def getfiles(folder):
    """
    Generate a list of all files to upload

    :param folder: Destination to check for contents
    :return: list of strings : list of all files in folder and subfolders
    """
    filelist = []

    for root, dirs, files in os.walk(folder):
        for name in files:
            fpath = os.path.join(root, name)
            cpath = os.path.realpath(__file__)
            if not fpath == cpath: filelist.append(fpath)

    filelist.sort()
    return(filelist)


def getobjlist(prefix):
    """
    Generate a list of all objects already present in the bucket with given prefix

    :param prefix: string, prefix to use to check for existing files
    :return: list of strings : list of all objects (with given prefix) in bucket
    """

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
    """
    Simple check if the bucket has any contents at all under the given prefix

    :param prefix: string, prefix to check for contents
    :return: boolean, do any objects exist under this prefix
    """

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

    print("---\nYour EBRAINS login token has expired. Please get a new token and copy it here.\n")
    token = input("EBRAINS auth token: ")
    print("---")

    if not token: raise SystemExit

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
    """
    Send the file to the bucket

    If the file already exists, you have the choice to skip it (skip-=True) or overwrite it (skip=false)
    """

    url = APIURL + bucket + "/" + obj

    if existing:
        if obj in existing:
            if skip:
                pass
            else:
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
    # Handle commandline arguments, if any, and install the required `requests` library
    args = parser.parse_args()
    setup("requests")
    import requests as rq

    # If commandline args were offered, slot them into the expected arguments
    # An empty string is an allowable value but obvious fails a boolean test
    if args.token is not None:
        token = args.token
    if args.bucket is not None:
        bucket = args.bucket
    if args.folder is not None:
        folder = args.folder
        skip_check = True        # Skip the interactive "continue y/n?" check
    else:
        skip_check = False
    if args.prefix is not None:
        prefix = args.prefix
        print("prefix = ", prefix)


    if args.verbose:
        print("\nUpload data to an EBRAINS bucket\n---\n")



    if token is None:

        print("Opening your browser for EBRAINS login. You can also copy-paste the following link:")
        print(auth_url)
        sleep(3)
        webbrowser.open(auth_url)

        token = input("\nEBRAINS authentication token: ")

    if bucket is None:
        bucket = input("Bucket name: ")

    if bucket is None or token is None:
        print("Bucket or token not provided, exiting")
        raise SystemExit
    if not tokenvalid(bucket, token):
        print("\nBucket not accessible with this token. Please get a new token and try again.")
        raise SystemExit

    if folder is None:
        print("\nFolder to upload\n---")
        print(" - Please note that only the contents of the folder will be uploaded, not the folder itself.")
        print(" - Empty subfolders are not supported by the EBRAINS storage and will be skipped.")
        print(" - If you choose the current folder, all files except this Python script will be uploaded.\n")
        folder = input("Data folder path (press Enter to use current folder): ")

    if not folder or folder == ".":
        folder = os.path.dirname(os.path.realpath(__file__))
        print("Current folder selected: " + folder)
    elif not os.path.exists(folder):
        print("Invalid folder path, exiting\n")
        raise SystemExit

    if args.verbose:
        print("Gathering list of files to be uploaded", end="... ", flush=True)
    filelist = getfiles(folder)
    if args.verbose:
        print(f"{len(filelist)} files found")

    if prefix is None:
        print("\nDestination folder in the bucket\n---")
        prefix = input(" - If you wish to copy to an existing folder in the bucket, please specify its path.\n - If the folder does not exist, it will be created.\n\nBucket folder to copy to: ")
    prefix = prefix.strip().strip("/").replace("\\","/").replace("//","/")

    existing = []
    skip = False
    if filesinbucket(prefix):
        if args.overwrite is not None:
            skip = not(args.overwrite)
        else:
            existing = getobjlist(prefix)
            print("\nExisting files in the bucket\n---")
            print("1. Overwrite existing files")
            print("2. Skip existing files\n---")
            skip = ''
            while not (skip=='1' or skip=='2'):
                skip = input("Choose 1 or 2: ")
            if skip == '2': skip = True
        print(skip)

    if not skip_check:
        cont = input("\n" + str(len(filelist)) + " files ready to be uploaded. Continue? (y/n): ")
        if cont != "y":
            print("Upload cancelled by user.\n")
            raise SystemExit
    else:
        if args.verbose:
            print("\nUploading your files to the bucket " + bucket + ":\n---")
        t0 = perf_counter()
        for fname in filelist:
            with open(fname,"rb") as content:
                obj = os.path.relpath(fname,folder).replace("\\","/")
                if prefix: obj = prefix + "/" + obj
                sendobj(obj, content, existing, skip)
        t1 = perf_counter()
        if args.verbose:
            print(f"Done in {t1-t0:.1n}s")
