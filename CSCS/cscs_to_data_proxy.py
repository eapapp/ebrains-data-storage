import requests as rq
import CSCS_auth_per_scope_OTP as cscs
from getpass import getpass
import http


DP_APIURL = "https://data-proxy.ebrains.eu/api/v1/buckets/"
headers = ''
swclient = None
bucket = ''


def swift_list(container_name):
    # Run swift list on container
    response = swclient.get_container(container=container_name, full_listing=True)

    # results = []
    # for n in response[1]:
    #     objname = n["name"]
    #     results.append(objname)      

    return(response[1])


def get_cscs_objlist(container_url):
    global swclient
    username = input('CSCS user name: ')
    password = getpass()
    otp = input('OTP: ')

    sess = cscs.get_unscoped_token(username, password, otp)
    if sess is None:
        print('Login failed.')
        raise(SystemExit)
    
    sc_sess = cscs.get_scoped_token(sess, container_url)
    swclient = cscs.connect(sc_sess)

    container_name = container_url.split('/')[-1].split('?')[0]    # Discard prefix
    objlist_full = swift_list(container_name)
    # objlist = []
    # for obj in objlist_full:
    #     if not obj['content_type'] == 'application/directory':
    #         objlist.append(obj)

    return(objlist_full)


def get_object(container_url, obj):
    container_name = container_url.split('/')[-1].split('?')[0]    # Discard prefix
    try:
        header, contents = swclient.get_object(container_name, obj)
    except http.client.IncompleteRead as icread:
        print('Exception: ' + str(icread))
        print('Re-trying...')
        header, contents = swclient.get_object(container_name, obj)

    return(contents)


def upload(obj_url, content):

    # obj = "/".join(obj_url.split("/")[7:])
    print(' -', obj_url, '... ',flush=True, end='')
    url = DP_APIURL + bucket + '/' + obj_url

    for i in range(3):    # Retry max. 3 times                
        resp = rq.put(url=url,headers=headers)

        if resp.status_code == 200: # HTTP 200 OK

            uploadurl = resp.json()["url"]
            resp = rq.put(uploadurl,content)

            if resp.status_code == 201: # HTTP 201 Created
                print("Done.")
                break

    else:
        print("- Upload failed: " + str(resp.status_code) + " " + resp.reason)


def get_bucket_objlist():

    url = DP_APIURL + bucket + "?limit=0"
    resp = rq.get(url=url, headers=headers)

    if resp.status_code == 200:

        objlist = []
        objects = resp.json()["objects"]
        for obj in objects:
            objlist.append(obj["name"])

        return(objlist)

    else:
        print("Data proxy API error: " + resp.reason + " - " + bucket + "\n")
        raise SystemExit



if __name__=='__main__':
    print('\nMove the contents of a CSCS container to a data proxy bucket file by file\n---')
    container_url = input('Container URL: ')
    bucket = input('Bucket name: ')
    ebrains_token = input('EBRAINS auth token: ')
    if not(container_url or bucket or ebrains_token): raise SystemExit
    headers = {
        "accept": "application/json",
        "Authorization": "Bearer " + ebrains_token
        }

    # Get object list from container
    objlist = get_cscs_objlist(container_url)  

    # Get list of existing files in bucket
    existing = get_bucket_objlist()
    # existing = ''

    # Download and upload file by file
    print('\nMoving', len(objlist), 'files:')
    
    if existing:
        for obj in objlist:
            if not obj['name'] in existing:
                content = get_object(container_url, obj['name'])
                upload(obj['name'], content)
    else:
        for obj in objlist:
            content = get_object(container_url, obj['name'])
            upload(obj['name'], content)

    # TODO: Compare results

    # TODO: Delete original files and container