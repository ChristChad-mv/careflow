import { AgentExtension } from '@a2a-js/sdk';

export interface AgentLatencyExtension extends AgentExtension {
  params: {
    supportsLatencyTaskUpdates?: boolean;
    skillLatency?:
      | {
          min?: number;
          max?: number;
        }
      | {
          p50?: number;
          p75?: number;
          p90?: number;
          p95?: number;
          p99?: number;
          p999?: number;
        }
      | {
          [key: string]: number;
        };
  };
}
