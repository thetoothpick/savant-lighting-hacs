# Savant Lighting for Home Assistant

Websocket-based client integration for Savant Lighting web interface (UI running on Savant Host port 80, websocket server running on port 8480).

Currently working:
* config file initialization
* load lights from host
* turn lights off/on
* handle brightness
* refresh light state after toggling


## Example Config

```yaml
light:
  - platform: savant_lighting
    host: 192.168.x.x
```
