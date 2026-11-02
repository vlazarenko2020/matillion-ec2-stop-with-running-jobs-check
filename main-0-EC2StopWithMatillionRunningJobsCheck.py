#!/bin/env python


import argparse
from lambda_function_EC2StopWithMatillionRunningJobsCheck import lambda_handler
import json
from pprint import pprint
from pathlib import Path


if __name__ == "__main__":


    folder_with_path = Path(".")

    l_event_json_files = []
    # for cur_file_with_path in folder_with_path.glob("event-*.json"):
    for cur_file_with_path in folder_with_path.glob("event-Mat-[TDP]*.json"):
        l_event_json_files.append(cur_file_with_path)

    k = 0
    print('Select JSON file to pass as an Event to the Lambda:')
    for cur_json_file in l_event_json_files:
        print(f" - {str(k)} - {cur_json_file}")
        k = k + 1

    user_input = input("What is your selection: ")    

    try:
        user_input_integer = int(user_input)
    except ValueError:
        print("\nERROR: Invalid input. You have to enter a number from listed range. Exiting.\n")
        exit()

    if user_input_integer >= 0 and user_input_integer < k:

        with open(l_event_json_files[user_input_integer], 'r') as fj:
            d_event_eventbridge = json.load(fj)  # -- d_event_eventbridge is a JSON format ready for EventBridge.
            print('\n..Event to send to Lambda:')
            pprint(d_event_eventbridge)
            print('')

            lambda_handler(d_event_eventbridge, "")

    else:
        print(f"\nERROR: You entered number ({user_input}) that is out of range of listed numbers. Exiting.\n")
        exit()

    # parser = argparse.ArgumentParser()
    # parser.add_argument('-s', choices=['DEV', 'PROD'], required=True)
    # args = parser.parse_args()

    # json_file_with_event = f"event_{args.s}.json"

    # with open(json_file_with_event, "r") as fj:
    #     d_event_eventbridge = json.load(fj)  # -- d_event_eventbridge is a JSON format ready for EventBridge.

    # # --- d_event_eventbridge
    # # ---
    # # {
    # # "e_bucket": "mainframe-s3-prod-order-hist",
    # # "e_prefix": "order-hist/",
    # # "e_bucket_with_folder": "mainframe-s3-prod-order-hist"
    # # }

    # print('\n..Event to send to Lambda:')
    # pprint(d_event_eventbridge)
    # print('')

    # lambda_handler(d_event_eventbridge, "")

