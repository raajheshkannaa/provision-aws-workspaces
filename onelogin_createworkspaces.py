import boto3
from botocore.exceptions import ClientError
from time import sleep
from onelogin.api.client import OneLoginClient

#client_id = "<ONELOGIN CLIENT ID>"
#client_secret = "<ONELOGIN CLIENT SECRET>"

oclient = OneLoginClient("<ONELOGIN CLIENT ID>","<ONELOGIN CLIENT SECRET>")

client = boto3.client('workspaces')

def get_workspaces():
    response = client.describe_workspaces(
        DirectoryId = '<AWS WORKSPACES DIRECTORY ID>'
    )

    resources = response['Workspaces']

    length = len(resources)
    
    users = []
    for key in range(length):
        username = resources[key]['UserName']
        wsid = resources[key]['WorkspaceId']
        state = resources[key]['State']
        wsprop = resources[key]['WorkspaceProperties']['RunningMode']
        users.append(username)

    return(users)

def create_workspaces(username):
    
    response = client.create_workspaces(
        Workspaces = [
            {
                'DirectoryId': '<AWS WORKSPACES DIRECTORY ID>',
                'UserName': username,
                'BundleId': '<AWS WORKSPACES IMAGE BUNDLE ID>',
                #'VolumeEncryptionKey': '<KMS KEY ARN',
                #'UserVolumeEncryptionEnabled': True,
                #'RootVolumeEncryptionEnabled': True,
                'WorkspaceProperties': {
                    'RunningMode': 'AUTO_STOP',
                    'RunningModeAutoStopTimeoutInMinutes': 60,
                    'ComputeTypeName': 'PERFORMANCE'
                },
                'Tags': [
                    {
                        'Key': 'Created-by',
                        'Value': 'Automation'
                    }
                ]
            }
        ]
    )

    res1 = response['FailedRequests']
    res2 = response['PendingRequests']
    
    if res1:
        length = len(res1)
        for key in range(length):
            #print(res1)
            username = res1[key]['WorkspaceRequest']['UserName']
            error = res1[key]['ErrorMessage']
            error_code = res1[key]['ErrorCode']
            if error_code == 'ResourceExists.WorkSpace':
                print("Workspace already exists for user {}".format(username))
            elif error_code == 'ResourceNotFound.User':
                print("The user '{}' could not be found in the directory.".format(username))
            else:
                print(error)

    if res2:
        sleep(30)
        length = len(res2)
        for key in range(length):
            username = res2[key]['UserName']
            print("Workspace is being created for user {}...\nMight take upto 20 minutes to be available.".format(username))


def main(event, context):

    ousers = oclient.get_users()
    wusers = get_workspaces()

    for wuser in wusers:
        #print(wuser)
        for ouser in ousers:
            #print(ouser.samaccountname)
            if str(ouser.samaccountname) in wuser:
                print(ouser.email)
        
        create_workspaces(ouser)