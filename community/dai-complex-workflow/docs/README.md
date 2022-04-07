# Manual Configuration Steps
>Manual Steps only support Invoice Processor

### Initialize

1. Login to the Google Cloud Console and open Cloud Shell
2. Execute the following cmd in your cloud shell terminal and replace [PROJECT_ID] with your actual project id.

~~~~
gcloud config set project [PROJECT_ID]
~~~~

3. Execute the following in Cloud Shell to enable required APIs.

~~~~
gcloud services enable storage.googleapis.com firestore.googleapis.com cloudfunctions.googleapis.com documentai.googleapis.com cloudbuild.googleapis.com appengine.googleapis.com
~~~~

### Google Cloud Storage

1. Create the GCS bucket for ingesting uploaded documents in (PDF, JPEG, PNG, TIFF, or GIF) formats. Execute the following commands from your Cloudshell terminal.

~~~~ 
gsutil mb -c standard -l us-central1 gs://$GOOGLE_CLOUD_PROJECT-dai-ingest
gsutil mb -c standard -l us-central1 gs://$GOOGLE_CLOUD_PROJECT-dai-split-docs
gsutil mb -c standard -l us-central1 gs://$GOOGLE_CLOUD_PROJECT-dai-raw-splitter-response
gsutil mb -c standard -l us-central1 gs://$GOOGLE_CLOUD_PROJECT-dai-raw-entity-extraction
gsutil mb -c standard -l us-central1 gs://$GOOGLE_CLOUD_PROJECT-cf-stage
gsutil mb -c standard -l us-central1 gs://$GOOGLE_CLOUD_PROJECT-invoice-hitl-results
gsutil mb -c standard -l us-central1 gs://$GOOGLE_CLOUD_PROJECT-hitl-instructions
~~~~

2. Create the following environemt variables.

~~~~
export GCS_DAI_INGEST=$GOOGLE_CLOUD_PROJECT-dai-ingest
export GCS_DAI_SPLIT_DOCS=$GOOGLE_CLOUD_PROJECT-dai-split-docs
export GCS_DAI_RAW_SPLITTER_RESPONSE=$GOOGLE_CLOUD_PROJECT-dai-raw-splitter-response
export GCS_DAI_RAW_ENTITY_EXTRACTION=$GOOGLE_CLOUD_PROJECT-dai-raw-entity-extraction
export GCS_CF_STAGE=$GOOGLE_CLOUD_PROJECT-cf-stage
export GCS_INVOICE_HITL_RESULTS=$GOOGLE_CLOUD_PROJECT-invoice-hitl-results
export GCS_HITL_INSTRUCTIONS=$GOOGLE_CLOUD_PROJECT-hitl-instructions

export PROJECT_NUMBER=$(gcloud projects list --filter="project_id=$GOOGLE_CLOUD_PROJECT" --format='value(project_number)')
~~~~

### Configure Document AI Invoice Parser and PDAI Splitter/Classifier

1. Browse to Document AI and select "Create Processor"
2. Select "Procurement Doc Splitter" from the list. In the slide out window enter a name of your choice and select "Create"
3. Note the ID as it will be used to populate the following command. Replace [pdai splitter id] with the ID of your new splitter. Then execute the command in the Cloudshell terminal.

~~~
export PDAI_SPLITTER_ID=[pdai spliiter id]
~~~

4. From the Document AI screen. Select Processors on the left nav. On the newly open screen select "+ Create Processor"
5. From the list select "Invoice Parser". In the slide out window enter a name of your choice and select "Create".
6. Note the ID as it will be used to populate the following command. Replace [invoice processor id] with the ID of your new invoice processor. Then execute the command in the Cloudshell terminal.

~~~
export INVOICE_PROCESSOR_ID=[invoice processor id]
~~~

