# Level 2 line-order experiments

Scratch, not for merging.

## A baseline (c40e978)

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

## B declare by connection count

```mermaid
flowchart LR
  subgraph cpu_box["<b>ESP32-WROVER-E</b>"]
    n_app["<b>app</b>"]
    n_platform["<b>platform</b>"]
    n_server_link["<b>server_link</b>"]
    n_autopilot_link["<b>autopilot_link</b>"]
    n_cellular["<b>cellular</b>"]
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

## C B + lines grouped by subsystem

```mermaid
flowchart LR
  subgraph cpu_box["<b>ESP32-WROVER-E</b>"]
    n_app["<b>app</b>"]
    n_platform["<b>platform</b>"]
    n_server_link["<b>server_link</b>"]
    n_autopilot_link["<b>autopilot_link</b>"]
    n_cellular["<b>cellular</b>"]
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
  n_app --- n_autopilot_link
  n_app --- n_cellular
  n_platform --- n_server_link
  n_platform --- n_autopilot_link
  n_platform --- n_cellular
  n_server_link --- n_autopilot_link
  classDef bus fill:none,stroke:#888,stroke-dasharray:3 3
  class n_uart_modem,n_uart2_board,n_uart0_console,n_gpio_board bus
  classDef device fill:none,stroke:#888
  class n_sim7600,n_user_led,n_autopilot_board,n_ch9102 device
```

## D C + line direction by declaration order

```mermaid
flowchart LR
  subgraph cpu_box["<b>ESP32-WROVER-E</b>"]
    n_app["<b>app</b>"]
    n_platform["<b>platform</b>"]
    n_server_link["<b>server_link</b>"]
    n_autopilot_link["<b>autopilot_link</b>"]
    n_cellular["<b>cellular</b>"]
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
  n_app --- n_autopilot_link
  n_app --- n_cellular
  n_platform --- n_server_link
  n_platform --- n_autopilot_link
  n_platform --- n_cellular
  n_server_link --- n_autopilot_link
  classDef bus fill:none,stroke:#888,stroke-dasharray:3 3
  class n_uart_modem,n_uart2_board,n_uart0_console,n_gpio_board bus
  classDef device fill:none,stroke:#888
  class n_sim7600,n_user_led,n_autopilot_board,n_ch9102 device
```

## E C + subsystem lines before bus lines

```mermaid
flowchart LR
  subgraph cpu_box["<b>ESP32-WROVER-E</b>"]
    n_app["<b>app</b>"]
    n_platform["<b>platform</b>"]
    n_server_link["<b>server_link</b>"]
    n_autopilot_link["<b>autopilot_link</b>"]
    n_cellular["<b>cellular</b>"]
    n_uart_modem["UART1"]
    n_uart2_board["UART2"]
    n_uart0_console["UART0"]
    n_gpio_board["GPIO"]
  end
  n_sim7600["SIM7600 modem"]
  n_user_led["user LED"]
  n_autopilot_board["autopilot board"]
  n_ch9102["USB-UART bridge"]
  n_app --- n_platform
  n_app --- n_server_link
  n_app --- n_autopilot_link
  n_app --- n_cellular
  n_platform --- n_server_link
  n_platform --- n_autopilot_link
  n_platform --- n_cellular
  n_server_link --- n_autopilot_link
  n_server_link --- n_uart0_console
  n_cellular --- n_uart_modem
  n_cellular --- n_gpio_board
  n_autopilot_link --- n_uart2_board
  n_uart_modem --- n_sim7600
  n_gpio_board --- n_sim7600
  n_gpio_board --- n_user_led
  n_uart2_board --- n_autopilot_board
  n_uart0_console --- n_ch9102
  classDef bus fill:none,stroke:#888,stroke-dasharray:3 3
  class n_uart_modem,n_uart2_board,n_uart0_console,n_gpio_board bus
  classDef device fill:none,stroke:#888
  class n_sim7600,n_user_led,n_autopilot_board,n_ch9102 device
```

## F C without invisible links

```mermaid
flowchart LR
  subgraph cpu_box["<b>ESP32-WROVER-E</b>"]
    n_app["<b>app</b>"]
    n_platform["<b>platform</b>"]
    n_server_link["<b>server_link</b>"]
    n_autopilot_link["<b>autopilot_link</b>"]
    n_cellular["<b>cellular</b>"]
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
  n_app --- n_autopilot_link
  n_app --- n_cellular
  n_platform --- n_server_link
  n_platform --- n_autopilot_link
  n_platform --- n_cellular
  n_server_link --- n_autopilot_link
  classDef bus fill:none,stroke:#888,stroke-dasharray:3 3
  class n_uart_modem,n_uart2_board,n_uart0_console,n_gpio_board bus
  classDef device fill:none,stroke:#888
  class n_sim7600,n_user_led,n_autopilot_board,n_ch9102 device
```

## G D without invisible links

```mermaid
flowchart LR
  subgraph cpu_box["<b>ESP32-WROVER-E</b>"]
    n_app["<b>app</b>"]
    n_platform["<b>platform</b>"]
    n_server_link["<b>server_link</b>"]
    n_autopilot_link["<b>autopilot_link</b>"]
    n_cellular["<b>cellular</b>"]
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
  n_app --- n_autopilot_link
  n_app --- n_cellular
  n_platform --- n_server_link
  n_platform --- n_autopilot_link
  n_platform --- n_cellular
  n_server_link --- n_autopilot_link
  classDef bus fill:none,stroke:#888,stroke-dasharray:3 3
  class n_uart_modem,n_uart2_board,n_uart0_console,n_gpio_board bus
  classDef device fill:none,stroke:#888
  class n_sim7600,n_user_led,n_autopilot_board,n_ch9102 device
```

## H C with ELK layout

```mermaid
---
config:
  layout: elk
---
flowchart LR
  subgraph cpu_box["<b>ESP32-WROVER-E</b>"]
    n_app["<b>app</b>"]
    n_platform["<b>platform</b>"]
    n_server_link["<b>server_link</b>"]
    n_autopilot_link["<b>autopilot_link</b>"]
    n_cellular["<b>cellular</b>"]
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
  n_app --- n_autopilot_link
  n_app --- n_cellular
  n_platform --- n_server_link
  n_platform --- n_autopilot_link
  n_platform --- n_cellular
  n_server_link --- n_autopilot_link
  classDef bus fill:none,stroke:#888,stroke-dasharray:3 3
  class n_uart_modem,n_uart2_board,n_uart0_console,n_gpio_board bus
  classDef device fill:none,stroke:#888
  class n_sim7600,n_user_led,n_autopilot_board,n_ch9102 device
```

