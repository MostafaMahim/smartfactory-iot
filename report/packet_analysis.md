# Module 1 Assignment — Packet Analysis
## Task 4: Wire-Level Protocol Annotation

---

## 4.2 MQTT Packet Annotations

### CONNECT Packet

| Field | Offset (bytes) | Raw Hex | Decoded Value |
|-------|---------------|---------|---------------|
| Frame type + flags (byte 1) | 0 | `10` | Type=CONNECT (0001), flags=0000 |
| Remaining length (byte 2) | 1 | `27` | 39 bytes |
| Protocol name length | 2–3 | `00 04` | 4 |
| Protocol name | 4–7 | `4D 51 54 54` | "MQTT" |
| Protocol version | 8 | `04` | 4 (MQTT 3.1.1) |
| Connect flags | 9 | `C2` | See breakdown below |
| Keep-alive | 10–11 | `00 3C` | 60 seconds |
| Client ID length | 12–13 | `00 1A` | 26 |
| Client ID | 14–… | `73 6D …` | "smartfactory-publisher-001" |

**Connect Flags byte breakdown:**

| Bit | Name | Value | Meaning |
|-----|------|-------|---------|
| 7 | Username flag | 1 | Username present |
| 6 | Password flag | 1 | Password present |
| 5 | Will retain | 0 | Will not retained |
| 4–3 | Will QoS | 00 | Will QoS = 0 |
| 2 | Will flag | 0 | No will message |
| 1 | Clean session | 1 | New session |
| 0 | Reserved | 0 | — |

---

### QoS 1 PUBLISH Packet

| Field | Offset (bytes) | Raw Hex | Decoded Value |
|-------|---------------|---------|---------------|
| Fixed header byte 1 | 0 | `32` | Type=PUBLISH(0011), DUP=0, QoS=01, RETAIN=0 |
| Remaining length | 1 | `4A` | 74 bytes |
| Topic length | 2–3 | `00 1A` | 26 |
| Topic string | 4–… | `66 61 …` | "factory/line1/temperature" |
| Packet Identifier | … | `00 01` | 1 |
| Payload | … | `7B …` | JSON sensor reading |

**Fixed header byte 1 bit expansion:**

| Bits 7–4 (packet type) | Bit 3 (DUP) | Bits 2–1 (QoS) | Bit 0 (RETAIN) |
|------------------------|-------------|----------------|----------------|
| `0011` = PUBLISH (3)  | `0` = No duplicate | `01` = QoS 1 | `0` = Not retained |

---

### PUBACK Packet

| Field | Offset | Raw Hex | Decoded Value |
|-------|--------|---------|---------------|
| Fixed header | 0 | `40` | Type=PUBACK (0100) |
| Remaining length | 1 | `02` | 2 bytes |
| Packet Identifier | 2–3 | `00 01` | 1 |

**Packet Identifier match:** PUBLISH PKT ID = 1 ; PUBACK PKT ID = 1 ; **Match? YES ✓**

---

## 4.3 CoAP Packet Annotations

### CON GET Request

| Field | Bits/Bytes | Raw Value | Decoded Value |
|-------|-----------|-----------|---------------|
| Version (bits 7–6) | 2 bits | `01` | 1 (always 1) |
| Type (bits 5–4) | 2 bits | `00` | 0 = CON |
| TKL (bits 3–0) | 4 bits | `0001` | Token length = 1 |
| Code (byte 1) | 8 bits | `01` | 0.01 = GET |
| Message ID (bytes 2–3) | 16 bits | `5D A2` | 23970 |
| Token (bytes 4–4) | 1 byte | `E3` | 0xE3 |
| Option Delta | 4 bits | `B` | Delta=11, Option#=11 (Uri-Path) |
| Option Length | 4 bits | `7` | 7 bytes |
| Option Value | 7 bytes | `66 61 63 74 6F 72 79` | "factory" |

**Byte 0 full expansion:**

| Bit 7 | Bit 6 | Bit 5 | Bit 4 | Bit 3 | Bit 2 | Bit 1 | Bit 0 |
|-------|-------|-------|-------|-------|-------|-------|-------|
| Ver   | Ver   | T     | T     | TKL   | TKL   | TKL   | TKL   |
| `0`   | `1`   | `0`   | `0`   | `0`   | `0`   | `0`   | `1`   |

---

### ACK 2.05 Content Response

| Field | Bytes | Raw Hex | Decoded Value |
|-------|-------|---------|---------------|
| Fixed header byte 0 | 0 | `61` | Ver=01, T=10 (ACK), TKL=0001 |
| Code byte 1 | 1 | `45` | 2.05 = Content |
| Message ID | 2–3 | `5D A2` | 23970 (matches request? YES ✓) |
| Token | 4 | `E3` | 0xE3 (matches request? YES ✓) |
| Option: Content-Format | … | `C1 32` | Option#=12, Value=50 (application/json) |
| Payload Marker | … | `FF` | 0xFF |
| Payload | … | `7B …` | JSON sensor reading |

---

### Observe Notification

| Field | Value |
|-------|-------|
| Observe option number | 6 |
| Observe sequence value | increments from 0 each notification |
| Message type | CON |
| Response code | 2.05 Content |

---

## 4.4 AMQP Frame Annotations

> AMQP was not implemented in this assignment as per instructions.

---

