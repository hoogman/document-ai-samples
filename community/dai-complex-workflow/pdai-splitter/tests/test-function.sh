curl localhost:8080 \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
        "context": {
          "eventId": "1147091835525187",
          "timestamp": "2020-04-23T07:38:57.772Z",
          "eventType": "google.storage.object.finalize",
          "resource": {
             "service": "storage.googleapis.com",
             "name": "projects/_/buckets/em-inbound-purchase-orders/test4.pdf",
             "type": "storage#object"
          }
        },
        "data": {
          "bucket": "em-inbound-purchase-orders",
          "contentType": "application/pdf",
          "kind": "storage#object",
          "md5Hash": "...",
          "metageneration": "1",
          "name": "test4.pdf",
          "size": "352",
          "storageClass": "MULTI_REGIONAL",
          "timeCreated": "2020-04-23T07:38:57.230Z",
          "timeStorageClassUpdated": "2020-04-23T07:38:57.230Z",
          "updated": "2020-04-23T07:38:57.230Z"
        }
      }'