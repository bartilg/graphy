import requests
import msal
import json
import pandas as pd
from .util import *

def get_access_token(client_id, authority, client_secret, scope):
    """Gets an access token for the MS Graph API

    Args:
        client_id (string): Application (client) ID from Azure App Registration
        authority (string): Authority url from the M365 Tenant
        client_secret (string): Client secret key from Azure App registration
        scope (string): Url for the scope permissions

    Returns:
        string: returns access token for MS Graph API
    """
    client = msal.ConfidentialClientApplication(client_id, authority=authority, client_credential=client_secret)
    token_result = client.acquire_token_silent(scope, account=None)
    
    # If the token is available in cache, save it to a variable
    if token_result:
        access_token = 'Bearer ' + token_result['access_token']
        print('Access token was loaded from cache')

    # If the token is not available in cache, acquire a new one from Azure AD and save it to a variable
    if not token_result:
        token_result = client.acquire_token_for_client(scopes=scope)
        access_token = 'Bearer ' + token_result['access_token']
        print('New access token was acquired from Azure AD')

    return access_token

def paginate_json(data, headers, response_data):
    """Paginates Json API responses until hitting the end. Adds them to list response_data

    Args:
        data (json): response from initial API call
        headers (json): Headers for the API call
        response_data (list[json]): list of API return values
    """
    while "@odata.nextLink" in data:
        next_link = data["@odata.nextLink"]
        graph_result = requests.get(next_link, headers=headers)
        data = graph_result.json()
        response_data.extend(data["value"])
    
def get_user_table(access_token):
    """queries the Graph API and generates a Pandas Dataframe of all employees UPN's and Directory Id's

    Args:
        access_token (string): access token for the MS Graph API
    """
    url = 'https://graph.microsoft.com/v1.0/users?$select=userprincipalname,id,mail,displayname,usertype,officeLocation,department,jobTitle,companyName,employeeid&$expand=manager($select=id,employeeId)'
    headers = {
        'Authorization': access_token
    }
    
    response_data = []
    
    # Make a GET request to the provided url, passing the access token in a header
    graph_result = requests.get(url=url, headers=headers)
    data = graph_result.json()
    response_data.extend(data["value"])

    paginate_json(data,headers,response_data)

    #convert table to pandas dataframe and drop unnecessary odata column
    df = pd.json_normalize(response_data)
    #df.drop('manager.@odata.type', axis=1)
    print(df)

    return df

def get_users(access_token, odata_query=''):
    """Issues a GET request to pull a list of users from Microsoft 365
    
    Args:
        access_token (string): access token for the MS Graph API
        odata_query (str, optional): odata query to apply to the request. Defaults to '' for .
    """
    #MS Graph REST API url
    url = 'https://graph.microsoft.com/v1.0/users/' + odata_query
    #Headers for API call (access token)
    headers = {
        'Authorization': access_token
    }
    temp = requests.patch(url,headers=headers)
    print(temp)

    
def patch_user(access_token, userPrincipalName, **kwargs):
    """Issues a PATCH request to update user properties in Azure AD
    For Valid PATCH arguments check API Reference: https://learn.microsoft.com/en-us/graph/api/user-update?view=graph-rest-1.0&tabs=http

    Args:
        access_token (string): access token for the MS Graph API
        userPrincipalName (string): UPN for the user to be patched
    """
    #MS Graph REST API url
    url = 'https://graph.microsoft.com/v1.0/users/' + userPrincipalName
    #Headers for API call (access token)
    headers = {
        'Authorization': access_token
    }    
    #init request body from kwargs key value pairs
    body = {}
    for key, value in kwargs.items():
        body[key] = value
    #Issue HTTP PATCH request to update user info
    temp = requests.patch(url,headers=headers,json=body)
    print(userPrincipalName)
    print(temp)

def get_ms_id_dict(df):
    """Constructs a dictionary where users employeeIds are the keys and their ids are the values

    Args:
        df (dataframe): Pandas Dataframe the dictionary is being built from

    Returns:
        dictionary: dictionary of employeeIds and Ids
    """
    dict = df.set_index('employeeId')['id'].to_dict()
    return dict

