# A2A Latency Extension

An extension of the Google Agent2Agent protocol, facilitating awareness of the expected latency of a given A2A server agent to provide the upstream A2A client agent the ability to provide an ideal customer experience for real-time voice experiences.

This extension provides two methods by which a server can inform an upstream client about the expected latency:

* **Data-only**: using `params` in the AgentExtension to provide latency met*rics in the public AgentCard
* **Profile**: using `TaskStatusUpdateEvent` events to send real-time updates about the current status of the Task processing

## Data extension

The `params` field in the AgentExtension object should, if possible, publish the expected latency that the client will experience before receiving a response from the server.

```javascript
{
  capabilities: {
    ...
    extensions: [
      {
        uri: "https://github.com/twilio-labs/a2a-latency-extension",
        description: "",
        required: true,
        params: {
          supportsTaskLatencyUpdates: true,
          skillLatency:
            minLatency: ...,
            maxLatency: ...
            // --or--
            p50Latency: ...,
            p75Latency: ...,
            p90Latency: ...,
            p95Latency: ...,
            p99Latency: ...
            // --or--
            skillName: {
                ...
            }
        }
      }
    ]
  }
}
```

This published metric allows potential clients to reference a server's latency to determine if or how to integrate as a dependency of their agent.

Whether the latency is low or high, the upstream client can design the handling of that latency to provide the ideal experience for their real-time voice application.

If the latency is low enough, the client can rely on a simple synchronous request (tool call, etc.) and expect to receive a final response fast enough to not interrupt the user experience.

If the listed latency is too high, the client's request to the server might be designed to be asynchronous, continuing the conversation with the user while waiting for a response from the server a while later.

### Static or dynamic

Whenever possible, we propose that the server provide a measured latency metric in its AgentExtension usage. This will increase the reputation of an A2A server by exposing a metric reflective of the experience. An up-to-date metric will also allow clients to decide to rely on a fallback A2A server if there are notably higher latencies.

In the absense of a live latency metric, servers can publish a reasonable average latency. Keep in mind, an inaccurate static number will reflect poorly on the server's reputation, and will mislead clients into designing experiences that might not meet the needs of their customers.

## Profile extension

Using the `supportsTaskLatencyUpdates` field,

If `required: true` is specified in the AgentExtension object, then the client will need to listen for the streaming `TaskStatusUpdateEvent` events to handle the DataPart message containing the server's expected latency.

```typescript
const toolUpdateEvent: TaskStatusUpdateEvent = {
  kind: "status-update",
  taskId: taskId,
  contextId: contextId,
  status: {
    state: "working",
    message: {
      kind: "message",
      role: "agent",
      messageId: uuidv4(),
      parts: [
        {
          kind: "data",
          data: {
            latency: 3275, // in milliseconds
          },
        },
      ],
      taskId: taskId,
      contextId: contextId,
      metadata: {
        toolName: update.toolName,
      },
    },
    timestamp: new Date().toISOString(),
  },
  final: false,
};
```
