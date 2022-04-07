curl localhost:8080 \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
        "context": {
          "eventId": "1147091835512345",
          "timestamp": "2020-04-23T07:38:57.772Z",
          "eventType": "google.storage.object.finalize",
          "resource": {
             "service": "storage.googleapis.com",
             "name": "projects/_/buckets/daitk-automation-test-hitl-results/2128119567898801343/1723832540688547840.json",
             "type": "storage#object"
          }
        },
        "data": {
          "bucket": "daitk-automation-test-hitl-results",
          "contentType": "application/json",
          "kind": "storage#object",
          "md5Hash": "...",
          "metageneration": "1",
          "name": "2128119567898801343/1723832540688547840.json",
          "size": "352",
          "storageClass": "MULTI_REGIONAL",
          "timeCreated": "2020-04-23T07:38:57.230Z",
          "timeStorageClassUpdated": "2020-04-23T07:38:57.230Z",
          "updated": "2020-04-23T07:38:57.230Z"
        }
      }'