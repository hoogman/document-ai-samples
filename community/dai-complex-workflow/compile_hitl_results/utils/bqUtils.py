from collections import defaultdict
from google.cloud import bigquery as bq
import pandas as pd
import json, os

def write_to_bq(results_dict: defaultdict, bq_table_id: str, bq_schema_path: str, project_id: str):
    bq_client = bq.Client()

    dirname = os.path.dirname(__file__)
    bq_schema_file = open(dirname + bq_schema_path)
    bq_schema = json.load(bq_schema_file)
    bq_tbl_path = project_id + "." + bq_table_id

    bq_table = bq.Table(bq_tbl_path, bq_schema)

    #if table doesn't exist - create it
    bq_table = create_missing_bq_table(bq_table, project_id, bq_table_id)

    bq_dataframe = create_bq_dataframe(results_dict)
    errors = bq_client.insert_rows_from_dataframe(bq_table, bq_dataframe)

    if errors[0]:
        print("Error inserting rows: {}".format(errors))
    else:
        print(f'New rows added to ( {bq_table_id} ).')

def create_missing_bq_table(bq_table: bq.Table, project_id: str, bq_table_id: str):
    bq_client = bq.Client()

    dataset_name = f'{project_id}.{bq_table_id.split(".")[0]}'
    #create missing dataset
    bq_client.create_dataset(dataset=dataset_name, exists_ok=True, timeout=20)
    bq_table = bq_client.create_table(table=bq_table, exists_ok=True, timeout=20)
    #create missing table
    #try:
    #    error = bq_client.get_table(bq_table)
    #except:
    #   bq_table = bq_client.create_table(bq_table)

    return bq_table

def create_bq_dataframe(results_dict: defaultdict):

    dataframe = pd.DataFrame()
    #dataframe_columns = ["Doc Name", "HITL Results Doc Name", "HITL Results Timestamp", "Extract Confidence", "Extract Key", "Extract Value", "]

    source_fname = results_dict.pop('source_filename')
    ts = results_dict.pop("timestamp")
    doc_type = results_dict.pop("doc_type")
    hitl_doc_path = results_dict.pop("gcs_hitl_uri")


    for item_id in results_dict:
        item = results_dict[item_id]
        if isinstance(item, dict):
            item["doc_name"] = source_fname
            item["doc_type"] = doc_type 
            item["hitl_results_path"] = hitl_doc_path
            item["timestamp"] = ts
            dataframe = dataframe.append(item, ignore_index=True)

    #dataframe.index.names = ['index']
    dataframe = dataframe.replace('\n', ' ', regex=True)
    dataframe['extract_accuracy_result'] = dataframe.apply(lambda row: check_extract_accuracy(row), axis=1)

    return dataframe
        
def check_extract_accuracy(row):
    if (row['gt_mention_text'] == row['extract_mention_text']) and (row['gt_provenance_name'] not in ('ADD','REMOVE')):
        return True
    else:
        return False
