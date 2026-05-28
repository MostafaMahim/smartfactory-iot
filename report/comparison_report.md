# Module 1 Assignment — Protocol Comparison Report

**Student Name:** ______Mostafa Mahim Masrukh_____________________
**Student ID:**   _____101042730______________________
**Date:**         _______05/28/2026____________________

---

## 5.1 QoS Comparison Results Table

> Run `pytest tests/mqtt/test_qos_loss.py -v -s` and paste the output table here.

| Protocol / QoS      | Sent | Received | Lost (%) | Duplicates | Avg Latency (ms) |
|---------------------|------|----------|----------|------------|-----------------|
| MQTT QoS 0          | 360  | 323      | 10.3%    | 0          | < 1             |
| MQTT QoS 1          | 360  | 360      | 0.0%     | 4          | 2–8             |
| MQTT QoS 2          | 360  | 360      | 0.0%     | 0          | 5–15            |
| CoAP NON            | 120  | 107      | 10.8%    | 0          | < 1             |
| CoAP CON            | 120  | 120      | 0.0%     | 2          | 3–12            |
| AMQP (confirms off) | 120  | 120      | 0.0%     | 0          | 4–10            |

**Analysis Questions:**

1. **Why does QoS 0 lose messages while QoS 1 and 2 do not?** *(2–3 sentences)*

   QoS 0 is fire-and-forget — the broker never sends back an acknowledgement, 
   so if a packet is dropped on the network, it is simply lost forever. QoS 1 and 
   QoS 2 both use acknowledgement messages (PUBACK) to confirm delivery, so the 
   sender retransmits automatically if no acknowledgement arrives within the timeout.

2. **QoS 1 may show duplicates. Under what circumstances does this happen, and is it a problem for sensor telemetry?** *(2–3 sentences)*

   Duplicates happen when the PUBACK acknowledgement is lost — the sender 
   retransmits the message even though the broker already received it. For sensor 
   telemetry this is acceptable because receiving a duplicate temperature reading 
   causes no harm — we just process it twice.

3. **QoS 2 has higher latency than QoS 1. What causes this, and when is the trade-off worth it?** *(2–3 sentences)*

   QoS 2 uses a 4-step handshake (PUBLISH → PUBREC → PUBREL → PUBCOMP) instead 
   of QoS 1's 2-step (PUBLISH → PUBACK), which doubles the round trips and adds 
   5–15ms latency. This trade-off is worth it for safety-critical commands like 
   turning a cooling fan ON or OFF where duplicate or lost messages could damage 
   equipment.

---

## 5.2 CoAP–HTTP Proxy Mapping

> Run `pytest tests/coap/test_proxy.py -v -s` and record the observed HTTP headers.

| HTTP Header             | CoAP Option          | Your Observed Value        |
|-------------------------|----------------------|----------------------------|
| Content-Type            | Content-Format (12)  | application/json           |
| Cache-Control: max-age  | Max-Age (14)         | max-age=60                 |
| ETag                    | ETag (4)             | a3f2c1d8 (8-byte hex)      |
| Location                | Location-Path (8)    | /factory/line1/temperature |

---


### Data Path Recommendations

| Data Path | Recommended Protocol | Justification |
|-----------|---------------------|---------------|
| Sensor → Cloud (high frequency, <100 ms latency) | MQTT QoS 1 | Lightweight pub/sub, 2-8ms latency, handles fan-out to multiple consumers |
| Actuator commands (safety-critical, exactly-once) | MQTT QoS 2 | 4-way handshake guarantees exactly-once delivery, prevents dangerous duplicates |
| Backend service-to-service routing | AMQP | Topic exchange routing, dead-letter queues, publisher confirms for reliability |
| OTA firmware delivery to constrained MCU (Class 2) | CoAP Block2 | Designed for tiny devices, Block2 splits large files into chunks automatically |

### Detailed Justification

> ### Sensor → Cloud (MQTT QoS 1)
MQTT was purpose-built for IoT sensor data. In our implementation, the publisher 
connected to Mosquitto with a persistent session (clean_session=False) and published 
6 sensors at 1-second intervals. Our QoS experiment measured average latency of 2-8ms 
for QoS 1 with zero message loss, making it ideal for high-frequency telemetry. The 
publish/subscribe model means sensors never need to know who is consuming their data — 
the broker handles fan-out to multiple consumers automatically. QoS 0 was rejected 
because it lost 10.3% of messages under 10% packet loss conditions, which is 
unacceptable for factory monitoring.

### Actuator Commands (MQTT QoS 2)
Actuator commands like turning a cooling fan ON or OFF are safety-critical. Sending a 
duplicate OFF command during a thermal event could damage equipment. MQTT QoS 2 is the 
only mode that guarantees exactly-once delivery using a 4-way handshake 
(PUBLISH → PUBREC → PUBREL → PUBCOMP). Our experiment showed zero duplicates at QoS 2 
compared to 4 duplicates at QoS 1 over 60 seconds. The extra 5-15ms latency is a 
worthwhile trade-off for safety-critical operations.

### Backend Service-to-Service Routing (AMQP)
When sensor data needs routing to multiple internal consumers such as alerting services, 
databases, and analytics pipelines, AMQP provides flexible routing that MQTT cannot 
match. AMQP topic exchanges allow routing keys like factory.line1.temperature.critical 
so each consumer only receives relevant messages. Dead-letter queues capture failed 
messages for inspection, and publisher confirms give producers reliable acknowledgement 
that messages were persisted before clearing their buffer.

### OTA Firmware Delivery (CoAP Block2)
RFC 7252 Class 2 devices have only 50KB RAM and 250KB flash — too small for MQTT or 
AMQP stacks. CoAP runs over UDP with a minimal 4-byte header. Block2 transfer 
automatically fragments large firmware files into MTU-sized chunks, each individually 
acknowledged. In our implementation, the 3KB+ manifest was correctly fragmented and 
reassembled by aiocoap without any extra application code. The Observe mechanism also 
lets devices subscribe to OTA notifications and wake only when a new firmware version 
is available, saving battery life.

---


### Technical Challenge

The most significant challenge was understanding MQTT persistent sessions. When 
clean_session=False is set, the broker remembers subscription state between 
connections. During development, accidentally using a different Client ID created 
a new session while the old one kept queuing messages in the background. This caused 
unexpected behaviour where old messages arrived when reconnecting. The fix was simple 
— always use the same CLIENT_ID constant — but finding the problem required carefully 
reading the MQTT specification about session state management.

### Most Surprising Protocol Difference

The most surprising finding was how much overhead QoS 2 adds at the wire level. A 
single temperature reading at QoS 2 generates four TCP segments: PUBLISH, PUBREC, 
PUBREL, and PUBCOMP. For a 120-byte sensor payload, the protocol overhead was 
approximately 180 bytes — meaning the overhead was larger than the actual data. This 
makes QoS 2 unsuitable for high-frequency telemetry at scale, which is why QoS 1 is 
the better choice for sensor data where occasional duplicates are harmless.

### Most Complex Protocol to Implement

CoAP was the hardest to implement correctly for two reasons. First, the asyncio 
background task for sensor updates must be started with asyncio.ensure_future() after 
the event loop is running — getting this wrong silently created tasks that never 
executed, so observers received the initial reading but never got updates. Second, the 
Observe sequence number wrap-around at 2^24 requires modular arithmetic to detect 
stale notifications correctly. A simple greater-than comparison breaks when the counter 
wraps from 16,777,215 back to 0, making valid new readings look stale to the client.

