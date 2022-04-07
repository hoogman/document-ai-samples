import os, datetime, json
from google.cloud import documentai_v1 as documentai
from google.cloud import storage as storage
from google.cloud import firestore
from collections import defaultdict
import utils.firestoreUtils as firestoreUtils
import utils.bqUtils as bqUtils

firestore_collection = os.environ["EXTRACT_FIRESTORE_COLLECTION"]
firestore_output_collection = os.environ["COMPILED_RESULTS_FIRESTORE_COLLECTION"]
bq_results_table = os.environ["BQ_RESULTS_TABLE_ID"]
bq_schema_file = os.environ["BQ_SCHEMA_FILE"]
project_id = os.environ["PROJECT_ID"]

def main_func(event, context):

    gt_gcs_bucket = event['bucket']
    gt_gcs_blob = event['name']
    #content_type = event['contentType']

    gcs_hitl_uri = f"gs://{event['bucket']}/{event['name']}"
    eventid = context.event_id
    extract_timestamp = context.timestamp

    hitl_op_id = gt_gcs_blob.split('/')[0]

    extract_doc = firestoreUtils.get_firestore_doc(firestore_collection, hitl_op_id)
    extract_entities, source_extraction_fname, doc_type = firestoreUtils.parse_firestore_doc(extract_doc)

    gt_blob_bytes = get_gcs_blob(gt_gcs_bucket, gt_gcs_blob)

    gt_document = documentai.types.Document.from_json(gt_blob_bytes)

    print(f'Hitl results for Operation ID ( {hitl_op_id} ) ingested.')

    print(f'Merging HITL results with Extract results on document - {source_extraction_fname}')

    #added v2 to address missing values in hitl response
    results_dict = merge_results_v2(gt_document, extract_entities)
    #v1 - adjusting to change in hitl response
    #results_dict = merge_results(gt_document, extract_entities)

    results_dict["source_filename"] = source_extraction_fname
    dt = datetime.datetime.now()
    results_dict["timestamp"] = dt
    results_dict["gcs_hitl_uri"] = gcs_hitl_uri
    results_dict["doc_type"] = doc_type

    print('Results merge complete.')

    bqUtils.write_to_bq(results_dict, bq_results_table, bq_schema_file, project_id)

    print("Completed results load to BigQuery")

    fs_doc_name = (str(source_extraction_fname.replace(" ", "_").replace("&", "and").replace(".pdf","")) + "_" + str(hitl_op_id))

    firestoreUtils.create_firestore_doc(firestore_output_collection, fs_doc_name, results_dict)

    print('Compile Results Complete')

def get_gcs_blob(gcs_bucket, blob_name):

    storage_client = storage.Client()
    bucket = storage_client.get_bucket(gcs_bucket)
    file = bucket.blob(blob_name)
    blob_bytes = file.download_as_bytes()

    return blob_bytes

def merge_results(gt_document, extract_entities):
    print(f'Extracted entities count ({extract_entities.__len__()} )')
    results_dict = defaultdict()
    new_ent_id = 1000
    for ent in gt_document.entities:
        if ent.type_ == 'line_item' or ent.type_ == 'vat':
            for prop in ent.properties:
                if prop.id == "":
                    ext_type = None
                    ext_mention_txt = None
                    ext_conf = None
                else:
                    ext_type = extract_entities[prop.id]['type_']
                    ext_mention_txt = extract_entities[prop.id]['mention_text']
                    ext_conf = extract_entities[prop.id]['confidence']
                ent_dict = {
                    "gt_type_" : prop.type_,
                    "gt_mention_text" : prop.mention_text,
                    "gt_confidence" : prop.confidence,
                    "gt_provenance_name" : prop.provenance.type_.name,
                    "gt_provenance_value": prop.provenance.type_.value,
                    "extract_type_" : ext_type,
                    "extract_mention_text" : ext_mention_txt,
                    "extract_confidence" : ext_conf
                }
                if prop.id == '':
                    results_dict[str(new_ent_id)] = ent_dict
                    new_ent_id += 1
                else:
                    results_dict[prop.id] = ent_dict
            ent_dict = {
                "gt_type_": ent.type_,
                "gt_mention_text": ent.mention_text,
                "gt_confidence": ent.confidence,
                "gt_provenance_name": ent.provenance.type_.name,
                "gt_provenance_value": ent.provenance.type_.value,
                "extract_type_" : extract_entities[ent.id]['type_'],
                "extract_mention_text" : extract_entities[ent.id]['mention_text'],
                "extract_confidence" : extract_entities[ent.id]['confidence']                
            }
            if ent.id == '':
                results_dict[str(new_ent_id)] = ent_dict
                new_ent_id += 1
            else:
                results_dict[ent.id] = ent_dict
        else:
            if extract_entities.get(ent.id) != None:
                ent_dict = {
                    "gt_type_": ent.type_,
                    "gt_mention_text": ent.mention_text,
                    "gt_confidence": ent.confidence,
                    "gt_provenance_name": ent.provenance.type_.name,
                    "gt_provenance_value": ent.provenance.type_.value,
                    "extract_type_" : extract_entities[ent.id]['type_'],
                    "extract_mention_text" : extract_entities[ent.id]['mention_text'],
                    "extract_confidence" : extract_entities[ent.id]['confidence']  
                }
                if ent.id == '':
                    results_dict[str(new_ent_id)] = ent_dict
                    new_ent_id += 1
                else:
                    results_dict[ent.id] = ent_dict
            else:
                ent_dict = {
                    "gt_type_": ent.type_,
                    "gt_mention_text": ent.mention_text,
                    "gt_confidence": ent.confidence,
                    "gt_provenance_name": ent.provenance.type_.name,
                    "gt_provenance_value": ent.provenance.type_.value,
                    "extract_type_" : None,
                    "extract_mention_text" : None,
                    "extract_confidence" : None 
                }
                if ent.id == '':
                    results_dict[str(new_ent_id)] = ent_dict
                    new_ent_id += 1
                else:
                    results_dict[ent.id] = ent_dict

    return results_dict

