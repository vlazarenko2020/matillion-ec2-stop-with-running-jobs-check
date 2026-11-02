
from pprint import pprint,pformat
import requests
import urllib3
import json
from datetime import datetime
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from Modules_common import f_add_to_message
from Modules_common import f_S3CheckFile
from Modules_common import f_print_running_jobs
from Modules_common import f_upload_file
from Modules_common import f_get_secret
from Modules_common import f_get_instance_name
from Modules_common import f_process_return_status
from Modules_common import f_send_email
from Modules_common import f_email_to_developers_with_running_jobs
from Modules_stop import f_EC2InstanceStop_Logic
from Modules_stop import check_ec2_status_not_state

import z_config as zz

SECONDS_TO_CHECK_STATUS = 0


def lambda_handler(event, context):

    now = datetime.now()
    datetime_str = now.strftime("%Y-%m-%d %H:%M:%S")

    print(f'---\n---\n--- {datetime_str}\n--- Event:')
    pprint(event)
    print('---')

    # {
    # "e_system": "DEV",
    # "e_region": "us-east-1",
    # "e_force": "no",
    # "e_email_to": "user@example.com",
    # "e_email_to_developers": "user@example.com"
    # }
    
    e_region            = event["e_region"]   # us-east-1
    e_dev_prod          = event["e_system"]   # TEST, DEV, PROD
    e_force_stop        = event["e_force"]    # yes, no
    email_to            = event["e_email_to"]
    email_to_developers = event["e_email_to_developers"]

    if e_force_stop == 'yes':
        forced_shutdown_true_false = True
    else:
        forced_shutdown_true_false = False

    print(f"Force Stop Setting: {e_force_stop}")


    # --------------
    v_secret_name = '/matillion/' + e_dev_prod.lower()
    print(f"\n...Getting secret '{v_secret_name}' from the Secret Manager.")
    username1, password1, instanceid1, url1 = f_get_secret(v_secret_name,
                                                           e_region)
    print(f"Secret is  {v_secret_name}:{username1}:'XXXXXXXXXX':{instanceid1}:{url1}")
    # --------------



    instance_name = f_get_instance_name(instanceid1)
    print('...\n...\n...')
    print("InstanceID:    {0}".format(instanceid1))
    print("Instance Name: {0}".format(instance_name))
    print('...\n...\n...')


    # ec2 = boto3.client('ec2')
    ec2_status = check_ec2_status_not_state(instanceid1,
                                            SECONDS_TO_CHECK_STATUS)
    if ec2_status:
        print(f'{e_dev_prod}-EC2 Instance ({instanceid1}) running-status is {ec2_status}. Will check Jobs Status.\n')
    else:
        # body = f_add_to_message(body, f"{e_dev_prod}-EC2 Instance ({instance_name}) running-status is {ec2_status}. Instance is DOWN. Exiting without API queries.\n")   
        body = f_add_to_message("", f"Email to {zz.admin_email} only.")
        body = f_add_to_message(body, f"{e_dev_prod}-EC2 Instance ({instance_name}) running-status is {ec2_status}. Instance is DOWN. Exiting without API queries.\n")   
        # subject = f_add_to_message(subject, f"EC2-{e_dev_prod} Instance ({instance_name}) was already stopped.") 
        subject = f_add_to_message("", f"EC2-{e_dev_prod} Instance ({instance_name}) was already stopped.") 

        subject_bez_EndOfLine = subject.replace('\n','')

        f_send_email(subject_bez_EndOfLine, 
                     body, 
                     e_region, 
                     zz.admin_email)
        return {
                "statusCode": 200,
                "body": json.dumps("SUCCESS: Instance is DOWN. Exiting without API queries")
                }




    URL_BASE          = url1
    URL_PROJECT_GROUP = URL_BASE + '/group'
    HEADER = { 'Accept': 'application/json', 'Content-Type': 'application/json' }

    flag = "success"
    try:
        r_project_group_all = requests.get(URL_PROJECT_GROUP,
                                           timeout=10, 
                                           auth=(username1, password1), 
                                           verify=False)
        print(f"Matillion-{e_dev_prod} Project Group:")
        pprint(r_project_group_all.json())
        print('')
        flag = "success"
    except requests.exceptions.ConnectionError:
        prom_error = f"Failed to connect to the API server '{URL_PROJECT_GROUP}'. The server might be down."
        print(prom_error)
        flag = "error"

    except requests.exceptions.Timeout:
        prom_error = f"Request timed out. The server '{URL_PROJECT_GROUP}' might be slow or unresponsive."
        print(prom_error)
        flag = "error"

    except requests.exceptions.HTTPError as err:
        prom_error = f"HTTP error occurred: {err}"
        print(prom_error)
        flag = "error"

    except requests.exceptions.RequestException as err:
        prom_error = f"An error occurred while making the request: {err}"
        print(prom_error)
        flag = "error"



    # -----------------------------------------------------------------------------------------------------------------------
    if flag == "error":
        body = prom_error
        body = f_add_to_message(body, f"As API cannot be reached, EC2-{e_dev_prod} Instance '{instance_name}' will be stopped without running jobs check.\n")
        # subject = f"EC2-{e_dev_prod} Instance '{instance_name}' was stopped but its API was timed-out."
        subject_beginning = f"WARNING: EC2-{e_dev_prod} Instance '{instance_name}' API was timed-out. "
        # ----------------------------------------------------------------------------------------------------
        return_status, return_formated_boto = f_EC2InstanceStop_Logic(instanceid1, 
                                                                      instance_name,
                                                                      e_region)
        # ----------------------------------------------------------------------------------------------------
        subject, body = f_process_return_status(return_status, 
                                                return_formated_boto, 
                                                e_dev_prod,
                                                instance_name, 
                                                subject_beginning,    # -- beginning of subject
                                                body)       # -- beginning of body
        # ----------------------------------------------------------------------------------------------------
        subject_bez_EndOfLine = subject.replace('\n','')
        # ----------------------------------------------------------------------------------------------------
        f_send_email(subject_bez_EndOfLine, 
                    body, 
                    e_region, 
                    email_to)
        # ----------------------------------------------------------------------------------------------------
        return {
                "statusCode": 200,
                "body": json.dumps("SUCCESS: API cannot be reached. Instance was stopped.")
                }
    # -----------------------------------------------------------------------------------------------------------------------



    FLAG = 0     
    l_running_jobs_line_by_line = [] 
    for cur_p_group in r_project_group_all.json():
        print(cur_p_group)
            
        URL_PROJECTS = f"{URL_BASE}/group/name/{cur_p_group}/project"
    
        r_project_all = requests.get(URL_PROJECTS, 
                                     auth=(username1, password1), 
                                     verify=False)
    
        for cur_project in r_project_all.json():
            print("   Projects:")
            print("    " + cur_project)
    
            URL_JOBS = f"{URL_BASE}/group/name/{cur_p_group}/project/name/{cur_project}/task/running"
