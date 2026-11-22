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

