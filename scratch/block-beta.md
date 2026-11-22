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