def correct_provenance_val(results: dict, provenance_name: str, provenance_value: int):

    for key in results:
        results[key]["gt_provenance_name"] = provenance_name
        results[key]["gt_provenance_value"] = provenance_value

    return results

def merge_results_v2(gt_document, extract_entities):
    print(f'Extracted entities count ({extract_entities.__len__()} )')
    
    results_dict = defaultdict()
    new_ent_id = 1000

    gt_entities_dict = {}

    for ent in gt_document.entities:
        ent_dict = {
            "mention_text": ent.mention_text,
            "confidence": ent.confidence,
            "type_": ent.type_,
            "gt_provenance_name": ent.provenance.type_.name,
            "gt_provenance_value": ent.provenance.type_.value
        }
        if ent.id == "":
            gt_entities_dict[str(new_ent_id)]=ent_dict
            new_ent_id += 1
        else:
            gt_entities_dict[ent.id]=ent_dict
        if ent.type_ == 'line_item' or ent.type_ == 'vat':
            for prop in ent.properties:
                prop_dict = {
                    "mention_text": prop.mention_text,
                    "confidence": prop.confidence,
                    "type_": prop.type_,
                    "gt_provenance_name": prop.provenance.type_.name,
                    "gt_provenance_value": prop.provenance.type_.value
                }
                if prop.id == "":
                    gt_entities_dict[str(new_ent_id)]=prop_dict
                    new_ent_id += 1
                else:
                    gt_entities_dict[prop.id]=prop_dict

    print(f"HITL entities count ( {len(gt_entities_dict)} )")

    common_dicts = {}
    hitl_removed_entities_dict = {}
    hitl_added_entities_dict = {}
    if len(extract_entities) >= len(gt_entities_dict):
        # More extracted entities then found in hitl indicates entities were removed during review
        for key in extract_entities:
            if (key in gt_entities_dict):
                # entities with common IDs between htil and extract
                common_dicts[key] = extract_entities[key]
                #if (extract_entities[key]["type_"] == gt_entities_dict[key]["type_"])
            else:
                # results missing from hitl response
                # provenance = REMOVE
                hitl_removed_entities_dict[key] = extract_entities[key].copy()
        for key in gt_entities_dict:
            if (key not in extract_entities):
                #entities added during HITL review
                #provenance = ADDED
                hitl_added_entities_dict[key] = gt_entities_dict[key].copy()
    else:
        # more entities exist in in HITL results
        for key in gt_entities_dict:
            if (key in extract_entities):
                #common entities between hitl and extract results
                common_dicts[key] = gt_entities_dict[key]
            else:
                #if key is found in HITL results and not extract it indicates entity was added during review
                hitl_added_entities_dict[key] = gt_entities_dict[key].copy()
        for key in extract_entities:
            if (key not in gt_entities_dict):
                hitl_removed_entities_dict[key] = extract_entities[key].copy()

    if len(hitl_removed_entities_dict) > 0:
        hitl_removed_entities_dict = correct_provenance_val(hitl_removed_entities_dict, "REMOVE", 2)
    if len(hitl_added_entities_dict) > 0:
        hitl_added_entities_dict = correct_provenance_val(hitl_added_entities_dict, "ADD", 1)

    merged_dict = {}
    for key in common_dicts:
        ent = {
            "gt_type_": gt_entities_dict[key]["type_"],
            "gt_mention_text": gt_entities_dict[key]["mention_text"],
            "gt_confidence": gt_entities_dict[key]["confidence"],
            "gt_provenance_name": gt_entities_dict[key]["gt_provenance_name"],
            "gt_provenance_value": gt_entities_dict[key]["gt_provenance_value"],
            "extract_type_" : extract_entities[key]['type_'],
            "extract_mention_text" : extract_entities[key]['mention_text'],
            "extract_confidence" : extract_entities[key]['confidence']  
        }
        merged_dict[key] = ent

    for key in hitl_added_entities_dict:
        if key in gt_entities_dict:
            gt_type = gt_entities_dict[key]["type_"]
            gt_mention_text = gt_entities_dict[key]["mention_text"]
            gt_conf = gt_entities_dict[key]["confidence"]
            gt_prov_name = gt_entities_dict[key]["gt_provenance_name"]
            gt_prov_value = gt_entities_dict[key]["gt_provenance_value"]
        else:
            gt_type = hitl_added_entities_dict[key]["type_"]
            gt_mention_text = hitl_added_entities_dict[key]["mention_text"]
            gt_conf = 1.0
            gt_prov_name = hitl_added_entities_dict[key]["gt_provenance_name"]
            gt_prov_value = hitl_added_entities_dict[key]["gt_provenance_value"]

        if key in extract_entities:
            extract_type = extract_entities[key]["type_"]
            extract_mention_text = extract_entities[key]["mention_text"]
            extract_conf = extract_entities[key]["confidence"]
        else:
            extract_type = "None"
            extract_mention_text = "None"
            extract_conf = 0.0

        add_ent = {
            "gt_type_": gt_type,
            "gt_mention_text": gt_mention_text,
            "gt_confidence": gt_conf,
            "gt_provenance_name": gt_prov_name,
            "gt_provenance_value": gt_prov_value,
            "extract_type_" : extract_type,
            "extract_mention_text" : extract_mention_text,
            "extract_confidence" : extract_conf
        }
        merged_dict[key] = add_ent
    #add removed entities to the merge dict
    for key in hitl_removed_entities_dict:
        if key in gt_entities_dict:
            gt_type = gt_entities_dict[key]["type_"]
            gt_mention_text = gt_entities_dict[key]["mention_text"]
            gt_conf = gt_entities_dict[key]["confidence"]
            gt_prov_name = gt_entities_dict[key]["gt_provenance_name"]
            gt_prov_value = gt_entities_dict[key]["gt_provenance_value"]
        else:
            gt_type = "None"
            gt_mention_text = "None"
            gt_conf = 0.0
            gt_prov_name = "OPERATION_TYPE_UNSPECIFIED"
            gt_prov_value = 0

        if key in extract_entities:
            extract_type = extract_entities[key]["type_"]
            extract_mention_text = extract_entities[key]["mention_text"]
            extract_conf = extract_entities[key]["confidence"]
            gt_type = hitl_removed_entities_dict[key]["type_"]
            gt_mention_text = hitl_removed_entities_dict[key]["mention_text"]
            gt_conf = 1.0
            gt_prov_name = hitl_removed_entities_dict[key]["gt_provenance_name"]
            gt_prov_value = hitl_removed_entities_dict[key]["gt_provenance_value"]
        else:
            extract_type = "None"
            extract_mention_text = "None"
            extract_conf = 0.0

        remove_ent = {
            "gt_type_": gt_type,
            "gt_mention_text": gt_mention_text,
            "gt_confidence": gt_conf,
            "gt_provenance_name": gt_prov_name,
            "gt_provenance_value": gt_prov_value,
            "extract_type_" : extract_type,
            "extract_mention_text" : extract_mention_text,
            "extract_confidence" : extract_conf
        }
        merged_dict[key] = remove_ent

        #fix provenance for replaced entities
    for key in merged_dict:
        if merged_dict[key]["gt_type_"] != merged_dict[key]["extract_type_"]:
            if merged_dict[key]["gt_type_"] != "None" and merged_dict[key]["extract_type_"] != "None":
                merged_dict[key]["gt_provenance_name"] = "REPLACE"
                merged_dict[key]["gt_provenance_value"] = 3
        elif merged_dict[key]["gt_mention_text"] != merged_dict[key]["extract_mention_text"]:
            merged_dict[key]["gt_provenance_name"] = "REPLACE"
            merged_dict[key]["gt_provenance_value"] = 3
    return merged_dict

    
        