7. Enable Human-In-the-Loop processing on Invoice parser.

    1. From the Document AI page. Select Processors from the left navigation
    2. From the list. Click on the name of your newly created invoice processor
    3. Select the "Human Review"
    4. Select "Set Up Human Review"
    5. Under Validation filters. Select the radio button next to "Document-level filter"
    6. Move the "Confidence threshold %" slider to 100
    7. Under Labelers. Select Radio button next to "Use my own labelers"
    8. Select "Labeler pool" input box -> New Labler Pool...
    9. In the New Labler Pool Window. Enter a pool name of your choice. Under pool managers add user account you used to login to the GCP Console then select "Create Pool". If you receiver a permissions error then you can utilize your personal gmail.com address.
    10. Under Instructions - Add a PDF file outlining instructions for reviewers. PDF should be located in a GCS bucket. I you have not uploaded a Labeler Instructions doc yet, then do so now. Doc should reside in your GCS bucket ending in hitl-instructions.
    11. Under Results - Select the newly created GCS bucket ending in invoice-hitl-results
    12. Select "Save Configuration"
    13. When configuration has completed select the "Enable" toggle.

## Create Google Firestore Instance

1.  Create Firestore DB Instance 

~~~~
gcloud app create --region=us-central --project=$GOOGLE_CLOUD_PROJECT
gcloud beta firestore databases create --project=$GOOGLE_CLOUD_PROJECT --region=us-central 
~~~~

## Create Cloud Functions

1. Upload provided .zip files to your Cloud Shell session.

![Upload!](./images/cloudshell-upload.jpg)

2. In your Cloudshell terminal. Execute the following command.

~~~
unzip compile_hitl_results.zip
unzip invoice-extractor.zip
unzip pdai-splitter.zip
~~~

1. Create Cloud Function to support ingest, split/classify, and image conversion.

~~~~
gcloud beta functions deploy doc_ingest \
--runtime python38 \
--entry-point main_func \
--source pdai-splitter \
--trigger-event google.storage.object.finalize \
--trigger-resource $GCS_DAI_INGEST \
--set-env-vars PROJECT_ID=$GOOGLE_CLOUD_PROJECT,LOCATION='us',PDAI_SPLITTER_ID=$PDAI_SPLITTER_ID,SPLIT_INVOICE_BUCKET=$GCS_DAI_SPLIT_DOCS,SPLITTER_RESPONSE_BUCKET=$GCS_DAI_RAW_SPLITTER_RESPONSE,PROJECT_NUM=$PROJECT_NUMBER \
--ingress-settings=internal-and-gclb \
--stage-bucket=$GCS_CF_STAGE \
--max-instances=10 \
--timeout=120
~~~~

2. Create Cloud Function to support entity extraction and entity storage to Cloud Firestore.

~~~~
gcloud beta functions deploy doc_extract \
--runtime python38 \
--entry-point main_func \
--source pdai-extractor \
--trigger-event google.storage.object.finalize \
--trigger-resource $GCS_DAI_SPLIT_DOCS \
--set-env-vars=PROJECT_ID=$GOOGLE_CLOUD_PROJECT,PROJECT_NUM=$PROJECT_NUMBER,LOCATION='us',PDAI_INVOICE_PROCESSOR_ID=$INVOICE_PROCESSOR_ID,GCS_RAW_EXTRACT_BUCKET=$GCS_DAI_RAW_ENTITY_EXTRACTION,FIRESTORE_COLLECTION='invoice_extractions',SKIP_HITL=False \
--ingress-settings internal-and-gclb \
--stage-bucket $GCS_CF_STAGE \
--max-instances=10 \
--timeout=120

Note - Setting SKIP_HITL=True will prevent documents from being submitted for Human-in-the-loop review
~~~~

3. Create Cloud Function to support compliing the results from the entity extraction and ground-truth validation performed using Human-in-the-loop review.

~~~
gcloud beta functions deploy compile_results \
--runtime python38 \
--entry-point main_func \
--source compile_hitl_results \
--trigger-event google.storage.object.finalize \
--trigger-resource $GCS_INVOICE_HITL_RESULTS \
--set-env-vars=EXTRACT_FIRESTORE_COLLECTION='invoice_extractions',COMPILED_RESULTS_FIRESTORE_COLLECTION='compiled_invoice_results' \
--stage-bucket $GCS_CF_STAGE \
--ingress-settings internal-and-gclb \
--max-instances=10 \
--timeout=120
~~~

4. Execute the following command to ensure the default service account used on your Cloud Functions has the needed access.

~~~
gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
    --member=serviceAccount:$GOOGLE_CLOUD_PROJECT@appspot.gserviceaccount.com \
    --role="roles/storage.objectAdmin"

gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
    --member=serviceAccount:$GOOGLE_CLOUD_PROJECT@appspot.gserviceaccount.com \
    --role="roles/editor"
~~~