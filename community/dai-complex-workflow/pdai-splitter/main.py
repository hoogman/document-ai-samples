import os
import json
import datetime
import base64
import pdaihelper as pdai_helper

from io import BytesIO
from google.cloud import documentai_v1 as documentai
from google.cloud import storage
from google.api_core import exceptions

#output_bucket = os.environ["invoice_parser_output_bucket"]
#processor_timeout = int(os.environ["invoice_parser_timeout"])

def main_func(event, context):

    #set vars with data from gcs event
    bucket_name = event['bucket']
    file_name = event['name']
    content_type = event['contentType']

    print(f'Executing ingest of ( {file_name} ) from GCS Bucket ( {bucket_name} ).')

    gcs_input_uri = f"gs://{event['bucket']}/{event['name']}"
    eventid = context.event_id

    #different doctype place holder

    #process document splits
    pdai_helper.process_doc(file_name, bucket_name, content_type, eventid)
