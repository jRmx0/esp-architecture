<!-- esp-architecture:diagrams begin: generated from architecture.yaml by generate_diagrams.py, do not edit -->

## Context

The device and the world around it.

```mermaid
flowchart LR
  n_system[["<b>rmx-mower-gateway</b><br/>ESP32 + SIM7600G-H board that links the mower's autopilot to rmx-server over LTE (MQTT over TLS) and relays NTRIP corrections."]]
  n_rmx_server["<b>rmx_server</b><br/>Broker and server app at mqtt.rmx.lt:8883"]
  n_ntrip_caster["<b>ntrip_caster</b><br/>NTRIP caster for RTK corrections"]
  n_autopilot{{"<b>autopilot</b><br/>Mower autopilot board on the board link"}}
  n_installer(["<b>installer</b><br/>Provisions the device certificate over the serial console"])
  n_system -->|"state, telemetry, metrics, command acks"| n_rmx_server
  n_rmx_server -->|"commands, firmware chunks"| n_system
  n_system -->|"GGA position"| n_ntrip_caster
  n_ntrip_caster -->|"RTCM corrections"| n_system
  n_autopilot -->|"frames to relay, GGA"| n_system
  n_system -->|"corrections, relayed messages, heartbeat"| n_autopilot
  n_installer -->|"device certificate chain"| n_system
```

## Block

Inside the chip: components and the buses they drive; outside: devices on those buses.

```mermaid
block-beta
  columns 1
  block:chip
    columns 6
    chip_title["<b>rmx-mower-gateway</b>"]:6
    n_app_main["app_main"]
    n_supervisor["supervisor"]
    space
    space
    space
    space
    n_mqtt_link["mqtt_link"]
    n_board_link["board_link"]
    n_ntrip["ntrip"]
    n_remote_cmd["remote_cmd"]
    n_ota["ota"]
    n_gwstate["gwstate"]
    n_metrics["metrics"]
    n_monitor["monitor"]
    n_usage["usage"]
    n_devcert["devcert"]
    space
    space
    n_rmx_codec["rmx_codec"]
    space
    space
    space
    space
    space
    n_cell["cell"]
    n_bl_uart["bl_uart"]
    space
    space
    space
    space
    n_board["board"]
    n_settings["settings"]
    n_gw_tasks["gw_tasks"]
    n_gw_link["gw_link"]
    space
    space
    n_uart_modem[/"uart_modem<br/>uart"/]
    n_uart2_board[/"uart2_board<br/>uart"/]
    n_gpio_board[/"gpio_board<br/>gpio"/]
    n_uart0_console[/"uart0_console<br/>uart"/]
    space
    space
  end
  block:outside
    columns 6
    n_sim7600["sim7600<br/>SIM7600G-H LTE modem"]
    space
    space
    space
    space
    space
  end
  style outside fill:none,stroke:none
  n_devcert --> n_uart0_console
  n_cell --> n_sim7600
  n_bl_uart --> n_uart2_board
  n_board --> n_gpio_board
  n_uart_modem --- n_sim7600
  classDef title fill:none,stroke:none
  classDef device fill:none,stroke:#888,stroke-dasharray:4 3
  class chip_title title
  class n_sim7600 device
```

| Task | Component | Priority | Stack |
|---|---|---|---|
| `ntrip` | ntrip | 6 | 4096 |
| `cell_wd` | cell | 5 | 4096 |
| `remote_cmd` | remote_cmd | 4 | 6144 |
| `supervisor` | supervisor | 3 | 6144 |
| `gw_tick` | metrics | 3 | 6144 |
| `ota` | ota | 3 | 12288 |
| `devcert` | devcert | 3 | 6144 |
| `gw_signal` | metrics | 2 | 4096 |

## Organigram

Who calls whom, from the top down (`depends_on`). Red boxes: used by more than one component (gw_link, mqtt_link, usage, rmx_codec, settings); a shared resource needs care against contention. Red arrows: 1 upward, which the layers forbid.

