import requests as rq
import webbrowser
import sys
import subprocess
import pkg_resources
from time import sleep
import os

APIURL = 'https://data-proxy.ebrains.eu/api/v1/datasets/'
headers = ''


def setup(package):

    installed = {pkg.key for pkg in pkg_resources.working_set}
    if not package in installed:
        print("Installing required packages...\n")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
        print("\nSetup done.\n---\n")
  
    return()


def getobjlist(url, marker):

    if not 'limit=' in url: url = url + '?limit=0'
    if marker: url = url + '&marker=' + marker

    resp = rq.get(url=url,headers=headers)

    if resp.status_code == 200:

        objlist = []
        objects = resp.json()['objects']
        for obj in objects:
            # if int(obj['bytes']) < 104857600:    # file size limit for testing
            objlist.append(obj['name'])

        if len(objects) > 0:
            marker = objlist[-1]
            nextpage = getobjlist(url, marker)
            objlist.extend(nextpage)

        return(objlist)

    else:
        print('Data proxy API error: ' + resp.reason + '\n')
        raise SystemExit


def getfile(dataset, file):

    url = APIURL + dataset + '/' + file + '?redirect=false'
    resp = rq.get(url=url,headers=headers)
    dld_url = resp.json()['url']
    binary = rq.get(dld_url).content

    return(binary)


def tokenvalid(dataset, token):

    global headers

    url = APIURL + dataset + "/stat"
    headers = {
        "accept": "application/json",
        "Authorization": "Bearer " + token
    }

    resp = rq.get(url=url,headers=headers)

    if resp.status_code == 200:
        return(True)
    else:
        return(False)


if __name__=='__main__':
  
    print('\nDownload all files from an EBRAINS dataset\n---\n')
    print('Note: for controlled access data, you need to accept the terms of service in the e-mail first.')
    print('The files will be downloaded in the current directory unless you specify otherwise.')
    dataset = input('\nDataset ID: ')
    if not dataset: raise SystemExit

    setup("requests")
    import requests as rq

    auth_url = "https://lab.ebrains.eu/hub/oauth_login?next=https://lab.ebrains.eu/user-redirect/lab/tree/shared/Data%20Curation/EBRAINS-token.ipynb"
    print("\nOpening your browser for EBRAINS login. You can also copy-paste the following link:")
    print(auth_url)
    sleep(3)
    webbrowser.open(auth_url)
    token = input('EBRAINS authentication token: ')
    
    if not tokenvalid(dataset, token):
        print("\nBucket not accessible with this token. Please get a new token (evt. accept the terms) and try again.")
        raise SystemExit

    url = APIURL + dataset
    headers = {
        'accept': 'application/json',
        'Authorization': 'Bearer ' + token
    }

    dld_folder = input('\nFolder to download the data to (enter an absolute or relative path): ')
    if not dld_folder:
        dld_folder = os.getcwd()
        print(dld_folder)
    elif not os.path.isabs(dld_folder):
        dld_folder = os.path.join(os.getcwd(), dld_folder)

    print('---')
    objlist = getobjlist(url, '')
    for obj in objlist:
        fname = obj.split('/')[-1]
        fpath = obj[:len(obj)-len(fname)]        
        print(' - Downloading file ' + fname + '... ',flush=True, end='')
        content = getfile(dataset,obj)        
        dld_path = os.path.join(dld_folder, fpath)
        if not os.path.isdir(dld_path): os.makedirs(dld_path)           
        file_path = os.path.join(dld_folder, obj)
        with open(file_path,'wb+') as outf:
            outf.write(content)           
        print('Done.')

    print('---\n')
