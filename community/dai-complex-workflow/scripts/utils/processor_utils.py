#!/usr/bin/python

from os import name
from google.cloud import documentai_v1beta3 as documentai
from google.cloud import service_usage

def create_processor(project_num: int, location: str, processor_type: str, processor_name: str):
    dai_client = documentai.DocumentProcessorServiceClient()
    dai_parent = f'projects/{project_num}/locations/{location}'

    dai_processor = documentai.types.Processor(type_=processor_type, display_name=processor_name)
    dai_create_processor_req = documentai.CreateProcessorRequest(parent=dai_parent, processor=dai_processor)

    response = dai_client.create_processor(dai_create_processor_req)

    p_name = response.display_name
    p_ep = response.process_endpoint
    p_id = response.name.split("/")[-1]
    p_version = response.default_processor_version.split("/")[-1]
    p_state = response.state.name
    p_create_time = response.create_time.timestamp()
    p_type = response.type_

    response_dict = {
        "name": p_name,
        "endpoint": p_ep,
        "id": p_id,
        "version": p_version,
        "state": p_state,
        "create_time": p_create_time,
        "type": p_type
    }

    return response_dict

def delete_processor(project_num: int, location: str, processor_id: str):
    dai_client = documentai.DocumentProcessorServiceClient()
    dai_parent = f'projects/{project_num}/locations/{location}'
    p_name = f'{dai_parent}/processors/{processor_id}'

    dai_delete_req = documentai.DeleteProcessorRequest(name=p_name)
    delete_resp = dai_client.delete_processor(dai_delete_req)

    return delete_resp

def list_processors_types(project_num: int, location: str):
    dai_parent = f'projects/{project_num}/locations/{location}'
    dai_client = documentai.DocumentProcessorServiceClient()
    fetch_request = documentai.FetchProcessorTypesRequest(parent=dai_parent)
    response = dai_client.fetch_processor_types(request=fetch_request)

    types_list = []
    for item in response.processor_types:
        types_list.append(item.type_)

    return types_list

def check_service_state(project_num: int, service_name: str):
    service_client = service_usage.ServiceUsageClient()
    sname = f'projects/{project_num}/services/{service_name}'
    req = service_usage.GetServiceRequest(name=sname)
    resp = service_client.get_service(request=req)

    service_state = resp.state.name

    return service_state

def enable_service_api(project_num: int, service_name: str):

    service_state = check_service_state(project_num,service_name)

    if service_state != "ENABLED":
        service_client = service_usage.ServiceUsageClient()
        sname = f'projects/{project_num}/services/{service_name}'
        req = service_usage.EnableServiceRequest(name=sname)
        resp = service_client.enable_service(req)

        return resp

    else:
        return "ENABLED"

def list_service_apis(project_num: int):
    service_client = service_usage.ServiceUsageClient()
    p_name = f'projects/{project_num}'
    req = service_usage.ListServicesRequest(parent=p_name)
    s_apis = service_client.list_services(request=req)

    service_list = []

    for x in s_apis._response.services:
        service_info = [x.config.name, x.state.name]
        service_list.append(service_info)

    # Returns a list of lists (Service Name, State)
    return s_apis
