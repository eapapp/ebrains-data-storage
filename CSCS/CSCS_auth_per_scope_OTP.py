from keystoneauth1.identity import v3
from keystoneauth1.identity import V3OidcAccessToken
from keystoneauth1 import session
from keystoneclient.v3 import client
import swiftclient.client as swiftclient
from getpass import getpass
import requests as rq


def get_unscoped_token(user, password, otp):
    # Get an unscoped token

    auth_url = 'https://castor.cscs.ch:13000/v3'
    identity_provider = 'cscskc'
    protocol = 'openid'
    discovery_endpoint ='https://auth.cscs.ch/auth/realms/cscs/.well-known/openid-configuration'
    token_endpoint = 'https://auth.cscs.ch/auth/realms/cscs/protocol/openid-connect/token'
    client_id = 'castor'
    client_secret = 'c6cc606a-5ae4-4e3e-8a19-753ad265f521'    

    headers = {'client_id': client_id,
               'client_secret': client_secret,
               'username': user,
               'password': password,
               'grant_type': 'password',
               'otp': otp}

    resp = rq.post(url=token_endpoint,data=headers)
    access_token = resp.json()['access_token']

    auth = V3OidcAccessToken(access_token=access_token,
               auth_url=auth_url,
               identity_provider=identity_provider,
               protocol=protocol,
               discovery_endpoint=discovery_endpoint)

    sess = session.Session(auth=auth)

    # print("User ID: " + sess.get_user_id())

    return(sess)


def get_scoped_token(sess, project):
    # Get a scoped token

    auth_url = 'https://castor.cscs.ch:13000/v3'
    ks = client.Client(session=sess, interface='public')

    # Check if the project is available to this user
    projects = ks.projects.list(user=sess.get_user_id())

    # Find out if project is a name or a URL
    if "/" in project:
        if project[-1] == "/": project = project[:-1]   # Remove trailing /
        proj_id = project[31:63]
        # Check if the project is available to this user
        if not proj_id in [p.id for p in projects]:
            print('Cannot log on to this project.')
            return(None)

    else:
        proj_name = project
        # Check if the project is available to this user
        if not proj_name in [p.name for p in projects]:
            print('Cannot log on to this project.')
            return(None)
        else:
            for p in projects:
                if p.name == proj_name:
                    proj_id = p.id
                    break

    kc_token = sess.get_token()
    auth = v3.Token(auth_url=auth_url, 
                    token=kc_token,
                    project_id=proj_id)
    sc_sess = session.Session(auth=auth)
    return(sc_sess)


def connect(sess):
    # Create a Swift connection
    scoped_token = sess.get_token()
    swift_url = sess.get_endpoint(service_type='object-store', interface='public')
    swclient = swiftclient.Connection(preauthurl=swift_url, preauthtoken=scoped_token)
    return(swclient)


if __name__=='__main__':
    
    print('\n---\nCSCS Authentication via OIDC (unscoped + scoped)\n---')
    username = input('User name: ')
    password = getpass()
    otp = input('One-time password from authenticator app: ')
    proj_id = input('Project URL or name: ') or 'ebrain01'

    sess = get_unscoped_token(username,password,otp)
    sc_sess = get_scoped_token(sess, proj_id)
    swclient = connect(sc_sess)
    print("Connection successful.")
