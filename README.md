# MQTT Recorder

Simple cli tool for recording and replaying MQTT messages.

# Install

`pip install mqtt-recorder`

## Usage
|   Argument   |                        Description                       | Required | Default |
|:------------:|:--------------------------------------------------------:|----------|:-------:|
| -h, --help   | Show help                                                |          |         |
| --host       | MQTT broker address                                      |     x    |         |
| --port       | MQTT broker port                                         |          | 1883    |
| --mode       | mode: record/replay                                      |     x    |         |
| --file       | output/input csv file                                    |     x    |         |
| --loop       | looping replay                                           |          | false   |
| --qos        | Quality of Service that will be used for subscriptions   |          | 0       |
| --topics     | json file containing selected topics for subscriptions   |          | null    |
| --enable_ssl | True to enable MQTTs support, False otherwise            |          | False   |
| --ca_cert    | Path to the Certificate Authority certificate files      |          | None    |
| --certfile   | Path to the client certificate                           |          | None    |
| --keyfile    | Path to the client private key                           |          | None    |
| --username   | MQTT broker username                                     |          | None    |
| --password   | MQTT broker password                                     |          | None    |
| --encode_b64 | True to store message payloads as base64 encoded strings |          | False   |
### Recording
#### Subscribing to every topic
`mqtt-recorder --host localhost --mode record --file recording.csv`
#### Subscribing to selected topics
`mqtt-recorder --host localhost --mode record --file test.csv --topics topics.json`<br>
Topics can be selected using a json file.
Example
```json
{
    "topics": [
        "/myhome/groundfloor/livingroom/temperature",
        "USA/California/San Francisco/Silicon Valley"
    ]
}
```
### Replaying
`mqtt-recorder --host localhost --mode replay --file test.csv`
