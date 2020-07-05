# MQTT Recorder

Simple cli tool for recording and replaying MQTT messages.

## Usage
|  Argument  |                       Description                      | Required | Default |
|:----------:|:------------------------------------------------------:|----------|:-------:|
| -h, --help | Show help                                              |          |         |
| --host     | MQTT broker address                                    |     x    |         |
| --port     | MQTT broker port                                       |          | 1883    |
| --mode     | mode: record/replay                                    |     x    |         |
| --file     | output/input csv file                                  |     x    |         |
| --loop     | looping replay                                         |          | false   |
| --qos      | Quality of Service that will be used for subscriptions |          | 0       |
| --topics   | json file containing selected topics for subscriptions |          | null    |
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
