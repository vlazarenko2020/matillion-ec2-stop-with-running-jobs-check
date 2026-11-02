
import json
from time import sleep
import logging
import boto3


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# logger.warning(f"--\nLog Level in Module (check_ec2_status_not_state): {logger.level}\n--")


def check_ec2_status_not_state(f_instance_ID,
                               f_SECONDS_TO_CHECK_STATUS):

    logger.warning(f'..Checking Status of EC2 Instance with InstaceID: {f_instance_ID}')

    ec2 = boto3.client('ec2')

    period_sec = 5
    if f_SECONDS_TO_CHECK_STATUS > 5:
        attempts = f_SECONDS_TO_CHECK_STATUS // period_sec
    else:
        attempts = 1

    status = None
    i = 1
    while (status != 'ok' and i <= attempts):
 
        try:
            status_response = ec2.describe_instance_status(
                InstanceIds=[f_instance_ID, ],
                DryRun=False,
                IncludeAllInstances=True
            )
        except Exception as e:
            print("An error occurred:", e)
            exit()
 
        status = status_response['InstanceStatuses'][0]['SystemStatus']['Status']
        logger.warning(f'Status ({str(i)} of {str(attempts)}): {status}')
        if status == 'ok':
            break
        else:
            if attempts != 1:
                sleep(period_sec)
            i += 1

    logger.warning(f'Final EC2 Instance Status: {status}')
    logger.debug(json.dumps(status_response, indent=1))

    if status == 'ok':
        return True
    else:
        return False




if __name__ == "__main__":

    # PROD_DEV = 'PROD'
    # INSTANCE_ID = "i-0123456789abcdef0"

    PROD_DEV = 'DEV'
    INSTANCE_ID = "i-0123456789abcdef0"   # -- replace with a real instance ID to run this test block

    f_SECONDS_TO_CHECK_STATUS = 0    
    ec2_status = check_ec2_status_not_state(INSTANCE_ID,
                                            f_SECONDS_TO_CHECK_STATUS)

    if ec2_status:
        logger.warning(f'{PROD_DEV}-EC2 Instance ({INSTANCE_ID}) running-status is {ec2_status}. Will check Jobs Status.\n')
    else:
        logger.warning(f'{PROD_DEV}-EC2 Instance ({INSTANCE_ID}) running-status is {ec2_status}. Instance is DOWN. Exiting without API queries.\n')
        exit()


