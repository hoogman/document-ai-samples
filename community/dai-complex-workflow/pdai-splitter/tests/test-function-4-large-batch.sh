curl localhost:8080 \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
        "context": {
          "eventId": "1147091835525999",
          "timestamp": "2020-04-23T07:38:57.772Z",
          "eventType": "google.storage.object.finalize",
          "resource": {
             "service": "storage.googleapis.com",
             "name": "projects/_/buckets/daitk-invoice-ingest/SKM_INVOICES--CAD--MAY 252021.pdf",
             "type": "storage#object"
          }
        },
        "data": {
          "bucket": "daitk-invoice-ingest",
          "contentType": "application/pdf",
          "kind": "storage#object",
          "md5Hash": "...",
          "metageneration": "1",
          "name": "SKM_INVOICES--CAD--MAY 252021.pdf",
          "size": "352",
          "storageClass": "MULTI_REGIONAL",
          "timeCreated": "2020-04-23T07:38:57.230Z",
          "timeStorageClassUpdated": "2020-04-23T07:38:57.230Z",
          "updated": "2020-04-23T07:38:57.230Z"
        }
      }'