## UReR Services

### POIS Service

```
endpoint: http://urer-pois-service.herokuapp.com/new_event
```

```
method allowed: POST, expected data as json
```

```json
{
    "request_id": "1322aa",
    "response_at": "http://urer-client.herokuapp.com/receive/recommandation",
    "radius": 200,
    "location": "47.171571, 27.574983",
    "type": "hospital"
}
```

#### Mandatory JSON Keys:
- *response_at* - endpoint where recommandation is sent with POST
- *request_id* -  key-value which is sent in recommandation JSON
- *radius* - area in meters
- *location*- coordinates, lat, lon

#### Optional JSON Keys:
- *output* - json/xml, if not defined response will be as json
- *keyword* - substring of place name
- *type* - type of place - [List of supported types](https://developers.google.com/places/web-service/supported_types)

##### All optional at:
[Google API Places Search](https://developers.google.com/places/web-service/search)

If no places are found from Google Places then response_at will not be called with the result.
