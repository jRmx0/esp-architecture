# Level 2 line-curve experiments, part 2

Scratch, not for merging.

## N frontmatter curve linear

```mermaid
---
config:
  flowchart:
    curve: linear
---
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

## O per-edge curve linear on subsystem lines

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
  n_app e1@--- n_platform
  e1@{ curve: linear }
  n_app e2@--- n_server_link
  e2@{ curve: linear }
  n_app e3@--- n_cellular
  e3@{ curve: linear }
  n_app e4@--- n_autopilot_link
  e4@{ curve: linear }
  n_platform e5@--- n_server_link
  e5@{ curve: linear }
  n_platform e6@--- n_cellular
  e6@{ curve: linear }
  n_platform e7@--- n_autopilot_link
  e7@{ curve: linear }
  n_server_link e8@--- n_autopilot_link
  e8@{ curve: linear }
  classDef bus fill:none,stroke:#888,stroke-dasharray:3 3
  class n_uart_modem,n_uart2_board,n_uart0_console,n_gpio_board bus
  classDef device fill:none,stroke:#888
  class n_sim7600,n_user_led,n_autopilot_board,n_ch9102 device
```

## P per-edge curve basis on subsystem lines

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
  n_app e1@--- n_platform
  e1@{ curve: basis }
  n_app e2@--- n_server_link
  e2@{ curve: basis }
  n_app e3@--- n_cellular
  e3@{ curve: basis }
  n_app e4@--- n_autopilot_link
  e4@{ curve: basis }
  n_platform e5@--- n_server_link
  e5@{ curve: basis }
  n_platform e6@--- n_cellular
  e6@{ curve: basis }
  n_platform e7@--- n_autopilot_link
  e7@{ curve: basis }
  n_server_link e8@--- n_autopilot_link
  e8@{ curve: basis }
  classDef bus fill:none,stroke:#888,stroke-dasharray:3 3
  class n_uart_modem,n_uart2_board,n_uart0_console,n_gpio_board bus
  classDef device fill:none,stroke:#888
  class n_sim7600,n_user_led,n_autopilot_board,n_ch9102 device
```

## Q direction TB

```mermaid
flowchart TB
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

