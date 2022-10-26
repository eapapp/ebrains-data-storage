import CSCS_auth_per_scope as cscs
from getpass import getpass
import swiftclient
import os

swclient = None
username = ""
password = ""
project_id = ""
container = ""


def renew_token():

    global swclient
    global username
    global password
    global project_id

    # Get an unscoped token
    sess = cscs.get_unscoped_token(username,password)

    # Get a scoped token
    sc_sess = cscs.get_scoped_token(sess, project_id)
    swclient = cscs.connect(sc_sess)


def getobjlist(folder):

    objlist = []

    for root, subdirs, files in os.walk(folder):
        if subdirs == [] and files == []:
            objlist.append(root)
        else:
            for f in files:
                objlist.append(os.path.join(root,f))

    return(objlist)


def putfile(obj, contents):
    global swclient
    global container

    try:
        swclient.put_object(container=container, obj=obj, contents=contents)
    except swiftclient.ClientException as e:
        if e.http_status == 401:    # Unauthorized -- token expired
            print("---\nYour CSCS access token has expired.")
            print("Requesting new token...")
            renew_token()
            print("Success.\n---")
            swclient.put_object(container=container, obj=obj, contents=contents)
        else:
            print(str(e.http_status) + " - " + e.msg)


def upload(obj, contents, skip):
    global swclient
    global container

    try:
        resp = swclient.head_object(container=container, obj=obj)
        if type(resp) == dict and int(resp["content-length"]) > 0:     # Object already exists
            if not skip: putfile(obj, contents)
        else:
            putfile(obj, contents)

    except swiftclient.ClientException as e:
        if e.http_status == 401:    # Unauthorized -- token expired
            print("---\nYour CSCS access token has expired.")
            print("Requesting new token...")
            renew_token()
            print("Success.\n---")
            upload(obj, contents, skip)
        
        elif e.http_status == 404:
            putfile(obj, contents)

        else:
            print(str(e.http_status) + " - " + e.msg)


if __name__=='__main__':

    print('\n--- Uploading local folders to a curation container on CSCS ---\n')
    username = input('CSCS user name: ')
    password = getpass()

    # Get an unscoped token
    sess = cscs.get_unscoped_token(username,password)
    if sess is None:
        print('Login failed.')
        raise(SystemExit)

    print('---')
    print('Login successful.\n')

    # Ask for container URL
    container_url = input('Destination container URL: ')
    if container_url[-1] == "/": container_url = container_url[:-1]   # Remove trailing /
    container = container_url.split('/')[-1].split('?')[0]    # Discard prefix
    prefix = ""
    if '?prefix=' in container_url: prefix = container_url.split('?prefix=')[1]    

    # Get a scoped token
    project_id = container_url[:64]
    sc_sess = cscs.get_scoped_token(sess, project_id)
    swclient = cscs.connect(sc_sess)
    print('---')
    print('Login to CSCS project OK.\n')

    folderlist = input("Text file listing folder paths: ")
    folders = []    
    with open(folderlist, "r") as fl:
        for line in fl:
            folders.append(line.strip())

    print("\nHow to handle files that already exist in the container\n---")
    print("1. Overwrite existing files")
    print("2. Skip existing files\n---")
    skip = ''
    while not (skip=='1' or skip=='2'):
        skip = input("Choose 1 or 2: ")
    if skip == '2': skip = True

    # Upload files
    print("\nUploading " + str(len(folders)) + " folders\n---\n")

    for f in folders:
        objlist = getobjlist(f)
        count = 0
        fname = os.path.basename(f)
        print("Begin uploading folder: " + fname)
        print("---")
        for obj in objlist:
            count += 1
            if os.path.isdir(obj):
                contents = ""
                obj = fname + "/" + os.path.relpath(obj,f).replace("\\","/")
                print(str(count) + " of " + str(len(objlist)) + " - " + obj)
                if prefix: obj = prefix + "/" + obj
                upload(obj, contents, skip)
            else:
                contents = open(obj, 'rb')
                obj = fname + "/" + os.path.relpath(obj,f).replace("\\","/")
                print(str(count) + " of " + str(len(objlist)) + " - " + obj)                   
                if prefix: obj = prefix + "/" + obj
                upload(obj, contents, skip)
                contents.close()

        print("---\nFolder " + fname + " uploaded.\n")

    print("Upload complete.")
