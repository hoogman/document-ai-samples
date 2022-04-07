variable "project_id" {
  type        = string
  description = "GCP Project ID"
}

variable "project_number" {
  type        = number
  description = "GCP Project Number"
}

variable "resource_location" {
  type        = string
  description = "Location for resources us/eu"
  default     = "us"
}

variable "firestore_location" {
  type        = string
  description = "Location of Firestore instances. Default = us-central"
  default     = "us-central"
}

variable "dai_extraction_fs_collection" {
  type        = string
  description = "Name of Firestore Collection for DAI extraction results. Default = dai_entity_extractions"
  default     = "dai_entity_extractions"
}

variable "upload_cf_dir" {
  type        = string
  description = "Folder Name for DAI upload Cloud Function dir. Default = pdai-splitter"
  default     = "pdai-splitter"
}

variable "extract_cf_dir" {
  type        = string
  description = "Folder Name for DAI extraction Cloud Function dir. Default = pdai-extractor"
  default     = "pdai-extractor"
}
variable "results_compiler_cf_dir" {
  type        = string
  description = "Folder Name for DAI results compiler Cloud Function dir. Default = compile-hitl-results"
  default     = "compile_hitl_results"
}

variable "dai_compiled_results_fs_collection" {
  type        = string
  description = "Name of Firestore Collection for DAI compiled results. Default = dai_compiled_results"
  default     = "dai_compiled_results"
}

variable "dai_compile_results_bq_dataset_id" {
  type        = string
  description = "Bigquery target Dataset ID for results. Default = documentai_toolkit"
  default     = "documentai_toolkit"
}

variable "dai_compile_results_bq_table_kd" {
  type        = string
  description = "Bigquery target Table ID for results. Default = dai_extraction_results"
  default     = "dai_extraction_results"
}

variable "cf_failure_policy" {
  type        = bool
  description = "Cloud Function retry policy. Defaults to false."
  default     = false
}

variable "cf_timeout" {
  type        = number
  description = "Cloud Function timeout value. Default = 120"
  default     = 120
}

variable "cf_mem_size" {
  type        = number
  description = "Cloud Function memory allocation in MB. Default = 256"
  default     = 256

  validation {
    condition     = contains([128, 256, 512], var.cf_mem_size)
    error_message = "Valid values for Cloud Function Memory are: 128, 256, 512."
  }
}

variable "cf_ingress_setting" {
  type        = string
  description = "Cloud Function network ingress setting. Default = ALLOW_INTERNAL_AND_GCLB"
  default     = "ALLOW_INTERNAL_AND_GCLB"
}

variable "skip_hitl" {
  type        = bool
  description = "Set value to true to skip hitl within extraction workflow. Default = false"
  default     = false
}

variable "pdai_splitter_id" {
  type        = string
  description = "PDAI Splitter processor ID"
}

variable "pdai_invoice_processor_id" {
  type        = string
  description = "PDAI Invoice Processor ID"
}

variable "pdai_expense_processor_id" {
  type        = string
  description = "PDAI Expense Processor ID"
}

variable "iam_policy_binding_roles" {
  type        = list(string)
  description = "List of roles to apply project iam policy bindings"
  default     = ["roles/storage.objectAdmin", "roles/editor"]
}
