
import time
from pprint import pprint,pformat
import boto3
# import botocore.exceptions
from botocore.exceptions import ClientError
from botocore.exceptions import NoCredentialsError, PartialCredentialsError


# ------------------------------------------------------------------------------------------------------------------------------------
def f_Ec2InstanceStart_Logic(f_instance_id,
                             f_instance_name,
                             f_region):

    HOW_MANY_TIMES_REPEAT_LOOP = 30
    sleep_seconds = 5

    ec2 = boto3.client('ec2', 
                    region_name=f_region)

    # -----------------------------------------------------------
    r_ec2_status_json = ec2.describe_instance_status(InstanceIds=[f_instance_id], 
                                                     IncludeAllInstances=True)
    # -----------------------------------------------------------
    # pprint(r_ec2_status_json)
    r_status_initial = r_ec2_status_json['InstanceStatuses'][0]['InstanceState']['Name']


    # if r_status_initial == 'running':
    if r_status_initial in ['running', 'pending']:

            print(f"- Instance '{f_instance_name}' state is already '{r_status_initial}'.")
            print(f"- No need to start instance because it is already running.")
            r_ec2_status_json_pretty_format = pformat(r_ec2_status_json)
            print(f"Pretty 'start_instances' command output:\n {r_ec2_status_json_pretty_format}\n")
            return 'AlreadyRunning', r_ec2_status_json_pretty_format

    elif r_status_initial == 'stopping':

            print(f"- Instance '{f_instance_name}' state is '{r_status_initial}'.")
            print(f"- Will wait until its state will change to 'stop' and start it.")
            cur_loop_iteration = 1
            prom_ec2_status = r_status_initial
            while prom_ec2_status != 'stopped' and cur_loop_iteration <= HOW_MANY_TIMES_REPEAT_LOOP:
                time.sleep(sleep_seconds)
                # -----------------------------------------------------------
                prom_ec2_status_json = ec2.describe_instance_status(InstanceIds=[f_instance_id],
                                                                    IncludeAllInstances=True)
                # -----------------------------------------------------------
                # print("\nRaw JSON:\n{0}\n".format(prom_ec2_status_json))
                prom_ec2_status = prom_ec2_status_json["InstanceStatuses"][0]["InstanceState"]['Name']
                print(f"{str(cur_loop_iteration)}: Status: {prom_ec2_status}")
                cur_loop_iteration += 1

            r_status_new = f_Ec2InstanceStart(f_instance_id,
                                              f_instance_name,
                                              prom_ec2_status,
                                              ec2)

    elif r_status_initial == 'stopped':

            print(f"- Instance '{f_instance_name}' state is '{r_status_initial}'.")
            print(f"- Will start it.")
            r_status_new = f_Ec2InstanceStart(f_instance_id,
                                              f_instance_name,
                                              r_status_initial,
                                              ec2)

    elif r_status_initial in ['shutting-down', 'terminated']:   # 'shutting-down' - The instance is in the process of terminating permanently.
        r_ec2_status_json_pretty_format = pformat(r_ec2_status_json)
        print(f"Pretty 'start_instances' command output:\n {r_ec2_status_json_pretty_format}\n")
        print(f"ERROR: Instance '{f_instance_name}' state is {r_status_initial}.")
        return 'Terminated', r_ec2_status_json_pretty_format



    # -- this block works anly if Status was ['stopping', 'stopped']
    # -- EC2 was started so I need to wait until EC2 is running and complete this function.
    if r_status_new == 'running':

        print(f"Instance '{f_instance_name}' state is {r_status_new}.")
        r_ec2_status_json_pretty_format = pformat(r_ec2_status_json)
        print(f"Pretty 'start_instances' command output:\n {r_ec2_status_json_pretty_format}\n")
        return 'success', r_ec2_status_json_pretty_format

    else:    # -- r_status_new != 'running'

        print(f"Instance '{f_instance_name}' state is {r_status_new}.")
        print(f"Will wait for Instance '{f_instance_name}' state to become 'running'.")

        cur_loop_iteration = 1
        prom_ec2_status = r_status_new
        while prom_ec2_status != 'running' and cur_loop_iteration <= HOW_MANY_TIMES_REPEAT_LOOP:

            time.sleep(sleep_seconds)
            # -----------------------------------------------------------
            prom_ec2_status_json = ec2.describe_instance_status(InstanceIds=[f_instance_id],
                                                                IncludeAllInstances=True)
            # -----------------------------------------------------------

            # print("\nRaw JSON:\n{0}\n".format(prom_ec2_status_json))

            prom_ec2_status = prom_ec2_status_json["InstanceStatuses"][0]["InstanceState"]['Name']
            print(f"{str(cur_loop_iteration)}: Status: {prom_ec2_status}")

            cur_loop_iteration += 1

        prom_ec2_status_json_pretty_format = pformat(prom_ec2_status_json)
        if  prom_ec2_status != 'running':
            print(f"WARNING: Probably Instance '{f_instance_name}' was not started.")
            print(f"         Its current status: '{prom_ec2_status}'.")
            print(f"Pretty 'ec2.describe_instance_status' command output:\n {prom_ec2_status_json_pretty_format}\n")
            return 'StartFailure', prom_ec2_status_json_pretty_format
        else:   # -- after 10 checks (5 sec each) instance was confirm to be started.
            print(f"SUCCESS: Instance '{f_instance_name}' state became {prom_ec2_status}.")
            print(f"Pretty 'ec2.describe_instance_status' command output:\n {prom_ec2_status_json_pretty_format}\n")
            return 'StartSuccess', prom_ec2_status_json_pretty_format
# ------------------------------------------------------------------------------------------------------------------------------------

# ------------------------------------------------------------------------------------------------------------------------------------
def f_Ec2InstanceStart(f_instance_id,
                       f_instance_name,
                       r_status_initial,
                       ec2):        # -- ec2 defined in 'f_Ec2InstanceStart_Logic' function

    print(f"EC2 Instance '{f_instance_name}' status is '{r_status_initial}'.")
    print(f"EC2 Instance '{f_instance_name}' is going to be started.")
    # l_instance_ids = [ f_instance_id ]

    try:
        # ---------------------------------------------------------
        r_ec2_status_json = ec2.start_instances(InstanceIds=[f_instance_id])
        # ---------------------------------------------------------
        r_status_new = r_ec2_status_json['StartingInstances'][0]['CurrentState']['Name']
        print(f"Command to start EC2 {f_instance_name} was executed. Current state: {r_status_new}")
    except botocore.exceptions.NoCredentialsError:
        print("Error: AWS credentials not found. Configure them using 'aws configure'.")
        exit()
    except botocore.exceptions.PartialCredentialsError:
        print("Error: Incomplete AWS credentials provided. Check your AWS config.")
        exit()
    except botocore.exceptions.ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == "UnauthorizedOperation":
            print("Error: You do not have permission to start EC2 instances. Check your IAM policy.")
            exit()
        elif error_code == "InvalidInstanceID.NotFound":
            print(f"Error: Instance ID {f_instance_id} does not exist.")
            exit()
        elif error_code == "IncorrectInstanceState":
            print(f"WARNING: Instance {f_instance_id} is already running.")

            # -- I already checked that EC2 state is 'running'
            # -- So this error should not happened.    

        else:
            print(f"Unexpected ClientError: {e.response['Error']['Message']}")
            exit()
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        exit()

    return r_status_new
# ------------------------------------------------------------------------------------------------------------------------------------

