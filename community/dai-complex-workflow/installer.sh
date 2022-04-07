#!/bin/bash

read -p 'Enter Project ID: ' PROJECT_ID
read -p 'Enter Project Number: ' PROJECT_NUMBER
read -p 'Enter Deployment Location (us/eu): ' LOCATION

#check_val() {

    #echo "Val 1 $1"
    #if [ '$1' != 'create' ] || [ '$1' != 'destroy' ]
    #then
        #read -p 'Enter Execution Method (create/destroy): ' EXECUTION
        #return 1
    #else
        #return 0
    #fi
#}
read -p 'Enter Execution Method (create/destroy): ' EXECUTION

while ! [[ $EXECUTION == "create" || $EXECUTION == "destroy" ]]
do
    read -p 'Enter Execution Method (create/destroy): ' EXECUTION
#check_val $EXECUTION
done


SPLITTER="PROCUREMENT_DOCUMENT_SPLIT_PROCESSOR/daitk-pdai-splitter"
INVOICE="INVOICE_PROCESSOR/daitk-invoice-processor"
EXPENSE="EXPENSE_PROCESSOR/daitk-expense-processor"

if [ $EXECUTION == "create" ]
then
    echo "Installing DocumentAI-Toolkit"
    echo "Creating DocumentAI Processors..."
    python3 scripts/processor_configurator.py --project_number=$PROJECT_NUMBER --location=$LOCATION --processor=$INVOICE --processor=$SPLITTER --processor=$EXPENSE --action=$EXECUTION
    source vars.sh
    ( cd terraform && terraform init )
    echo "Document AI Processors Created"
    ( cd terraform && terraform apply -var="pdai_expense_processor_id=$EXPENSE_PROCESSOR" -var="pdai_invoice_processor_id=$INVOICE_PROCESSOR" -var="pdai_splitter_id=$PROCUREMENT_DOCUMENT_SPLIT_PROCESSOR" -var="project_id=$PROJECT_ID" -var="project_number=$PROJECT_NUMBER" -var="resource_location=$LOCATION")
    echo "DocumentAI-Toolkit Workflow deployed"

elif [ $EXECUTION == "destroy" ]
then
    echo "Uninstalling DocumentAI-Toolkit"
    source vars.sh
    python3 scripts/processor_configurator.py --project_number=$PROJECT_NUMBER --location=$LOCATION --action=$EXECUTION
    echo "DocumentAP Processers have been removed"
    echo "Removing DocumentAI-Toolkit Workflow Infrastructure"
    ( cd terraform && terraform destroy -var="pdai_expense_processor_id=$EXPENSE_PROCESSOR" -var="pdai_invoice_processor_id=$INVOICE_PROCESSOR" -var="pdai_splitter_id=$PROCUREMENT_DOCUMENT_SPLIT_PROCESSOR" -var="project_id=$PROJECT_ID" -var="project_number=$PROJECT_NUMBER" -var="resource_location=$LOCATION")
    echo "DocumentAI-Toolkit Workflow Infrastructure has been removed. Have a nice day!"

fi
