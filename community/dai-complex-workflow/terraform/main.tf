resource "google_project_service" "storage_service" {
  project = var.project_id
  service = "storage.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "firestore_service" {
  project = var.project_id
  service = "firestore.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "cloudfunctions_service" {
  project = var.project_id
  service = "cloudfunctions.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "documentai_service" {
  project = var.project_id
  service = "documentai.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "cloudbuild_service" {
  project = var.project_id
  service = "cloudbuild.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "appengine_service" {
  project = var.project_id
  service = "appengine.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "logging_service" {
  project = var.project_id
  service = "logging.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "bigquery_service" {
  project = var.project_id
  service = "bigquery.googleapis.com"
  disable_on_destroy = false
}
#time delay for service api enablement
resource "time_sleep" "wait_for_cf_service_enable" {
  create_duration = "60s"
  depends_on = [
    google_project_service.cloudfunctions_service
  ]
}
#Configure GCS buckets
resource "google_storage_bucket" "dai_upload" {
  name                        = "${var.project_id}-dai-upload"
  location                    = var.resource_location
  project                     = var.project_id
  uniform_bucket_level_access = true
  force_destroy = true
}

resource "google_storage_bucket" "dai_split_docs" {
  name                        = "${var.project_id}-dai-split-docs"
  location                    = var.resource_location
  project                     = var.project_id
  uniform_bucket_level_access = true
  force_destroy = true
}

resource "google_storage_bucket" "dai_raw_splitter_response" {
  name                        = "${var.project_id}-dai-raw-splitter-response"
  location                    = var.resource_location
  project                     = var.project_id
  uniform_bucket_level_access = true
  force_destroy = true
}

resource "google_storage_bucket" "dai_raw_entity_extraction" {
  name                        = "${var.project_id}-dai-raw-entity-extraction"
  location                    = var.resource_location
  project                     = var.project_id
  uniform_bucket_level_access = true
  force_destroy = true
}

resource "google_storage_bucket" "cf_stage" {
  name                        = "${var.project_id}-cf-stage"
  location                    = var.resource_location
  project                     = var.project_id
  uniform_bucket_level_access = true
  force_destroy = true
}

resource "google_storage_bucket" "hitl_results" {
  name                        = "${var.project_id}-hitl-results"
  location                    = var.resource_location
  project                     = var.project_id
  uniform_bucket_level_access = true
  force_destroy = true
}

resource "google_storage_bucket" "hitl_instructions" {
  name                        = "${var.project_id}-hitl-reviewer_instructions"
  location                    = var.resource_location
  project                     = var.project_id
  uniform_bucket_level_access = true
  force_destroy = true
}

#Firestore Configuration
resource "google_app_engine_application" "firestore_instance" {
  project       = var.project_id
  location_id   = var.firestore_location
  database_type = "CLOUD_FIRESTORE"
}

#create upload cloud function

data "archive_file" "upload_zip" {
  type        = "zip"
  source_dir  = "${path.root}/../${var.upload_cf_dir}"
  output_path = "${path.root}/../cf_staging/${var.upload_cf_dir}.zip"
}

resource "google_storage_bucket_object" "cf_upload_object" {
  name   = "${data.archive_file.upload_zip.output_md5}.zip"
  bucket = google_storage_bucket.cf_stage.name
  source = data.archive_file.upload_zip.output_path
}

resource "google_cloudfunctions_function" "doc_upload" {
  name        = "doc_upload"
  description = "Doc Upload function handles the splitting/classification of documents"
  runtime     = "python38"

  available_memory_mb   = var.cf_mem_size
  source_archive_bucket = google_storage_bucket.cf_stage.name
  source_archive_object = google_storage_bucket_object.cf_upload_object.name
  event_trigger {
    event_type = "google.storage.object.finalize"
    resource   = google_storage_bucket.dai_upload.name
    failure_policy {
      retry = var.cf_failure_policy
    }
  }
  timeout          = var.cf_timeout
  entry_point      = "main_func"
  ingress_settings = var.cf_ingress_setting
  environment_variables = {
    PROJECT_ID               = var.project_id
    LOCATION                 = var.resource_location
    PROJECT_NUM              = var.project_number
    PDAI_SPLITTER_ID         = var.pdai_splitter_id
    SPLIT_INVOICE_BUCKET     = google_storage_bucket.dai_split_docs.name
    SPLITTER_RESPONSE_BUCKET = google_storage_bucket.dai_raw_splitter_response.name
  }
  depends_on = [
    time_sleep.wait_for_cf_service_enable
  ]
}