```mermaid
flowchart TD
  n_app_main["app_main"]
  n_supervisor["supervisor"]
  n_mqtt_link["mqtt_link"]
  n_board_link["board_link"]
  n_ntrip["ntrip"]
  n_remote_cmd["remote_cmd"]
  n_ota["ota"]
  n_gwstate["gwstate"]
  n_metrics["metrics"]
  n_monitor["monitor"]
  n_usage["usage"]
  n_devcert["devcert"]
  n_rmx_codec["rmx_codec"]
  n_cell["cell"]
  n_bl_uart["bl_uart"]
  n_board["board"]
  n_settings["settings"]
  n_gw_tasks["gw_tasks"]
  n_gw_link["gw_link"]
  n_app_main --> n_supervisor
  n_supervisor --> n_gw_link
  n_supervisor --> n_mqtt_link
  n_supervisor --> n_cell
  n_supervisor --> n_ota
  n_supervisor --> n_gwstate
  n_supervisor --> n_metrics
  n_mqtt_link --> n_devcert
  n_mqtt_link --> n_usage
  n_mqtt_link --> n_gw_link
  n_board_link --> n_bl_uart
  n_board_link --> n_mqtt_link
  n_board_link --> n_rmx_codec
  n_board_link --> n_gw_link
  n_ntrip --> n_board_link
  n_ntrip --> n_settings
  n_ntrip --> n_gw_link
  n_ntrip --> n_rmx_codec
  n_remote_cmd --> n_mqtt_link
  n_remote_cmd --> n_rmx_codec
  n_ota --> n_mqtt_link
  n_ota --> n_remote_cmd
  n_ota --> n_rmx_codec
  n_gwstate --> n_settings
  n_metrics --> n_mqtt_link
  n_devcert --> n_settings
  n_cell --> n_board
  n_cell --> n_usage
  n_cell --> n_gw_link
  classDef shared stroke:#d33,stroke-width:2px
  class n_gw_link,n_mqtt_link,n_usage,n_rmx_codec,n_settings shared
  linkStyle 27 stroke:#d33,stroke-width:2px
```

## Layering

Layers from the top (application) to the bottom (platform).

```mermaid
block-beta
  columns 1
  block:r_l4_app
    columns 7
    t_l4_app["l4_app"]
    n_app_main["app_main"]
    n_supervisor["supervisor"]
    space
    space
    space
    space
  end
  block:r_l3_services
    columns 7
    t_l3_services["l3_services"]
    n_mqtt_link["mqtt_link"]
    n_board_link["board_link"]
    n_ntrip["ntrip"]
    n_remote_cmd["remote_cmd"]
    n_ota["ota"]
    n_gwstate["gwstate"]
    space
    n_metrics["metrics"]
    n_monitor["monitor"]
    n_usage["usage"]
    n_devcert["devcert"]
    space
    space
  end
  block:r_l2_codecs
    columns 7
    t_l2_codecs["l2_codecs"]
    n_rmx_codec["rmx_codec"]
    space
    space
    space
    space
    space
  end
  block:r_l1_links
    columns 7
    t_l1_links["l1_links"]
    n_cell["cell"]
    n_bl_uart["bl_uart"]
    space
    space
    space
    space
  end
  block:r_l0_platform
    columns 7
    t_l0_platform["l0_platform"]
    n_board["board"]
    n_settings["settings"]
    n_gw_tasks["gw_tasks"]
    n_gw_link["gw_link"]
    space
    space
  end
  classDef title fill:none,stroke:#888,font-weight:bold
  class t_l4_app,t_l3_services,t_l2_codecs,t_l1_links,t_l0_platform title
```

| Layer | Holds |
|---|---|
| `l4_app` | Init order and the supervisor |
| `l3_services` | MQTT, board link, NTRIP, commands, OTA, state, metrics |
| `l2_codecs` | Pure C, no ESP-IDF or FreeRTOS includes, host-tested |
| `l1_links` | Modem and PPP, board UART |
| `l0_platform` | Pins, NVS, task table, link state |

<!-- esp-architecture:diagrams end -->
