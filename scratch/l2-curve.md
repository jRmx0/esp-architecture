# Level 2 line-curve experiments

Scratch, not for merging. Same graph as c40e978; only the init line differs.

## I curve basis

```mermaid
%%{init: {"flowchart": {"curve": "basis"}}}%%
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

## J curve linear

```mermaid
%%{init: {"flowchart": {"curve": "linear"}}}%%
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

## K curve linear, rankSpacing 80

```mermaid
%%{init: {"flowchart": {"curve": "linear", "rankSpacing": 80}}}%%
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

## L curve monotoneX

```mermaid
%%{init: {"flowchart": {"curve": "monotoneX"}}}%%
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

## M curve basis, rankSpacing 80, nodeSpacing 40

```mermaid
%%{init: {"flowchart": {"curve": "basis", "rankSpacing": 80, "nodeSpacing": 40}}}%%
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

