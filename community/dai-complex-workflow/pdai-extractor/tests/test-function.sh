curl localhost:8080 \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
        "context": {
          "eventId": "1147091835525155",
          "timestamp": "2020-04-23T07:38:57.772Z",
          "eventType": "google.storage.object.finalize",
          "resource": {
             "service": "storage.googleapis.com",
             "name": "projects/_/buckets/daitk-split-invoice-output/bqe-invoice-sample-invoice_statement-0-2498924141755607.pdf",
             "type": "storage#object"
          }
        },
        "data": {
          "bucket": "daitk-split-invoice-output",
          "contentType": "application/pdf",
          "kind": "storage#object",
          "md5Hash": "...",
          "metageneration": "1",
          "name": "bqe-invoice-sample-invoice_statement-0-2498924141755607.pdf",
          "size": "352",
          "storageClass": "MULTI_REGIONAL",
          "timeCreated": "2020-04-23T07:38:57.230Z",
          "timeStorageClassUpdated": "2020-04-23T07:38:57.230Z",
          "updated": "2020-04-23T07:38:57.230Z"
        }
      }'