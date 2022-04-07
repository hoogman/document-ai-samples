#!/usr/bin/python

import argparse, json
from utils.processor_utils import create_processor, delete_processor, list_processors_types, enable_service_api, list_service_apis

parser = argparse.ArgumentParser()
parser.add_argument("--project_number", help="Google Cloud Project Number", type=int, required=True)
parser.add_argument("--location", help="Services Deployment Location", type=str)
parser.add_argument("--processor", help="List of DAI processors in the format of PROCESSOR_TYPE/Processor-Name. ex INVOICE_PROCESSOR/my-invoice-processor", action="append")
parser.add_argument("--action", choices=['create','destroy'])
args = parser.parse_args()

project_number = args.project_number
location = args.location

processor_types = list_processors_types(project_number, location)
dai_service_api_name = "documentai.googleapis.com"
enable_service_api(project_number,dai_service_api_name)


if args.action == 'create':

    processor_list = []
    for processor in args.processor:
        p = processor.split("/")
        p_type = p[0]
        p_name = p[1]
        #name, id, ep, state, version = create_processor(project_number,location, p_type, p_name)
        p_list = create_processor(project_number,location, p_type, p_name)
        processor_list.append(p_list)

    processor_output = {
        "project_number": project_number,
        "location": location,
        "processors": processor_list
    }

    f = open("processor_state.json", "w")
    json.dump(processor_output,f)
    f.close()

    b = open("vars.sh", "w")
    b.write("#! /usr/bin/bash")
    for i in processor_output["processors"]:
        b.write("\n")
        b.write(f'{i["type"]}={i["id"]}')
    b.close()

elif args.action == 'destroy':

    f = open("processor_state.json", "r")
    data = json.load(f)

    for processor in data["processors"]:
        x = delete_processor(project_number, location, processor["id"])
    print(data)


# Outfile project_number, location, processor_name, 
print(f'This is the project num = {args.project_number}')
