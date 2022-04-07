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
             "name": "projects/_/buckets/daitk-invoice-ingest/jha-3-page-sample-Invoice.tiff",
             "type": "storage#object"
          }
        },
        "data": {
          "bucket": "daitk-invoice-ingest",
          "contentType": "image/tiff",
          "kind": "storage#object",
          "md5Hash": "...",
          "metageneration": "1",
          "name": "jha-3-page-sample-Invoice.tiff",
          "size": "352",
          "storageClass": "MULTI_REGIONAL",
          "timeCreated": "2020-04-23T07:38:57.230Z",
          "timeStorageClassUpdated": "2020-04-23T07:38:57.230Z",
          "updated": "2020-04-23T07:38:57.230Z"
        }
      }'