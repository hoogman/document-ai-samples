import os
import datetime
import base64
import json

from io import BytesIO
from google.cloud import documentai_v1 as documentai
from google.cloud import storage
from google.api_core import exceptions
import utils.firestoreUtils as firestoreUtils


project_id = os.environ["PROJECT_ID"]
project_num = os.environ["PROJECT_NUM"]
location = os.environ["LOCATION"]
gcs_raw_extract_dest = os.environ["GCS_RAW_EXTRACT_BUCKET"]
skip_human_review = os.environ["SKIP_HITL"]
#Invoice Parser Vars
pdai_invoice_processor_id = os.environ["PDAI_INVOICE_PROCESSOR_ID"]
#Expense Parser Vars
pdai_expense_processor_id = os.environ["PDAI_EXPENSE_PROCESSOR_ID"]

if skip_human_review == 'False' or skip_human_review == 'false':
    skip_human_review = False
else:
    skip_human_review = True

#if "SKIP_HITL" in os.environ:
#    skip_human_review = bool(os.environ["SKIP_HITL"])
#else:
#    skip_human_review = True

def main_func(event, context):

    bucket_name = event['bucket']
    file_name = event['name']
    content_type = event['contentType']

    gcs_input_uri = f"gs://{event['bucket']}/{event['name']}"
    eventid = context.event_id
    extract_timestamp = context.timestamp
    gcs_blob_location = context.resource['name']

    #Get file from GCS

    gcs_doc_blob, gcs_doc_meta = get_gcs_doc(file_name, bucket_name)

    xtype = gcs_doc_meta['dai_doc_type']
    if 'invoice' in xtype:

        print(f'Extracting Entities from Document - Document classified as {xtype}')
        #Send doc to DAI parser and get results
        doc_entities, hitl_operation_id, doc_results_json = process_doc(gcs_doc_blob, content_type, project_num, location, pdai_invoice_processor_id)

        #save raw extract results to GCS bucket
        save_extract_to_gcs(gcs_raw_extract_dest, doc_results_json, file_name, eventid, hitl_operation_id)

        #extract the entities from the document payload
        entity_list = extract_entities(doc_entities)

        #format results for firestore
        results_dict = create_results_dict(entity_list, file_name, eventid, extract_timestamp, bucket_name, gcs_blob_location, hitl_operation_id, xtype)

        #storage new doc in firestore collection
        firestoreUtils.create_firestore_doc(f'{file_name}-{eventid}', results_dict)

    elif 'receipt' in xtype or 'restaurant_statement' in xtype:
        print(f'Extracting Entities from Document - Document classified as {xtype}')
        #Send doc to DAI parser and get results
        doc_entities, hitl_operation_id, doc_results_json = process_doc(gcs_doc_blob, content_type, project_num, location, pdai_expense_processor_id)

        #save raw extract results to GCS bucket
        save_extract_to_gcs(gcs_raw_extract_dest, doc_results_json, file_name, eventid, hitl_operation_id)

        #extract the entities from the document payload
        entity_list = extract_entities(doc_entities)

        #format results for firestore
        results_dict = create_results_dict(entity_list, file_name, eventid, extract_timestamp, bucket_name, gcs_blob_location, hitl_operation_id, xtype)

        #storage new doc in firestore collection
        firestoreUtils.create_firestore_doc(f'{file_name}-{eventid}', results_dict)

    else:

        print(f'Document not processed for entity extraction - Document classified as {xtype}')


def get_gcs_doc(file_name, bucket_name):

    #Get doc from GCS
    gcs_client = storage.Client()
    bucket = gcs_client.get_bucket(bucket_name)
    gcs_file = bucket.get_blob(file_name)
    file_meta = gcs_file.metadata
    file_blob = gcs_file.download_as_bytes()

    return file_blob, file_meta

def process_doc(gcs_blob, content_type, project_number, location, pdai_processor_id):    

    documentai_client = documentai.DocumentProcessorServiceClient()

    document = {
        "content": gcs_blob,
        "mime_type": content_type
    }

    invoice_processor = f"projects/{project_number}/locations/{location}/processors/{pdai_processor_id}"

    request = {
        "name": invoice_processor,
        "raw_document": document,
        "skip_human_review": skip_human_review
    }

    results = documentai_client.process_document(request)
    print (f'HITL Output: {results.human_review_status}')

    hitl_op = results.human_review_status.human_review_operation
    hitl_op_split = hitl_op.split('/')
    hitl_op_id = hitl_op_split.pop()

    results_json = documentai.types.Document.to_json(results.document)

    return results.document, hitl_op_id, results_json

def extract_entities(doc):

    #entity_dict = dict()
    #ent_id, conf, mention_text, type_ = None
    entity_list = dict()
    #for entity in doc.entities:
        #ents = {
            #entity.type_: entity.mention_text,
            #"confidence": entity.confidence
        #}
        #entity_list.append(ents)

    #entity_list2 = list()
    for entity in doc.entities:
        if entity.type_ == 'line_item' or entity.type_ == 'vat':
            for property in entity.properties:
                ents = {
                    "type_": property.type_,
                    "mention_text": property.mention_text,
                    "confidence": property.confidence
                }
                entity_list[property.id] = ents
            ents = {
                    "type_": entity.type_,
                    "mention_text": entity.mention_text,
                    "confidence": entity.confidence
            }
            entity_list[entity.id] = ents
        else:
            ents = {
                "type_": entity.type_,
                "mention_text": entity.mention_text,
                "confidence": entity.confidence
            }
            entity_list[entity.id] = ents

    return entity_list

def create_results_dict(entity_list, file_name, event_id, timestamp: datetime, gcs_bucket_name, gcs_obj_path, hitl_operation_id, doc_type):

    output_dict = {
        "doc_type": doc_type,
        "parser_event_id": event_id,
        "extract_timestamp": datetime.datetime.now(),
        "file_name": file_name,
        "bucket_name": gcs_bucket_name,
        "gcs_resource": gcs_obj_path,
        "hitl_operation_id": hitl_operation_id,
        "entities": entity_list
    }

    return output_dict

def save_extract_to_gcs(dest_bucket, content, filename, eventid, hitl_operation_id):

    storageclient = storage.Client()
    bucket = storageclient.get_bucket(dest_bucket)
    
    fname = f'{filename.split(".")[0]}-{eventid}.json'
    
    #response_doc = {'document': content}

    write_file = bucket.blob(fname)
    write_file.metadata = {'hitl_operation_id': hitl_operation_id}
    write_file.upload_from_string(format(content), content_type='application/json')