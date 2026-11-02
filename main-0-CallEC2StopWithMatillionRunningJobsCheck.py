#!/bin/env python

from lambda_function_CallEC2StopWithMatillionRunningJobsCheck import lambda_handler
import json
from pprint import pprint


event_json_file_file_arrived_to_s3 = "event-CallEC2StopWithMatillionRunningJobsCheck.json"

if __name__ == "__main__":

    l_systems_to_select = ["PROD","DEV","TEST"]

    k = 0
    print('Select system:')
    for cur_system in l_systems_to_select:
        print(f" - {str(k)} - {cur_system}")
        k = k + 1

    user_input = input("What is your selection: ")    

    try:
        user_input_integer = int(user_input)
    except ValueError:
        print("\nERROR: Invalid input. You have to enter a number from listed range. Exiting.\n")
        exit()

    if user_input_integer >= 0 and user_input_integer < k:

        with open(event_json_file_file_arrived_to_s3, 'r') as fj:
            d_event_eventbridge = json.load(fj)  # -- d_event_eventbridge is a JSON format ready for EventBridge.
            print('\n..Event to send to Lambda:')
            pprint(d_event_eventbridge)
            print('')

            lambda_handler(d_event_eventbridge, "")

    else:
        print(f"\nERROR: You entered number ({user_input}) that is out of range of listed numbers. Exiting.\n")
        exit()

