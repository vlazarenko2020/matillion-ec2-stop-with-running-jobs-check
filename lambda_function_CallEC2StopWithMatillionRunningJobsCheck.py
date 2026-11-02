#!/home/linuxbrew/.linuxbrew/bin/python3

import os, json, configparser
from pprint import pprint
import boto3


F_TO_CALL = None   # -- set from 'e_lambda_arn_to_call' in the ini file
CONFIG_FILE= 'z_config_CallEC2StopWithMatillionRunningJobsCheck.ini'

lambda_client = boto3.client('lambda')
 
def lambda_handler(event,context):

    # {
    # "Records": [
    #     {
    #     "eventVersion": "2.1",
    #     "eventSource": "aws:s3",
    #     "awsRegion": "us-east-1",
    #     "eventTime": "2025-02-11T12:34:56.789Z",
    #     "eventName": "ObjectCreated:Put",
    #     "userIdentity": {
    #         "principalId": "AWS:EXAMPLEUSER"
    #     },
    #     "requestParameters": {
    #         "sourceIPAddress": "192.0.2.1"
    #     },
    #     "responseElements": {
    #         "x-amz-request-id": "EXAMPLE123456789",
    #         "x-amz-id-2": "EXAMPLEIDSTRING"
    #     },
    #     "s3": {
    #         "s3SchemaVersion": "1.0",
    #         "configurationId": "example-event-configuration",
    #         "bucket": {
    #         "name": "my-example-bucket",
    #         "ownerIdentity": {
    #             "principalId": "EXAMPLEOWNER"
    #         },
    #         "arn": "arn:aws:s3:::my-example-bucket"
    #         },
    #         "object": {
    #         "key": "example-folder/Matillion-TEST.flag",
    #         "size": 12345,
    #         "eTag": "d41d8cd98f00b204e9800998ecf8427e",
    #         "sequencer": "0055AED6DCD90281E5"
    #         }
    #     }
    #     }
    # ]
    # }


    filename_1 = os.path.basename(event["Records"][0]["s3"]["object"]["key"])

    print('... Event:')
    pprint(event)

    print('... Context:')
    pprint(context)

    print('...')
    print(f'File that arrived to S3:\n    {filename_1}')
    print('...')


    if filename_1 == "Matillion-PROD.flag":
        PROD_DEV = "PROD"
    elif filename_1 == "Matillion-DEV.flag":
        PROD_DEV = "DEV"
    elif filename_1 == "Matillion-TEST.flag":
        PROD_DEV = "TEST"
    else: 
        print('--')
        print(f'Exiting.\nFilename must be:\n  - Matillion-PROD.flag\n  or\n  - Matillion-DEV.flag')
        print('--')
        exit()




    if os.path.isfile(CONFIG_FILE):     # - 'z_config_CallEC2StopWithMatillionRunningJobsCheck.ini'
        parser = configparser.ConfigParser()
        parser.read(CONFIG_FILE)
        inputParams = parser.get('system', PROD_DEV)

        print('\n..Event (as string) from ini file:')
        print(inputParams)
        print('-----')

        d_inputParams = json.loads(inputParams)  # -- converting string to dictionary (json)

        print('\n..Event (as dictionary) from ini file:')
        pprint(d_inputParams)
        print('')


        # F_TO_CALL = d_inputParams["e_system"]["e_lambda_arn_to_call"]
        F_TO_CALL = d_inputParams["e_lambda_arn_to_call"]

        print('-----')
        print(f"Lambda to call: {F_TO_CALL}")
        print('-----')


        # r = lambda_client.invoke(
        #     FunctionName = F_TO_CALL,
        #     InvocationType = 'RequestResponse',
        #     Payload = inputParams
        # )

        # print('===')
        # print(r)
        # print('===')


        # status_1 = r['StatusCode']
    
        # print('===')
        # print(f'StatusCode: {status_1}')
        # print('===')

    else:
        print('--')
        print(f"Config File ({CONFIG_FILE}) doesn't exist. Exiting.")
        print('--')