#create extract cloud function
data "archive_file" "extract_zip" {
  type        = "zip"
  source_dir  = "${path.root}/../${var.extract_cf_dir}"
  output_path = "${path.root}/../cf_staging/${var.extract_cf_dir}.zip"
}

resource "google_storage_bucket_object" "cf_extract_object" {
  name   = "${data.archive_file.extract_zip.output_md5}.zip"
  bucket = google_storage_bucket.cf_stage.name
  source = data.archive_file.extract_zip.output_path
}

resource "google_cloudfunctions_function" "doc_extract" {
  name        = "doc_extract"
  description = "Doc Extract handles Entity extraction from documents"
  runtime     = "python38"

  available_memory_mb   = var.cf_mem_size
  source_archive_bucket = google_storage_bucket.cf_stage.name
  source_archive_object = google_storage_bucket_object.cf_extract_object.name
  event_trigger {
    event_type = "google.storage.object.finalize"
    resource   = google_storage_bucket.dai_split_docs.name
    failure_policy {
      retry = var.cf_failure_policy
    }
  }
  timeout          = var.cf_timeout
  entry_point      = "main_func"
  ingress_settings = var.cf_ingress_setting
  environment_variables = {
    PROJECT_ID                = var.project_id
    LOCATION                  = var.resource_location
    PROJECT_NUM               = var.project_number
    PDAI_INVOICE_PROCESSOR_ID = var.pdai_invoice_processor_id
    PDAI_EXPENSE_PROCESSOR_ID = var.pdai_expense_processor_id
    GCS_RAW_EXTRACT_BUCKET    = google_storage_bucket.dai_raw_entity_extraction.name
    FIRESTORE_COLLECTION      = var.dai_extraction_fs_collection
    SKIP_HITL                 = var.skip_hitl
  }
  depends_on = [
    time_sleep.wait_for_cf_service_enable
  ]
}

#create results cloud function

data "archive_file" "compile_results_zip" {
  type        = "zip"
  source_dir  = "${path.root}/../${var.results_compiler_cf_dir}"
  output_path = "${path.root}/../cf_staging/${var.results_compiler_cf_dir}.zip"
}

resource "google_storage_bucket_object" "cf_compile_results_object" {
  name   = "${data.archive_file.compile_results_zip.output_md5}.zip"
  bucket = google_storage_bucket.cf_stage.name
  source = data.archive_file.compile_results_zip.output_path
}

resource "google_cloudfunctions_function" "compile_results" {
  name        = "compile_results"
  description = "Process HITL results and merge with extraction results."
  runtime     = "python38"

  available_memory_mb   = var.cf_mem_size
  source_archive_bucket = google_storage_bucket.cf_stage.name
  source_archive_object = google_storage_bucket_object.cf_compile_results_object.name
  event_trigger {
    event_type = "google.storage.object.finalize"
    resource   = google_storage_bucket.hitl_results.name
    failure_policy {
      retry = var.cf_failure_policy
    }
  }
  timeout          = var.cf_timeout
  entry_point      = "main_func"
  ingress_settings = var.cf_ingress_setting
  environment_variables = {
    EXTRACT_FIRESTORE_COLLECTION          = var.dai_extraction_fs_collection
    COMPILED_RESULTS_FIRESTORE_COLLECTION = var.dai_compiled_results_fs_collection
    BQ_RESULTS_TABLE_ID                   = "${var.dai_compile_results_bq_dataset_id}.${var.dai_compile_results_bq_table_kd}"
    BQ_SCHEMA_FILE                        = "/bq_schema/dai_results_schema.json"
    PROJECT_ID                            = var.project_id
  }
  depends_on = [
    time_sleep.wait_for_cf_service_enable
  ]
}

#IAM project policy bindings to ensure Cloud Function Service Account has access to nessassary resources

resource "google_project_iam_binding" "storage_iam_policy_binding" {
  for_each = toset(var.iam_policy_binding_roles)
  project  = var.project_id
  role     = each.value

  members = [
    "serviceAccount:${var.project_id}@appspot.gserviceaccount.com",
  ]
}
