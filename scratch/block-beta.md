# Block diagram in block-beta: scratch

Scratch branch for redrawing the block diagram step by step. Not for merging.

## Test: edge labels

A. Labelled arrow, the docs' syntax `a -- "UART1" --> b`:

```mermaid
block-beta
  columns 3
  a["modem"] space b["processor"]
  a -- "UART1" --> b
```

B. Labelled line without an arrowhead, `a -- "UART1" --- b`:

```mermaid
block-beta
  columns 3
  a["modem"] space b["processor"]
  a -- "UART1" --- b
```

C. Composite block with a title, `block:cpu["ESP32-WROVER-E"]`:

```mermaid
block-beta
  columns 3
  a["modem"] space
  block:cpu["ESP32-WROVER-E"]
    columns 1
    u["UART1"]
  end
  a -- "UART1" --> u
```

## Step 1: level 1a, hardware

The processor and the devices outside it, one line per bus. The ESP32-WROVER-E module has integrated 16 MB flash and 8 MB PSRAM.

```mermaid
block-beta
  columns 5
  block:left
    columns 1
    sim7600["SIM7600 modem"]
    space
    ch9102["USB-UART bridge"]
  end
  space
  cpu["<b>ESP32-WROVER-E</b>"]
  space
  block:right
    columns 1
    user_led["user LED"]
    space
    autopilot_board["autopilot board"]
  end
  sim7600 -- "UART1" --- cpu
  sim7600 -- "GPIO" --- cpu
  ch9102 -- "UART0" --- cpu
  cpu -- "GPIO" --- user_led
  cpu -- "UART2" --- autopilot_board
  classDef device fill:none,stroke:#888
  class sim7600,ch9102,user_led,autopilot_board device
```

### Step 1, v2

v1 problems: the SIM7600's two lines join the same two boxes, so they overlap ("tGPIOI"); the device groups get a yellow composite fill. v2: the processor is a composite of three invisible rows, so each line ends at its own height; the groups have no fill or border.

```mermaid
block-beta
  columns 5
  block:left
    columns 1
    sim7600["SIM7600 modem"]
    space
    ch9102["USB-UART bridge"]
  end
  space
  block:cpu
    columns 1
    r1[" "]
    r2["<b>ESP32-WROVER-E</b>"]
    r3[" "]
  end
  space
  block:right
    columns 1
    user_led["user LED"]
    space
    autopilot_board["autopilot board"]
  end
  sim7600 -- "UART1" --- r1
  sim7600 -- "GPIO" --- r2
  ch9102 -- "UART0" --- r3
  r1 -- "GPIO" --- user_led
  r3 -- "UART2" --- autopilot_board
  classDef device fill:none,stroke:#888
  classDef port fill:none,stroke:none
  classDef group fill:none,stroke:none
  class sim7600,ch9102,user_led,autopilot_board device
  class r1,r2,r3 port
  class left,right group
```

## Level 2, subsystems: v1

1a and 1b stay as they are (flowcharts). Level 2 in block-beta, as a grid inside the processor: the subsystems that drive no bus (app, platform) in the inner column, each bus-driving subsystem in the middle column on the same row as its bus, the bus boxes at the processor's edge, and the devices outside, on their bus's row.

```mermaid
block-beta
  columns 5
  block:cpu:3
    columns 3
    title["<b>ESP32-WROVER-E</b>"]:3
    app["<b>app</b>"] server_link["<b>server_link</b>"] uart0["UART0"]
    space autopilot_link["<b>autopilot_link</b>"] uart2["UART2"]
    platform["<b>platform</b>"] cellular["<b>cellular</b>"] uart1["UART1"]
    space space gpio["GPIO"]
  end
  space
  block:devs
    columns 1
    space
    ch9102["USB-UART bridge"]
    autopilot_board["autopilot board"]
    sim7600["SIM7600 modem"]
    user_led["user LED"]
  end
  server_link --- uart0
  autopilot_link --- uart2
  cellular --- uart1
  cellular --- gpio
  uart0 --- ch9102
  uart2 --- autopilot_board
  uart1 --- sim7600
  gpio --- sim7600
  gpio --- user_led
  classDef title fill:none,stroke:none
  classDef bus fill:none,stroke:#888,stroke-dasharray:3 3
  classDef device fill:none,stroke:#888
  classDef group fill:none,stroke:none
  class title title
  class uart0,uart2,uart1,gpio bus
  class ch9102,autopilot_board,sim7600,user_led device
  class devs group
```

## Level 2, subsystems: v2

v1 changes, from the user: no lines inside the processor, and every box solid. Placement alone ties a subsystem to the bus beside it; lines only leave the processor, from a bus to its devices.

```mermaid
block-beta
  columns 5
  block:cpu:3
    columns 3
    title["<b>ESP32-WROVER-E</b>"]:3
    app["<b>app</b>"] server_link["<b>server_link</b>"] uart0["UART0"]
    space autopilot_link["<b>autopilot_link</b>"] uart2["UART2"]
    platform["<b>platform</b>"] cellular["<b>cellular</b>"] uart1["UART1"]
    space space gpio["GPIO"]
  end
  space
  block:devs
    columns 1
    space
    ch9102["USB-UART bridge"]
    autopilot_board["autopilot board"]
    sim7600["SIM7600 modem"]
    user_led["user LED"]
  end
  uart0 --- ch9102
  uart2 --- autopilot_board
  uart1 --- sim7600
  gpio --- sim7600
  gpio --- user_led
  classDef title fill:none,stroke:none
  classDef bus fill:none,stroke:#888
  classDef device fill:none,stroke:#888
  classDef group fill:none,stroke:none
  class title title
  class uart0,uart2,uart1,gpio bus
  class ch9102,autopilot_board,sim7600,user_led device
  class devs group
```

## Level 2, subsystems: v3

v2 change, from the user: one style for every box. Subsystems, buses and devices are all plain outlines with plain labels; only the processor's title is bold.

```mermaid
block-beta
  columns 5
  block:cpu:3
    columns 3
    title["<b>ESP32-WROVER-E</b>"]:3
    app["app"] server_link["server_link"] uart0["UART0"]
    space autopilot_link["autopilot_link"] uart2["UART2"]
    platform["platform"] cellular["cellular"] uart1["UART1"]
    space space gpio["GPIO"]
  end
  space
  block:devs
    columns 1
    space
    ch9102["USB-UART bridge"]
    autopilot_board["autopilot board"]
    sim7600["SIM7600 modem"]
    user_led["user LED"]
  end
  uart0 --- ch9102
  uart2 --- autopilot_board
  uart1 --- sim7600
  gpio --- sim7600
  gpio --- user_led
  classDef title fill:none,stroke:none
  classDef box fill:none,stroke:#888
  classDef group fill:none,stroke:none
  class title title
  class app,server_link,autopilot_link,platform,cellular,uart0,uart2,uart1,gpio,ch9102,autopilot_board,sim7600,user_led box
  class devs group
```