#           print(URL_JOBS)
    
            r_r_job_all = requests.get(URL_JOBS, 
                                       auth=(username1, password1), 
                                       verify=False)
#           print(r_r_job_all.json())
    
            for cur_job in r_r_job_all.json():
                # line9 = "Job \"{0}\"/\"{1}\"/\"{2}\" is \"{3}\".".format(cur_job["groupName"],cur_job["projectName"],cur_job["jobName"],cur_job["state"])
                line9 = f'Job "{cur_job["groupName"]}"/"{cur_job["projectName"]}"/"{cur_job["jobName"]}" is "{cur_job["state"]}'
                print(f'      {line9}')
                l_running_jobs_line_by_line.append(line9)
                if cur_job["state"] == "RUNNING" or cur_job["state"] == "QUEUED":
                    FLAG += 1

    kol_running_jobs = FLAG
    print('...')
    print(f"Number of Running Jobs: {str(kol_running_jobs)}")
    print('...')

    s3_flag_dry_run_s_prefix = f"{zz.s3_prefix_beginning}{e_dev_prod}/{zz.s3_flag_dry_run}"
    # 'Matillion-TEST/Dry-Run.txt'

    dry_run_s3_file_exists = f_S3CheckFile( zz.s3_bucket,
                                            s3_flag_dry_run_s_prefix,
                                            e_region)
    #                                                ||||||||||||||||||||||  - '- Matillion-'
    s3_flag_shutdown_allowed_for_ecops_s_prefix = f"{zz.s3_prefix_beginning}{e_dev_prod}/{zz.s3_flag_shutdown_allowed_for_ecops_bez_path}"
    #                                                                        ||||||||||   |||||||||||||||||||||||||||||||||||||||||||||| - 'Shutdown_With_Running_Jobs-Allowed-ECops_Managed_File.txt'
    #                                                                        |||||||||| - DEV/PROD/TEST
    # - Matillion-TEST/Shutdown_With_Running_Jobs-Allowed-ECops_Managed_File.txt

    allow_shutdown_s3_ecops_file_exists = f_S3CheckFile(zz.s3_bucket,
                                                        s3_flag_shutdown_allowed_for_ecops_s_prefix,    # - Matillion-TEST/Shutdown_With_Running_Jobs-Allowed-ECops_Managed_File.txt
                                                        e_region)

    body = ''
    subject = ''

    if kol_running_jobs == 0:

        body = f_add_to_message(body, "There are no running jobs were found.")

        if dry_run_s3_file_exists:
            body = f_add_to_message(body, "'DRY-RUN' file was found.")
            body = f_add_to_message(body, "'DRY-RUN' file prevents shutdown to allow Dry-Run testing.")
            body = f_add_to_message(body, f"EC2-{e_dev_prod} Instance '{instance_name}' will NOT be stopped.")
            subject = f_add_to_message(subject, f"EC2-{e_dev_prod} Instance '{instance_name}' was NOT stopped.")
        else:
            body = f_add_to_message(body, "'DRY-RUN' file was NOT found in S3 Bucket.")
            body = f_add_to_message(body, "'DRY-RUN' file absence allows shutdown.")
            body = f_add_to_message(body, f"EC2-{e_dev_prod} Instance '{instance_name}' will be stopped.")

            # ----------------------------------------------------------------------------------------------------
            return_status, return_formated_boto = f_EC2InstanceStop_Logic(instanceid1, 
                                                                          instance_name,
                                                                          e_region)
            # ----------------------------------------------------------------------------------------------------
            subject, body = f_process_return_status(return_status, 
                                                    return_formated_boto, 
                                                    e_dev_prod,instance_name, 
                                                    subject, 
                                                    body)
            # body = f_add_to_message(body, body)
            # subject = f_add_to_message(subject, subject8)

    else:   # kol_running_jobs != 0:

        body = f_add_to_message(body, f"There are '{str(FLAG)}' running jobs.")
        f_print_running_jobs(body, 
                             l_running_jobs_line_by_line)
        body = f_email_to_developers_with_running_jobs(body, 
                                                        l_running_jobs_line_by_line, 
                                                        e_region, 
                                                        e_dev_prod, 
                                                        instance_name, 
                                                        email_to_developers)
        # body = f_add_to_message(body, body_prom)
        
        # kol_running_jobs != 0                                         
        if forced_shutdown_true_false:   # - True. Forced shutdown. Don't pay attention on running jobs. Just shutdown.

            body = f_add_to_message(body, "Lambda was called with 'Force-Shutdown=Yes' JSON.")
            body = f_add_to_message(body, "It means killing Running Jobs during shutdown.")

            if allow_shutdown_s3_ecops_file_exists: # - True - file "Matillion-TEST/Shutdown_With_Running_Jobs-Allowed-ECops_Managed_File.txt" exists in S3 
                                                    # - True - (usually for DEV and TEST) to allow shutdown with running jobs

                body = f_add_to_message(body, "'Allow-Shutdown-S3-ECops-File' was found in S3 Bucket.")
                body = f_add_to_message(body, "'Allow-Shutdown-S3-ECops-File' allows shutdown.")

                if dry_run_s3_file_exists:
                    body = f_add_to_message(body, "'DRY-RUN' file was found.")
                    body = f_add_to_message(body, "This S3 file prevents shutdown to allow Dry-Run testing.")
                    subject = f_add_to_message(subject, f"EC2-{e_dev_prod} Instance ({instance_name}) was NOT stopped.")
                else:
                    body = f_add_to_message(body, "'DRY-RUN' file was NOT found in S3 Bucket.")
                    body = f_add_to_message(body, "'DRY-RUN' file absence allows shutdown.")

                    # ----------------------------------------------------------------------------------------------------
                    return_status, return_formated_boto = f_EC2InstanceStop_Logic(instanceid1, 
                                                                                  instance_name,
                                                                                  e_region)
                    # ----------------------------------------------------------------------------------------------------
                    subject, body = f_process_return_status(return_status, 
                                                            return_formated_boto, 
                                                            e_dev_prod,
                                                            instance_name, 
                                                            subject,    # -- beginning of subject
                                                            body)       # -- beginning of body
                    # body = f_add_to_message(body, body)
                    # subject = f_add_to_message(subject, subject8)

            else:    # - False - file "Matillion-TEST/Shutdown_With_Running_Jobs-Allowed-ECops_Managed_File.txt" doesn't exists in S3
                     # - False - (usually for PROD) to NOT allow shutdown with running jobs
                body = f_add_to_message(body, "'Allow-Shutdown-S3-ECops-File' was NOT found.")
                body = f_add_to_message(body, "It means ECOPS deleted 'Allow-Shutdown-S3-ECops-File' to prevent shutdown.")
                body = f_add_to_message(body, "Will pre-create new 'Allow-Shutdown-S3-ECops-File' to allow shutdown during next run.")
                subject = f_add_to_message(subject, f"EC2-{e_dev_prod} Instance ({instance_name}) was NOT stopped.")
                
                with open(zz.s3_flag_shutdown_allowed_for_ecops_s_path, 'w') as f:
                    f.write("SOMETHING.")
                try:
                    f_upload_file(zz.s3_flag_shutdown_allowed_for_ecops_s_path, 
                                  zz.s3_bucket, 
                                  s3_flag_shutdown_allowed_for_ecops_s_prefix)
                    body = f_add_to_message(body, f"S3 file ({s3_flag_shutdown_allowed_for_ecops_s_prefix}) was created in S3 Bucket ({zz.s3_bucket}).")
                except:
                    body = f_add_to_message(body, f"ERROR: Can not create file ({s3_flag_shutdown_allowed_for_ecops_s_prefix}) in S3 Bucket ({zz.s3_bucket}).")
                 
        else:    # - False. Not Forced shutdown. Allow running jobs to complete.
            body = f_add_to_message(body, "Lambda was called with 'Force-Shutdown=No' JSON.")
            body = f_add_to_message(body, "It means allowing Running Jobs to complete.")
            # body = f_add_to_message(body, "No shutdown. So ECops cannot manage shutdown.")   
            body = f_add_to_message(body, "No need to check 'DRY-RUN' file presence because there will be no shutdown.")   
            subject = f_add_to_message(subject, f"EC2-{e_dev_prod} Instance ({instance_name}) was NOT stopped.") 

    subject_bez_EndOfLine = subject.replace('\n','')

    # print('------')
    # print('Subject: {0}'.format(subject_bez_EndOfLine))
    # print('------')
    # print('Body: {0}'.format(body))
    # print('------')

    f_send_email(subject_bez_EndOfLine, 
                 body, 
                 e_region, 
                 email_to)
