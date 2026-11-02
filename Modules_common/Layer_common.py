
import logging


# ------------------------------------------------------------------------------------------------------------------------------------
def f_add_to_message(f_var_to_add_text, 
                     f_text_to_add):
    
    print(f_text_to_add)
    return f"{f_var_to_add_text}\n{f_text_to_add}"
# ------------------------------------------------------------------------------------------------------------------------------------


# ------------------------------------------------------------------------------------------------------------------------------------
def f_print_running_jobs(f_var_to_add_text, 
                         list_of_lines):

    for cur_line in list_of_lines:
        cur_text = f"   - {cur_line}"

        f_var_to_add_text = f_add_to_message(f_var_to_add_text, 
                                             cur_text)
    return f_var_to_add_text
# ------------------------------------------------------------------------------------------------------------------------------------


# ------------------------------------------------------------------------------------------------------------------------------------
def f_process_return_status(f_return_status, 
                            f_return_formated_boto, 
                            f_e_dev_prod, 
                            f_instance_name, 
                            f_subj8, 
                            f_body8):

    if f_return_status == 'StartFailure':
        f_subj8 = f_add_to_message(f_subj8, f"Cannot start EC2-{f_e_dev_prod} instance '{f_instance_name}'")
        f_body8 = f_add_to_message(f_body8, f"Cannot start EC2-{f_e_dev_prod} instance '{f_instance_name}'")
        f_body8 = f_add_to_message(f_body8, f_return_formated_boto)
    elif f_return_status == 'StartSuccess':
        f_subj8 = f_add_to_message(f_subj8, f"EC2-{f_e_dev_prod} Instance '{f_instance_name}' was started successfully.")
        f_body8 = f_add_to_message(f_body8, f"EC2-{f_e_dev_prod} Instance '{f_instance_name}' was started successfully.")
        f_body8 = f_add_to_message(f_body8, f_return_formated_boto)
    if f_return_status == 'StopFailure':
        f_subj8 = f_add_to_message(f_subj8, f"Cannot stop EC2-{f_e_dev_prod} instance '{f_instance_name}'")
        f_body8 = f_add_to_message(f_body8, f"Cannot stop EC2-{f_e_dev_prod} instance '{f_instance_name}'")
        f_body8 = f_add_to_message(f_body8, f_return_formated_boto)
    elif f_return_status == 'StopSuccess':
        f_subj8 = f_add_to_message(f_subj8, f"EC2-{f_e_dev_prod} Instance '{f_instance_name}' was stopped successfully.")
        f_body8 = f_add_to_message(f_body8, f"EC2-{f_e_dev_prod} Instance '{f_instance_name}' was stopped successfully.")
        f_body8 = f_add_to_message(f_body8, f_return_formated_boto)
    elif f_return_status == 'AlreadyRunning':
        f_subj8 = f_add_to_message(f_subj8, f"EC2-{f_e_dev_prod} Instance '{f_instance_name}' was already running.")
        f_body8 = f_add_to_message(f_body8, f"EC2-{f_e_dev_prod} Instance '{f_instance_name}' was already running.")
        f_body8 = f_add_to_message(f_body8, f_return_formated_boto)
    elif f_return_status == 'AlreadyStopped':
        f_subj8 = f_add_to_message(f_subj8, f"EC2-{f_e_dev_prod} Instance '{f_instance_name}' was already stopped.")
        f_body8 = f_add_to_message(f_body8, f"EC2-{f_e_dev_prod} Instance '{f_instance_name}' was already stopped.")
        f_body8 = f_add_to_message(f_body8, f_return_formated_boto)
    elif f_return_status == 'Terminated':
        f_subj8 = f_add_to_message(f_subj8, f"EC2-{f_e_dev_prod} Instance '{f_instance_name}' was terminated.")
        f_body8 = f_add_to_message(f_body8, f"EC2-{f_e_dev_prod} Instance '{f_instance_name}' was sterminated.")
        f_body8 = f_add_to_message(f_body8, f_return_formated_boto)

    return f_subj8, f_body8    
# ------------------------------------------------------------------------------------------------------------------------------------


