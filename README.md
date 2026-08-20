# Tuya Device Sharing SDK

A Python sdk for Tuya Open API, which provides basic IoT capabilities like device management capabilities, helping you create IoT solutions. 
With diversified devices and industries, Tuya IoT Development Platform opens basic IoT capabilities like device management, AI scenarios, and data analytics services, as well as industry capabilities, helping you create IoT solutions.

## Features
### APIs

- Manager
  - update_device_cache
  - refresh_mq
  - send_commands
  - get_device_stream_allocate
  - query_scenes
  - trigger_scene
  - add_device_listener
  - remove_device_listener
  - unload
- CustomerApi
	- get
	- post
	- put
	- delete
- SharingMQ
	- start
	- stop
	- add_message_listener
	- remove_message_listener
- DeviceRepository
	- query_devices_by_home
	- query_devices_by_ids
	- send_commands
- HomeRepository
	- query_homes
	- query_room_by_device
- SceneRepository
	- query_scenes
	- trigger_scene

## Possible scenarios

- [Smart Life Integration](https://github.com/tuya/tuya-smart-life)

## Usage

## Release Note

| version | Description                                            |
|---------|--------------------------------------------------------|
| 0.1.8   | fix topic error                                        |
| 0.1.9   | fix mq link id                                         |
| 0.2.0   | MQTT bulk subscription                                 |
| 0.2.1   | add updated_status_properties to SharingDeviceListener |
| 0.2.2   | add timestamp to SharingDeviceListener                 |
| 0.2.3   | fix paho-mqtt dependency                               |
| 0.2.4   | fix asbtract decorator                                 |
| 0.2.5   | handle unknown dpid in_on_device_report #39            |
| 0.2.6   | Cancel MQTT reconnect on stop #37                      |
| 0.2.8   | Add report_type to device status  #51                  |
| 0.2.9   | Fix incorrect type hint in DeviceFunction #44 <br/>Add pre-commit workflow #46 <br/>Apply ruff format #47 |
| 0.2.10  | Make enum mapping lookups case-insensitive #55 <br/>Add ruff-check to pre-commit #56 <br/>Add ApiRequestException for failed API responses #58 <br/>Fix 0.2.9 changelog formatting #59 |
| 0.2.11  | Add query_room_by_device to query the room a device belongs to |
| 0.2.12  | Add custom code type validation to disable local reporting when custom-type is enabled #68 |
| 0.2.13  | Fix query_room_by_device to use the terminal API path /v1.0/m/thing/ha/{device_id}/room <br/>Skip AES-GCM decrypt when response result is empty (e.g. device without a room) |
| 0.2.14  | Fix MQTT stale client_id reconnect storm on renewal: fully tear down the old client (loop_stop) and disable paho auto-reconnect so it never re-authenticates with an expired client_id |
| 0.2.15  | Parse electricity meter frames V0/V1/V2 into six parameters (voltage / current / power / reactive power / apparent power / power factor) |

## Installation

`pip3 install tuya-device-sharing-sdk`

## Issue feedback

You can provide feedback on your issue via **Github Issue**.

## License

**tuya-device-sharing-sdk** is available under the MIT license. Please see the [LICENSE](./LICENSE) file for more info.
