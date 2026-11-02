
import json
import base64
import time
from pprint import pprint,pformat
import logging
import datetime
# from datetime import datetime
import pytz
# import logging
# from pathlib import Path

import boto3
# import botocore.exceptions
from botocore.exceptions import ClientError
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

# from botocore.exceptions import ClientError


# ------------------------------------------------------------------------------------------------
def f_get_instance_name(f_instance_id):
    # When given an instance ID as str e.g. 'i-1234567', return the instance 'Name' from the name tag.
    ec2 = boto3.resource('ec2')
    ec2instance = ec2.Instance(f_instance_id)
    instancename = ''
    for tags in ec2instance.tags:
        if tags["Key"] == 'Name':
            instancename = tags["Value"]
    return instancename
# ------------------------------------------------------------------------------------------------



# -------------------------------------------------------------------------------------------------------
def f_get_secret(f_secret_name,f_region):

    secret_name = f_secret_name 
    region_name = f_region

    print(f' - secret name: {secret_name}')
    print(f' - region name: {region_name}')

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    # In this sample we only handle the specific exceptions for the 'GetSecretValue' API.
    # See https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
    # We rethrow the exception by default.
    get_secret_value_response = ''
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            # You provided a parameter value that is not valid for the current state of the resource.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            # We can't find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
    else:
        # Decrypts secret using the associated KMS CMK.
        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
        else:
            decoded_binary_secret = base64.b64decode(get_secret_value_response['SecretBinary'])


    s_returned_secret = get_secret_value_response["SecretString"]
    d_returned_secret = json.loads(s_returned_secret)

    userok      = d_returned_secret["user"]
    passik      = d_returned_secret["password"]
    instanceidk = d_returned_secret["instanceid"]
    urlik       = d_returned_secret["url"]

    return userok, passik, instanceidk, urlik
# ------------------------------------------------------------------------------------------------------------------------------------




