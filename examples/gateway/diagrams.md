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
flowchart TB
  subgraph chip["rmx-mower-gateway"]
    subgraph B_l4_app["l4_app"]
      n_app_main["app_main"]
      n_supervisor["supervisor"]
    end
    subgraph B_l3_services["l3_services"]
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
    end
    subgraph B_l2_codecs["l2_codecs"]
      n_rmx_codec["rmx_codec"]
    end
    subgraph B_l1_links["l1_links"]
      n_cell["cell"]
      n_bl_uart["bl_uart"]
    end
    subgraph B_l0_platform["l0_platform"]
      n_board["board"]
      n_settings["settings"]
      n_gw_tasks["gw_tasks"]
      n_gw_link["gw_link"]
    end
    subgraph B_buses["peripherals"]
      n_uart_modem[/"uart_modem<br/>uart"/]
      n_uart2_board[/"uart2_board<br/>uart"/]
      n_uart0_console[/"uart0_console<br/>uart"/]
      n_gpio_board[/"gpio_board<br/>gpio"/]
    end
    B_l4_app ~~~ B_l3_services
    B_l3_services ~~~ B_l2_codecs
    B_l2_codecs ~~~ B_l1_links
    B_l1_links ~~~ B_l0_platform
    B_l0_platform ~~~ B_buses
  end
  n_sim7600{{"sim7600<br/>SIM7600G-H LTE modem"}}
  n_uart_modem --- n_sim7600
  n_devcert --- n_uart0_console
  n_cell --- n_sim7600
  n_bl_uart --- n_uart2_board
  n_board --- n_gpio_board
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
flowchart TB
  subgraph L_l4_app["<b>l4_app</b>: Init order and the supervisor"]
    n_app_main["app_main"]
    n_supervisor["supervisor"]
  end
  subgraph L_l3_services["<b>l3_services</b>: MQTT, board link, NTRIP, commands, OTA, state, metrics"]
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
  end
  subgraph L_l2_codecs["<b>l2_codecs</b>: Pure C, no ESP-IDF or FreeRTOS includes, host-tested"]
    n_rmx_codec["rmx_codec"]
  end
  subgraph L_l1_links["<b>l1_links</b>: Modem and PPP, board UART"]
    n_cell["cell"]
    n_bl_uart["bl_uart"]
  end
  subgraph L_l0_platform["<b>l0_platform</b>: Pins, NVS, task table, link state"]
    n_board["board"]
    n_settings["settings"]
    n_gw_tasks["gw_tasks"]
    n_gw_link["gw_link"]
  end
  n_app_main ~~~ n_mqtt_link
  n_mqtt_link ~~~ n_rmx_codec
  n_rmx_codec ~~~ n_cell
  n_cell ~~~ n_board
```

<!-- esp-architecture:diagrams end -->
