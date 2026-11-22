<!-- esp-architecture:diagrams begin: generated from architecture.yaml by generate_diagrams.py, do not edit -->

## Context

The device and the world around it.

```mermaid
flowchart LR
  n_system[["<b>rmx-mower-gateway</b>"]]
  n_rmx_server["rmx_server"]
  n_ntrip_caster["ntrip_caster"]
  n_autopilot{{"autopilot"}}
  n_installer(["installer"])
  n_operator(["operator"])
  n_system -->|"state, telemetry"| n_rmx_server
  n_rmx_server -->|"commands, firmware"| n_system
  n_system -->|"GGA"| n_ntrip_caster
  n_ntrip_caster -->|"RTCM"| n_system
  n_autopilot -->|"frames, GGA"| n_system
  n_system -->|"corrections, frames"| n_autopilot
  n_installer -->|"certificate"| n_system
  n_operator -->|"commands"| n_rmx_server
```

## Block

### Level 1a: hardware

The processor and the devices outside it, one line per bus. The ESP32-WROVER-E module has integrated 16 MB flash and 8 MB PSRAM.

```mermaid
flowchart LR
  cpu_box["<b>ESP32-WROVER-E</b>"]
  n_sim7600["SIM7600 modem"]
  n_user_led["user LED"]
  n_autopilot_board["autopilot board"]
  n_ch9102["USB-UART bridge"]
  cpu_box ---|"UART1"| n_sim7600
  cpu_box ---|"GPIO"| n_sim7600
  cpu_box ---|"UART0"| n_ch9102
  cpu_box ---|"GPIO"| n_user_led
  cpu_box ---|"UART2"| n_autopilot_board
  classDef device fill:none,stroke:#888
  class n_sim7600,n_user_led,n_autopilot_board,n_ch9102 device
```

### Level 1b: software

The same hardware, each bus a box inside the processor: the drivers to write.

```mermaid
flowchart LR
  subgraph cpu_box["<b>ESP32-WROVER-E</b>"]
    n_uart_modem["UART1"]
    n_uart2_board["UART2"]
    n_uart0_console["UART0"]
    n_gpio_board["GPIO"]
  end
  n_sim7600["SIM7600 modem"]
  n_user_led["user LED"]
  n_autopilot_board["autopilot board"]
  n_ch9102["USB-UART bridge"]
  n_sim7600 --- n_uart_modem
  n_sim7600 --- n_gpio_board
  n_ch9102 --- n_uart0_console
  n_gpio_board --- n_user_led
  n_uart2_board --- n_autopilot_board
  classDef device fill:none,stroke:#888
  class n_sim7600,n_user_led,n_autopilot_board,n_ch9102 device
```

### Level 2: subsystems

The subsystems inside the processor, each joined to the buses it drives and to the subsystems it is connected to.

```mermaid
flowchart LR
  subgraph cpu_box["<b>ESP32-WROVER-E</b>"]
    n_cellular["<b>cellular</b>"]
    n_server_link["<b>server_link</b>"]
    n_autopilot_link["<b>autopilot_link</b>"]
    n_app["<b>app</b>"]
    n_platform["<b>platform</b>"]
    n_uart_modem["UART1"]
    n_uart2_board["UART2"]
    n_uart0_console["UART0"]
    n_gpio_board["GPIO"]
  end
  n_sim7600["SIM7600 modem"]
  n_user_led["user LED"]
  n_autopilot_board["autopilot board"]
  n_ch9102["USB-UART bridge"]
  n_server_link --- n_uart0_console
  n_cellular --- n_uart_modem
  n_cellular --- n_gpio_board
  n_autopilot_link --- n_uart2_board
  n_uart_modem --- n_sim7600
  n_gpio_board --- n_sim7600
  n_gpio_board --- n_user_led
  n_uart2_board --- n_autopilot_board
  n_uart0_console --- n_ch9102
  n_app --- n_platform
  n_app --- n_server_link
  n_app --- n_cellular
  n_app --- n_autopilot_link
  n_platform --- n_server_link
  n_platform --- n_cellular
  n_platform --- n_autopilot_link
  n_server_link --- n_autopilot_link
  classDef bus fill:none,stroke:#888,stroke-dasharray:3 3
  class n_uart_modem,n_uart2_board,n_uart0_console,n_gpio_board bus
  classDef device fill:none,stroke:#888
  class n_sim7600,n_user_led,n_autopilot_board,n_ch9102 device
```

| Subsystem | Components | Does |
|---|---|---|
| `cellular` | cell, board | LTE modem, PPP and its pins |
| `server_link` | mqtt_link, remote_cmd, ota, metrics, monitor, usage, devcert | MQTT to rmx-server: certificate, commands, OTA, telemetry, byte counts |
| `autopilot_link` | board_link, ntrip, bl_uart | Board link to the autopilot and the NTRIP corrections it carries |
| `app` | app_main, supervisor, gwstate | Init order, supervisor and gateway state |
| `platform` | rmx_codec, settings, gw_tasks, gw_link | NVS, task table, link state and the pure-C codec |

## Organigram

Who calls whom, from the top down (`depends_on`). Amber boxes: used by more than one component (gw_link, mqtt_link, rmx_codec, settings); check contention (one caller at a time, locking, the slowest caller sets the pace).

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
  n_supervisor --> n_ntrip
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
  n_cell --> n_gw_link
  classDef shared stroke:#d98e04,stroke-width:2px
  class n_gw_link,n_mqtt_link,n_rmx_codec,n_settings shared
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
