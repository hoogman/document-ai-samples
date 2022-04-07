import os, datetime
from google.cloud import firestore

#add document to firestore collection

firestore_collection = os.environ["FIRESTORE_COLLECTION"]

def create_firestore_doc(doc_name, doc_object):
    db = firestore.Client()

    print(f'Adding doc ({doc_name}) to firestore collection ({firestore_collection})')

    db.collection(firestore_collection).document(doc_name).set(doc_object)