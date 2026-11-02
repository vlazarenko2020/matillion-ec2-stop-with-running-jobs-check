

import os
import boto3
import botocore.exceptions
# from botocore.exceptions import ClientError
from Modules_common import f_add_to_message

# ------------------------------------------------------------------------------------------------------------------------------------
def f_send_email(f_subject,
                 f_body,
                 f_region,
                 f_recipient):
    # Replace sender@example.com with your "From" address.
    # This address must be verified with Amazon SES.
    # Read from the environment (not z_config) because the EC2Start image does not include z_config.py.
    SENDER = os.environ.get('MATILLION_EMAIL_SENDER')
    if not SENDER:
        raise RuntimeError("Environment variable 'MATILLION_EMAIL_SENDER' is not set. See project.env.example.")

    # If your account is still in the SES sandbox, recipient addresses must be verified.
    # MATILLION_EMAIL_ALWAYS_CC is optional: when set, every email is also sent to it.
    RECIPIENT_1 = os.environ.get('MATILLION_EMAIL_ALWAYS_CC')
    RECIPIENT_2 = f_recipient
    
    # Specify a configuration set. If you do not want to use a configuration
    # set, comment the following variable, and the 
    # ConfigurationSetName=CONFIGURATION_SET argument below.
#  CONFIGURATION_SET = "ConfigSet"
    
    # If necessary, replace us-west-2 with the AWS Region you're using for Amazon SES.
    AWS_REGION = f_region
    
    # The subject line for the email.
#   SUBJECT = "Amazon SES Test (SDK for Python)"
    SUBJECT = f_subject
    
    # The email body for recipients with non-HTML email clients.
    # BODY_TEXT = ("Amazon SES Test (Python)\r\n"
    #              "This email was sent with Amazon SES using the "
    #              "AWS SDK for Python (Boto)."
    #             )
    BODY_TEXT = f_body
                
    # The HTML body of the email.
    BODY_HTML = f"<html><head></head><body><pre>{f_body}</pre></body></html>"
    
    # The character encoding for the email.
    CHARSET = "UTF-8"
    
    # Create a new SES resource and specify a region.
    client = boto3.client('ses',
                          region_name=AWS_REGION)
    
    # Try to send the email.
    try:
        l_recipients_with_duplicates = [RECIPIENT_1, RECIPIENT_2,]  # -- not allow the same email to be sent twice
        l_recipients_no_duplicates = list(set(r for r in l_recipients_with_duplicates if r))

        response = client.send_email(
            Destination={
                'ToAddresses': l_recipients_no_duplicates,
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': CHARSET,
                        'Data': BODY_HTML,
                    },
                    'Text': {
                        'Charset': CHARSET,
                        'Data': BODY_TEXT,
                    },
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': SUBJECT,
                },
            },
            Source=SENDER,
            # If you are not using a configuration set, comment or delete the
            # following line
#            ConfigurationSetName=CONFIGURATION_SET,
        )
    # Display an error if something goes wrong. 
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])
# ------------------------------------------------------------------------------------------------------------------------------------

# ------------------------------------------------------------------------------------------------------------------------------------
def f_email_to_developers_with_running_jobs(f_var_to_add_text, 
                                            f_l_running_jobs_line_by_line, 
                                            f_region, 
                                            f_e_dev_prod, 
                                            f_instance_name, 
                                            f_email_to_pernell):
#   --- email to Jerry/Pernell when there are running jobs
    local_body = ""
    local_body = f_add_to_message(local_body, "\nList of Running Jobs:\n")
    for cur_line in f_l_running_jobs_line_by_line:
        body_line = f"   - {cur_line}"
        local_body = f_add_to_message(local_body, body_line)
    local_body = f_add_to_message(local_body, "\nRunning Jobs will prevent Scheduled Matillion Server shutdown.")
    local_subj = f"EC2-{f_e_dev_prod} Instance '{f_instance_name}' have '{str(len(f_l_running_jobs_line_by_line))}' running jobs."

    f_send_email(local_subj, 
                 local_body, 
                 f_region, 
                 f_email_to_pernell)
    
    f_var_to_add_text = f_add_to_message(f_var_to_add_text, f"{local_body}\nE-mail to Developers with list of running jobs was sent.")
    return f_var_to_add_text
# ------------------------------------------------------------------------------------------------------------------------------------
