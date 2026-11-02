
from pprint import pprint,pformat
from Modules_common import f_get_secret
from Modules_common import f_get_instance_name
from Modules_common import f_send_email
from Modules_common import f_process_return_status
from Modules_start import f_Ec2InstanceStart_Logic

# ------------------------------------------------------------------------------------------------------------------------------------
def lambda_handler(event, 
                   context):

    print('---\n--- Event:')
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
#   e_force_stop        = event["e_force"]    # yes, no -- not used for EC2Start
    email_to            = event["e_email_to"]
    email_to_developers = event["e_email_to_developers"]


# --------------
    v_secret_name = '/matillion/' + e_dev_prod.lower()
    print(f"\n...Getting secret '{v_secret_name}' from the Secret Manager.")
    username1, password1, instanceid1, url1 = f_get_secret(v_secret_name,
                                                                    e_region)
    print(f"Secret is  {v_secret_name}:{username1}:'XXXXXXXXXX':{instanceid1}:{url1}")
    # --------------


    # -------------------------------------------------------------------------------
    instance_name = f_get_instance_name(instanceid1)
    # -------------------------------------------------------------------------------

    print(f"\n...Starting EC2 Instance '{instance_name}'.")
    
    # -------------------------------------------------------------------------------
    return_status, return_formated_boto = f_Ec2InstanceStart_Logic(instanceid1,
                                                                   instance_name,
                                                                   e_region)
    # -------------------------------------------------------------------------------

    # ----------------------------------------------------------------------------------------------------
    subject, body = f_process_return_status(return_status, 
                                            return_formated_boto, 
                                            e_dev_prod,
                                            instance_name, 
                                            '',     # -- beginning of subject
                                            '')     # -- beginning of body
    # ----------------------------------------------------------------------------------------------------


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

    return "success"
# ------------------------------------------------------------------------------------------------------------------------------------