def get_mail_upn_dict(df):
    """Constructs a dictionary where users email addresses are the keys and their UPNs are the values

    Args:
        df (dataframe): Pandas Dataframe the dictionary is being built from

    Returns:
        dictionary: dictionary of email addresses and UPNs
    """
    dict = df.set_index('mail')['userPrincipalName'].to_dict()
    return dict
    
def set_manager(access_token, userPrincipalName, manager_id):
    """Set a users manager

    Args:
        access_token (string): access token for the MS Graph API
        userPrincipalName (string): UPN for the user to be patched
        manager_id (string): The id of the user's manager
    """
    url = 'https://graph.microsoft.com/v1.0/users/' + userPrincipalName + '/manager/$ref'
    headers = {
        'Authorization': access_token
    }
    body = {
        "@odata.id": "https://graph.microsoft.com/v1.0/users/" + manager_id
    }
    temp = requests.put(url,headers=headers,json=body)
    print(userPrincipalName)
    print(temp)
    
def assign_license(access_token, userPrincipalName, license_sku_id):
    """Assigns a license to a user

    Args:
        access_token (string): access token for the MS Graph API
        userPrincipalName (string): UPN for the user to be patched
        license_sku_id (string): the sku id of the license to assign
    """
    url = 'https://graph.microsoft.com/v1.0/users/'+ userPrincipalName + '/assignLicense'
    headers = {
        'Authorization': access_token
    }
    body = {
        "addLicenses": [
            {
                "skuId": license_sku_id
            }
        ],
        "removeLicenses": []
    }
    temp = requests.post(url,headers=headers,json=body)
    print(temp.json())
    


def create_user(access_token, userPrincipalName, **kwargs):
    #MS Graph REST API url
    url = 'https://graph.microsoft.com/v1.0/users/'
    #Headers for API call (access token)
    headers = {
        'Authorization': access_token
    }
    #init request body from kwargs key value pairs
    body = {}

    #default values for mandatory fields
    #enable account by default
    body['accountEnabled'] = 'true'
    #UPN is mandatory and must be passed in
    body['userPrincipalName'] = userPrincipalName
    #by default, use the prefix of the UPN as the mailNickname
    body['mailNickname'] = userPrincipalName.split('@')[0]
    #By Default, displayName is set to the UPN Prefix
    body['displayName'] = userPrincipalName.split('@')[0]
    #generate a password if it isn't specified
    my_pass = gen_password()
    body['passwordProfile'] = {
        "forceChangePasswordNextSignIn": True,
        "password": my_pass
    }
    
    #assign values from args
    for key, value in kwargs.items():
        passProfKeys = ['forceChangePasswordNextSignIn','forceChangePasswordNextSignInWithMfa','password']
        if key in passProfKeys:
            body['passwordProfile'][key] = value
        body[key] = value
    #Issue HTTP PATCH request to update user info
    temp = requests.post(url,headers=headers,json=body)
    print(temp.content)

def build_license_dict(json_data):
    sku_dict = {}    
    data = json.loads(json_data)
    subscribed_skus = data.get("value")
        
    for sku in subscribed_skus:
        sku_part_number = sku["skuPartNumber"]
        sku_id = sku.get("skuId")
            
        if sku_part_number and sku_id:
            sku_dict[sku_part_number] = sku_id
        
    return sku_dict

def get_subscribed_sku_ids(access_token):
    url = 'https://graph.microsoft.com/v1.0/subscribedSkus?$select=skuPartNumber,skuId'
    headers = {
        'Authorization': access_token
    }

    graph_result = requests.get(url=url, headers=headers)
    data = graph_result.json()

    return data

def get_license_report(access_token):
    url = 'https://graph.microsoft.com/v1.0/subscribedSkus'
    headers = {
        'Authorization': access_token
    }
    
    response_data = []
    
    # Make a GET request to the provided url, passing the access token in a header
    graph_result = requests.get(url=url, headers=headers)
    data = graph_result.json()
    response_data.extend(data["value"])

    paginate_json(data,headers,response_data)

    #convert table to pandas dataframe and drop unnecessary odata column
    df = pd.json_normalize(response_data)
    #df.drop('manager.@odata.type', axis=1)
    print(df)

    return df