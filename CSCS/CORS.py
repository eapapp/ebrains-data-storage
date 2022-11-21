import CSCS_auth_per_scope as cscs
from getpass import getpass
import re
import os


def readfile(path):

    lines = []
    with open(path,"r") as f:
        for line in f:
            lines.append(line.strip())

    return(lines)


if __name__=='__main__':

    # User login
    print('\n--- Set CORS header for CSCS containers ---\n')
    username = input('CSCS user name: ')
    password = getpass()

    # Get an unscoped token
    sess = cscs.get_unscoped_token(username,password)
    if sess is None:
        print('Login failed.')
        raise(SystemExit)

    print('---')
    print('Login successful.\n')

    # Ask for container URL(s)
    containers = input('Container URL(s) or file with URL list: ')
    if containers.startswith("https://object.cscs.ch/v1/AUTH_"):
        contURLs = set([c.strip() for c in re.split(',|;| |\n|\t', containers)])
    else:
        if os.path.exists(containers) and os.path.isfile(containers):
            contURLs = set(readfile(containers))
        else:
            print("File not found.")
            raise SystemExit

    project_id = ""
    for c in contURLs:

        if c[-1] == "/": c = c[:-1]   # Remove trailing /
        container = c.split('/')[-1].split('?')[0]    # Discard prefix
        print('\nProcessing container: ' + container)

        if project_id != c[:64]:
            # Get a scoped token
            project_id = c[:64]
            sc_sess = cscs.get_scoped_token(sess, project_id)
            swclient = cscs.connect(sc_sess)

        # Enable CORS
        resp = swclient.head_container(container=container)
        if "x-container-meta-access-control-allow-origin" in resp.keys():
            if not resp["x-container-meta-access-control-allow-origin"] == "*":
                swclient.post_container(container=container, headers={"X-Container-Meta-Access-Control-Allow-Origin":"*"})
                print("CORS added")
            else:
                print("CORS OK")
        else:
            swclient.post_container(container=container, headers={"X-Container-Meta-Access-Control-Allow-Origin":"*"})
            print("CORS added")                