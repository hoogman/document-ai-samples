import os
import base64

from io import BytesIO
from google.cloud import documentai_v1 as documentai
from google.cloud import storage
from google.api_core import exceptions
from PyPDF2 import PdfFileReader, PdfFileWriter

import utils.image_utils as imageutils

#Global vars
project_id = os.environ["PROJECT_ID"]
project_num = os.environ["PROJECT_NUM"]
location = os.environ["LOCATION"]
pdai_splitter_id = os.environ["PDAI_SPLITTER_ID"]
split_invoice_bucket = os.environ["SPLIT_INVOICE_BUCKET"]
splitter_response_bucket = os.environ["SPLITTER_RESPONSE_BUCKET"]

def process_doc(file_name, bucket_name, content_type, eventid):

    #Get doc from GCS
    gcs_client = storage.Client()
    bucket = gcs_client.bucket(bucket_name)
    gcs_file = bucket.blob(file_name)
    file_blob = gcs_file.download_as_bytes()

    #convert uploaded doc to pdf if needed
    if content_type != 'application/pdf':
        print(f'Converting {content_type} to application/pdf')
        file_blob = imageutils.convert_doc_to_pdf(file_blob)
        content_type = 'application/pdf'

    processed_doc, results_json = process_doc_split(file_blob, content_type, bucket_name, file_name)

    split_fname = file_name.split('.')[0]
    save_splitter_response(results_json, split_fname, splitter_response_bucket, eventid)    

    split_docs(file_blob, processed_doc, split_fname, eventid)

def process_doc_split(doc_content, content_type, bucket_name, file_name):

    documentai_client = documentai.DocumentProcessorServiceClient()
    pdf_num_pages = get_pdf_page_cnt(doc_content)
    invoice_processor = f"projects/{project_num}/locations/{location}/processors/{pdai_splitter_id}"

    if pdf_num_pages > 15:

        #support for docs over 15 pages under dev. Will utilize batchprocess for larger docs
        SystemExit("Support for documents larger than 15 pages is not currently supported.")
        destination_uri = f'gs://{splitter_response_bucket}'
        input_uri = f'gs://{bucket_name}/{file_name}'

        gcs_docs = documentai.GcsDocuments(
            documents = [{"gcs_uri": input_uri, "mime_type": content_type}]
        )

        input_config = documentai.BatchDocumentsInputConfig(gcs_documents=gcs_docs)

        output_config = documentai.DocumentOutputConfig(
            gcs_output_config={"gcs_uri": destination_uri}
        )

        request = documentai.types.document_processor_service.BatchProcessRequest(
            name=invoice_processor,
            input_documents=input_config,
            document_output_config=output_config
        )

        operation = documentai_client.batch_process_documents(request)

        operation.result(timeout=300)

        operation_name = operation.operation.name.split('/')

        operation_id = operation_name.pop()
        operation_blob = f'{operation_id}/0/output-document.json'

        #split_loc = f'{destination_uri}/{operation_id}/0/output-document.json'

        storage_client = storage.Client()
        bucket = storage_client.get_bucket(splitter_response_bucket)
        blob = bucket.get_blob(operation_blob)
        #blob_bytes
    

        return operation

    else:
        document = {
            "content": doc_content,
            "mime_type": content_type
        }

        request = {
            "name": invoice_processor,
            "raw_document": document
        }
        results = documentai_client.process_document(request)

        results_json = documentai.types.Document.to_json(results.document)

    return results.document, results_json

def split_docs(content_bytes: bytes, splits, ingest_file_name: str, eventid):

    content_bytesio = BytesIO(content_bytes)

    pdf_reader = PdfFileReader(content_bytesio)

    doc_entities = splits.entities

    splits_dict = dict()

    for i in doc_entities:
        pdf_writer = PdfFileWriter()
        for a in i.page_anchor.page_refs:
            if a.page is None:
                pagenum = 0
            else:
                pagenum = a.page
            
            pg = pdf_reader.getPage(pagenum)
            pdf_writer.addPage(pg)

        pdf_bytes = BytesIO()
        pdf_writer.write(pdf_bytes)

        pdf_bytes.seek(0)
        doc_type = i.type_
        out_filename = f'{ingest_file_name}-{doc_type}-{pagenum}-{eventid}.pdf'

        print(f'Document type ({doc_type}) identified with confidence ( {round(float(i.confidence), 5)} ) - Creating new document ({out_filename})')

        write_client = storage.Client()
        write_bucket = write_client.get_bucket(split_invoice_bucket)
        write_file = write_bucket.blob(out_filename)
        write_file.metadata = {'dai_doc_type': doc_type}        
        write_file.upload_from_string(pdf_bytes.read(), content_type='application/pdf')

def save_splitter_response(response, ingest_file_name, out_bucket, eventid):
    
    gcs_client = storage.Client()
    write_bucket = gcs_client.get_bucket(out_bucket)

    out_file_name = f'{ingest_file_name}-{eventid}.json'

    write_file = write_bucket.blob(out_file_name)
    write_file.upload_from_string(format(response), content_type='application/json')

def get_pdf_page_cnt(pdf_doc: bytes):

    pdf_file = BytesIO(pdf_doc)
    pdf_reader = PdfFileReader(pdf_file)

    num_pages = pdf_reader.getNumPages()
    #pdf_size = pdf_reader
    return num_pages