# ------------------------------------------------------------------------------------------------------------------------------------
def f_upload_file(f_file_name_s_path, 
                  f_bucket, 
                  f_bucket_object_name):

    """Upload a file to an S3 f_bucket
    :param f_file_name_s_path: File to upload
    :param f_bucket: Bucket to upload to
    :param f_bucket_object_name: S3 object name with prefix.
    :return: True if file was uploaded, else False
    """

    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(f_file_name_s_path, 
                                         f_bucket, 
                                         f_bucket_object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True
# ------------------------------------------------------------------------------------------------------------------------------------




# ------------------------------------------------------------------------------------------------------------------------------------
def f_S3CheckFile(f_bucket, 
                  f_file_s_prefix, 
                  f_region):
    
    s3 = boto3.resource('s3', 
                        region_name=f_region)
    bucket = s3.Bucket(f_bucket)

    objs = list(bucket.objects.filter(Prefix=f_file_s_prefix))
    if (len(objs) > 0):
        print(f"File ({f_file_s_prefix}) exists !!!")
        return True
    else:
        print(f"File ({f_file_s_prefix}) doesn't exist !!!")
        return False
# ------------------------------------------------------------------------------------------------------------------------------------




# --------------------------------------------------------------------------------------------------
def f_populate_history_file(f_flag_file_bez_path,
                            f_flag_file_bucket,
                            f_flag_file_prefix,
                            l_datafiles_exist_in_bucket,
                            l_datafiles_dont_exist_in_bucket,
                            f_s3_history_file,
                            yes_no):
    
    print(f"bucket_with_path: {f_s3_history_file}")
    bucket_name = f_s3_history_file.split('/')[0]   
    print(f"bucket_name:     {bucket_name}")
    bucket_file_key = f_s3_history_file.split(f'{bucket_name}/')[1] # - info_for_all_lambdas/LambdaS3SQSAdditionToTrigger-i/mainframe-s3-prod-nz2sf/history.csv
    print(f"bucket_file_key: {bucket_file_key}")


    # est_zone = pytz.timezone("US/Eastern")
    # date_time_now     = datetime.datetime.now()
    # date_time_now_est = date_time_now.astimezone(est_zone)
    # date_time_now_est_str = date_time_now_est.strftime("%Y-%m-%d %H:%M:%S")

    # Get the current UTC time
    utc_time = datetime.datetime.utcnow()
    # Make it timezone-aware
    utc_time = pytz.utc.localize(utc_time)
    # Convert to US/Eastern timezone
    date_time_now_est = utc_time.astimezone(pytz.timezone("US/Eastern"))
    date_time_now_est_str = date_time_now_est.strftime("%Y-%m-%d %H:%M:%S")


    line_for_history_file = f"{date_time_now_est_str};{f_flag_file_bez_path};{yes_no};{f_flag_file_bucket};{f_flag_file_prefix};{len(l_datafiles_exist_in_bucket)};{len(l_datafiles_dont_exist_in_bucket)}"

    prom_all_datafiles_with_bar_delimeter = ''
    for cur_datafile in l_datafiles_exist_in_bucket:
        prom_all_datafiles_with_bar_delimeter = f"{prom_all_datafiles_with_bar_delimeter}|{cur_datafile}"
    line_for_history_file = f"{line_for_history_file};{prom_all_datafiles_with_bar_delimeter}"

    prom_all_datafiles_with_bar_delimeter = ''
    for cur_datafile in l_datafiles_dont_exist_in_bucket:
        prom_all_datafiles_with_bar_delimeter = f"{prom_all_datafiles_with_bar_delimeter}|{cur_datafile}"
    line_for_history_file = f"{line_for_history_file};{prom_all_datafiles_with_bar_delimeter}"


    #                                                                     | - amount of datafiles in bucket
    # date            ;flag-file    ;Bucket           ;prefix_and_file   ; ; ;list of datafiles in bucket        ;list of datafiles NOT in bucket 
    # 2024-12-31 22:40;Z_my.flag;yes;mainframe-s3-prod;nz2sf-dev/uploads/;4;2;my1.data|my2.data|my3.data|my4.data;my6.data|my7.data
    # 2024-12-31 22:40;Z_my.flag;no ;mainframe-s3-prod;nz2sf-dev/uploads/;4;2;my1.data|my2.data|my3.data|my4.data;my6.data|my7.data
    #                            ---                                        | - amount of datafiles NOT in bucket
    #                             |-yes (flag00 was created)
    #                             |-no  (flag00 was NOT created)

    # -- Now I need to add my just-formed line 'line_for_history_file' to history-file in S3
    # -- To add a line to a file in an S3 bucket using boto3, you need to:
    # --  - Download the file from S3.
    # --  - Modify its content by appending a line.
    # --  - Upload the modified file back to S3.    

    try:
        s3_client = boto3.client("s3")

        # Try to read the file
        try:
            response = s3_client.get_object(Bucket=bucket_name, Key=bucket_file_key)
            file_content = response['Body'].read().decode('utf-8')
        except s3_client.exceptions.NoSuchKey:
            print(f"File '{bucket_file_key}' does not exist. Creating it.")
            file_content = ""

        # Append the new line
        # file_content += line_for_history_file
        file_content = f"{file_content}\n{line_for_history_file}"

        # Upload the updated file
        s3_client.put_object(Bucket=bucket_name, Key=bucket_file_key, Body=file_content.encode('utf-8'))

        print(f"Successfully added a line to '{bucket_file_key}' in bucket '{bucket_name}'.")

    except NoCredentialsError:
        print("AWS credentials not found.")
        print(f"ERROR: HISTORY-FILE s3://{bucket_name}/{bucket_file_key} was NOT updated in the S3 Bucket.")
        exit()
    except PartialCredentialsError:
        print("Incomplete AWS credentials configuration.")
        print(f"ERROR: HISTORY-FILE s3://{bucket_name}/{bucket_file_key} was NOT updated in the S3 Bucket.")
        exit()
    except Exception as e:
        print(f"An error occurred: {e}")
        print(f"ERROR: HISTORY-FILE s3://{bucket_name}/{bucket_file_key} was NOT updated in the S3 Bucket.")
        exit()
# --------------------------------------------------------------------------------------------------


