import requests as rq
import CSCS_auth_per_scope_OTP as cscs
from getpass import getpass


DP_APIURL = "https://data-proxy.ebrains.eu/api/v1/buckets/"
headers = ''
swclient = None


def get_cscs_objdict(container_url):
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
    objlist = swclient.get_container(container=container_name, full_listing=True)[1]
    obj_dict = {}
    for obj in objlist:
        obj_dict[obj['name']] = obj

    return(obj_dict)


def get_bucket_objdict(bucket):

    url = DP_APIURL + bucket + "?limit=0"
    resp = rq.get(url=url, headers=headers)

    if resp.status_code == 200:
        obj_dict = {}
        objects = resp.json()["objects"]
        for obj in objects:
            obj_dict[obj['name']] = obj
        return(obj_dict)

    else:
        print("Data proxy API error: " + resp.reason + " - " + bucket + "\n")
        raise SystemExit


def is_bucket(container):
    
    if '/' in container:
        if 'object.cscs.ch' in container:
            bucket = False
        elif 'data-proxy.ebrains.eu' in container:
            bucket = True
        else:
            print('Invalid container URL')
            raise SystemExit

    else:
        bucket = True    
    
    return(bucket)


if __name__=='__main__':
    print('\nCheck whether the contents of two containers/buckets are in sync\n---')
    print('Usage: for containers, enter the full container URL. For buckets, enter the bucket name.\n')
    cont1 = input('First container or bucket: ')
    cont2 = input('Second container or bucket: ')
    print('---')

    ebrains_token = ''
    if is_bucket(cont1):
        ebrains_token = input('EBRAINS auth token: ')
        headers = {
        "accept": "application/json",
        "Authorization": "Bearer " + ebrains_token
        }

        cont1_objdict = get_bucket_objdict(cont1)
    else:
        cont1_objdict = get_cscs_objdict(cont1)

    if is_bucket(cont2):
        if not ebrains_token:
            ebrains_token = input('EBRAINS auth token: ')
            headers = {
            "accept": "application/json",
            "Authorization": "Bearer " + ebrains_token
            }
        cont2_objdict = get_bucket_objdict(cont2)
    else:
        cont2_objdict = get_cscs_objdict(cont2)
    
    print('---\nComparing containers...')
    for obj in cont1_objdict:
        if obj in cont2_objdict:
            if not cont1_objdict[obj]['hash'] == cont2_objdict[obj]['hash']:
                print(' -', obj, ': Hash mismatch')
        else:
            print(' -', obj, 'in', cont1, 'not found in', cont2)

    for obj in cont2_objdict:
        if obj in cont1_objdict:
            if not cont2_objdict[obj]['hash'] == cont1_objdict[obj]['hash']:
                print(' -', obj, ': Hash mismatch')
        else:
            print(' -', obj, 'in', cont2, 'not found in', cont1)

    print('\n---\nDone.\n')
