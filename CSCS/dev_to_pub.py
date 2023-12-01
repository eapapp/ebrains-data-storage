# Python script for copying files from the _dev container to the _pub container
# using swift copy (without downloading and uploading again)
# @author eapapp

import CSCS_auth_per_scope_OTP as cscs
from getpass import getpass
import swiftclient
from datetime import datetime


def swift_list(swclient, container_name):
    # Run swift list on container
    response = swclient.get_container(container=container_name, full_listing=True)

    results = []
    for n in response[1]:
        objname = n["name"]
        results.append(objname)      

    return(results)


def renew_token(user,pwd,prj):
    # Get an unscoped token
    otp = input('One-time password from authenticator app: ')
    sess = cscs.get_unscoped_token(user,pwd,otp)

    # Get a scoped token
    sc_sess = cscs.get_scoped_token(sess, prj)
    swclient = cscs.connect(sc_sess)

    return(swclient)


if __name__=='__main__':

    print('\n--- Copying objects from a _dev container to the corresponding _pub container ---\n')
    username = input('CSCS user name: ')
    password = getpass()
    otp = input('One-time password from authenticator app: ')

    # Get an unscoped token
    sess = cscs.get_unscoped_token(username,password,otp)
    if sess is None:
        print('Login failed.')
        raise(SystemExit)

    print('---')
    print('Login successful.\n')

    # Ask for container URL
    dev_container = input('Dev container URL: ')

    if dev_container[-1] == "/": dev_container = dev_container[:-1]   # Remove trailing /
    project_id = dev_container[31:].split('/')[0]
    project_url = dev_container[:len(dev_container)-len(dev_container.split('/')[-1])-1]
    dev_container = dev_container.split('/')[-1].split('?')[0]    # Discard prefix

    if dev_container.endswith("_dev"):
        pub_container = dev_container[:-4] + "_pub"
        print("Pub container: " + pub_container)
        reply = input("Press Enter to confirm the name of the pub container, or type a new name here: ")
        if not reply.strip() == "": pub_container = reply
    else:
        pub_container = input("Pub container name: ")

    # Get a scoped token
    sc_sess = cscs.get_scoped_token(sess, project_url)
    swclient = cscs.connect(sc_sess)
    print('---\nLogin to project OK (' + project_id + ').')

    # Check if _pub container exists
    try:
        resp = swclient.head_container(container=pub_container)
    except swiftclient.ClientException as e:
        if e.http_status == 404:    # Container does not exist
            swclient.put_container(container=pub_container)

    # Fetch object list
    objlist = swift_list(swclient, dev_container)

    # Filter objects that have already been copied
    publist = swift_list(swclient, pub_container)
    devset = set(objlist)
    pubset = set(publist)
    diff = devset - pubset   

    if not diff:
        print("All _dev files are already present in _pub.")
        raise SystemExit

    print("---")
    print("Total number of objects in _dev: " + str(len(devset)))
    print("Already in _pub: " + str(len(pubset)) + " objects.")
    print("Remains to be copied: " + str(len(diff)) + " objects.")
    print("---")

    # Copy objects from _dev to _pub
    tstamp = datetime.now().strftime("%Y.%m.%d %H:%M:%S")
    print("---\nStarting to copy from _dev to _pub")
    print("Timestamp: " + tstamp)

    count = 0
    for obj in diff:
        count += 1
        if count % 1000 == 0:
            tstamp = datetime.now().strftime("%Y.%m.%d %H:%M:%S")
            print("---\nProcessing file nr. " + str(count))
            print("Timestamp: " + tstamp)

        dest = pub_container + "/" + obj
        try:
            swclient.copy_object(container=dev_container,obj=obj,destination=dest)
        except swiftclient.ClientException as e:
            if e.http_status == 401:    # Unauthorized -- token expired
                print("---\nYour CSCS access token has expired.")
                print("Requesting new token...")
                swclient = renew_token(username,password,project_url)
                print("Success.\n---")
                swclient.copy_object(container=dev_container,obj=obj,destination=dest)
            else:
                print(str(e.http_status) + " - " + e.msg + " - " + obj)
                count -= 1

    tstamp = datetime.now().strftime("%Y.%m.%d %H:%M:%S")
    print("---\nFinished copying objects from " + dev_container + " to " + pub_container + ".")
    print("Timestamp: " + tstamp)
    print(str(count) + " objects were copied.")
