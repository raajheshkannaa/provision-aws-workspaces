import boto3
from botocore.exceptions import ClientError
from botocore.vendored import requests
import json

# Get assigned users list and details from the application - Amazon Workspaces
apiKey = "" # OKTA API KEY
app_url = "" # OKTA APP URL FOR WORKSPACES # <https://company.okta.com/api/v1/apps/12345678911234567890/users>

#app_groups_url = "" # OKTA APP GROUP URL FOR WORKSPACES # https://company.okta.com/api/v1/apps/12345678911234567890/group

api_token = "SSWS "+ apiKey
headers = {'Accept':'application/json','Content-Type':'application/json','Authorization':api_token}

def getappusers(url):
    response = requests.request("GET", url, headers=headers)
    responseJSON = json.dumps(response.json())
    responseList = json.loads(responseJSON)
    returnResponseList = []
    returnResponseList = returnResponseList + responseList

    if "errorCode" in responseJSON:

        print("\nYou encountered following Error: \n")
        print(responseJSON)
        print("\n")

        return "Error"
    else:
        headerLink= response.headers["Link"]
        count = 1
  
        while str(headerLink).find("rel=\"next\"") > -1:

            linkItems = str(headerLink).split(",")

            nextCursorLink = ""
            for link in linkItems:

                if str(link).find("rel=\"next\"") > -1:
                    nextCursorLink = str(link)

            nextLink = str(nextCursorLink.split(";")[0]).strip()
            nextLink = nextLink[1:]
            nextLink = nextLink[:-1]

            url = nextLink

            print("\nCalling Paginated Url " + str(url) + "  " + str(count) +  " \n")
            response = requests.request("GET", url, headers=headers)
            responseJSON = json.dumps(response.json())
            responseList = json.loads(responseJSON)
            returnResponseList = returnResponseList + responseList
            headerLink= response.headers["Link"]
            count += 1
        
        returnJSON = json.dumps(responseJSON)
        return returnResponseList
        

client = boto3.client('workspaces')

def get_workspaces():
    response = client.describe_workspaces(
        DirectoryId = '<AWS WORKSPACES DIRECTORY ID>' # AWS DIRECTORY ID USED FOR WORKSPACES # THIS IS A REGIONAL SERVICE FYI
    )

    resources = response['Workspaces']

    length = len(resources)
    
    for key in range(length):
        username = resources[key]['UserName']
        wsid = resources[key]['WorkspaceId']
        state = resources[key]['State']
        wsprop = resources[key]['WorkspaceProperties']['RunningMode']
        print(username, wsid, state, wsprop)


def create_workspaces(username):
    response = client.create_workspaces(
        Workspaces = [
            {
                'DirectoryId': '<AWS WORKSPACES DIRECTORY ID>', # AWS DIRECTORY ID USED FOR WORKSPACES # THIS IS A REGIONAL SERVICE FYI
                'UserName': username,
                'BundleId': '<AWS WORKSPACES IMAGE BUNDLE ID>', # AWS WORKSPACES IMAGE BUNDLE ID USED TO PROVISION
                'VolumeEncryptionKey': '<AWS KMS KEY>', # AWS KMS KEY USED FOR ENCRYPTING BOTH THE ROOT and USER DRIVES`
                'UserVolumeEncryptionEnabled': True,
                'RootVolumeEncryptionEnabled': True,
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
                print("Workspace already exists for user {}.".format(username))
            elif error_code == 'ResourceNotFound.User':
                print("The user '{}' could not be found in the directory.".format(username))
            else:
                print(error)

    if res2:
        length = len(res2)
        for key in range(length):
            username = res2[key]['UserName']
            print("Workspace is being created for user {}...\nMight take upto 20 minutes to be available.".format(username))


def send_email(address):
    ses_client = boto3.client('ses')
    sender = 'WorkSpaces <no-reply-workspaces@l33t.com>'
    recipient = address
    subject = 'Amazon WorkSpaces'
    charset = "UTF-8"
    config = 'ConfigSet'
    # message body
    body = (
        "Dear Amazon WorkSpaces User,\r\n\n"
        "A new Amazon WorkSpace has been provided for you. Follow the steps below to quickly get up and running with your WorkSpace:\n"
        "1. Download and install a WorkSpaces Client for your favorite devices: https://clients.amazonworkspaces.com/\n"
        "2. Launch the client and enter the following registration code: <REGISTRATION CODE>\n"
        "3. Login with your domain username and password.\n\n"

        "If you have any issues connecting to your WorkSpace, please contact your administrator.\n\n"

        "Sincerely,\n"
        "l33tAdm1n\n"
        
        )

    try:
        response = ses_client.send_email(
            Source = sender,
            Destination = {
                'ToAddresses': [
                    recipient,
                ]
            },
            Message = {
                'Body': {
                    'Text': {
                        'Charset': charset,
                        'Data': body
                    },
                },
            'Subject': {
                'Charset': charset,
                'Data': subject,
                },
            }
            )

    # Display an error if something goes wrong.	
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])


def main(event, context):

    users = getappusers(app_url)
    
    # traverse each user from this list and get their username & email
    for item in users:
        #print(item.keys())
        for key in item:
            if key == 'credentials':
                for name in item[key]:
                    username = item[key][name]

            if key == '_links':
                for link in item[key]:
                    if link == 'user':
                        for href in item[key][link]:
                            user_url = (item[key][link][href])
                            response = requests.request("GET", user_url, headers=headers)
                            user_details = response.json()

                            for item in user_details:
                                if item == 'profile':
                                    for key in user_details[item]:
                                        if key == 'email':
                                            email = user_details[item][key]
                                            
        #print(username, email)
        create_workspaces(username)
        send_email(email)