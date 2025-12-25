#!/usr/bin/env tsx
import * as fs from 'fs';

import concurrently from 'concurrently';
import * as yaml from 'js-yaml';

interface ClientConfig {
  port: number;
  supportsLatencyTaskUpdates: boolean;
  ngrok?: {
    url: string;
  };
}

interface ServerConfig {
  name: string;
  port: number;
  supportsLatencyTaskUpdates?: boolean;
  supportsExtension?: boolean;
  skillLatency?: Array<{
    skill: string;
    latency: number;
  }>;
}

interface Config {
  client: ClientConfig;
  servers: ServerConfig[];
}

const CONFIG_FILE = 'config.yaml';

function getConfigFile(): string {
  // Parse command line arguments for --config flag
  const args = process.argv.slice(2);
  const configIndex = args.indexOf('--config');

  if (configIndex !== -1 && configIndex + 1 < args.length) {
    return args[configIndex + 1];
  }

  return CONFIG_FILE; // fallback to default
}

async function main() {
  const configFile = getConfigFile();

  // Check if config file exists
  if (!fs.existsSync(configFile)) {
    console.error(`Config file ${configFile} not found!`);
    process.exit(1);
  }

  try {
    // Read and parse the YAML configuration
    const configContent = fs.readFileSync(configFile, 'utf8');
    const config = yaml.load(configContent) as Config;

    if (!config.servers || config.servers.length === 0) {
      console.error('No servers configured in config.yaml');
      process.exit(1);
    }

    // Build commands for client and server
    const commands: Array<{
      command: string;
      name: string;
      prefixColor: string;
    }> = [];

    // Client command (voice.ts) - only start one instance
    let clientCmd = `tsx ./src/client/voice.ts`;

    // Set environment variables for the client
    let clientEnvVars = `PORT=${config.client.port} `;
    if (config.client.supportsLatencyTaskUpdates !== undefined) {
      clientEnvVars += `SUPPORTS_LATENCY_TASK_UPDATES=${config.client.supportsLatencyTaskUpdates} `;
    }
    if (config.client.ngrok?.url) {
      clientEnvVars += `NGROK_URL=${config.client.ngrok.url} `;
    }

    clientCmd = `${clientEnvVars}${clientCmd}`;

    commands.push({
      command: clientCmd,
      name: 'Client',
      prefixColor: 'green',
    });

    // Add commands for all servers
    const serverColorModifiers = [
      'blue',
      'blue.bold',
      'blue.dim',
      'blue.italic',
    ];
    config.servers.forEach((server, index) => {
      const serverCmd = `tsx ./src/server/index.ts`;
      // Set environment variables for the server
      let serverCmdWithEnv = `PORT=${server.port}`;
      if (server.supportsLatencyTaskUpdates !== undefined) {
        serverCmdWithEnv += ` SUPPORTS_LATENCY_TASK_UPDATES=${server.supportsLatencyTaskUpdates}`;
      }
      if (server.supportsExtension !== undefined) {
        serverCmdWithEnv += ` SUPPORTS_EXTENSION=${server.supportsExtension}`;
      }
      // Pass skillLatency configuration as JSON string
      if (server.skillLatency && server.skillLatency.length > 0) {
        const skillLatencyJson = JSON.stringify(server.skillLatency);
        serverCmdWithEnv += ` SKILL_LATENCY='${skillLatencyJson}'`;
      }
      serverCmdWithEnv += ` ${serverCmd}`;

      commands.push({
        command: serverCmdWithEnv,
        name: server.name,
        prefixColor: serverColorModifiers[index % serverColorModifiers.length],
      });
    });

    // Add ngrok command last if configured
    if (config.client.ngrok?.url) {
      // Use ngrok with explicit domain flag for better compatibility
      const ngrokCmd = `ngrok http ${config.client.port} --domain=${config.client.ngrok.url}`;
      commands.push({
        command: ngrokCmd,
        name: 'ngrok',
        prefixColor: 'yellow',
      });
      console.log(
        `🔗 Starting ngrok tunnel: ${config.client.ngrok.url} -> localhost:${config.client.port}`,
      );
    } else if (config.client.ngrok?.url) {
      console.log(
        `🔗 ngrok configured but disabled. To enable, set client.ngrok.enabled: true in config.yaml`,
      );
    }

    console.log(
      `Starting client and server${config.servers.length > 1 ? 's' : ''}...`,
    );
    console.log(`Client port: ${config.client.port}`);
    config.servers.forEach((server, index) => {
      console.log(`Server ${index + 1} (${server.name}) port: ${server.port}`);
    });
    if (config.client.ngrok?.url) {
      console.log(`ngrok URL: ${config.client.ngrok.url}`);
    }

    console.log('Starting client and server with concurrently...'); // Use concurrently API directly
    try {
      const prefixColors = [
        'green',
        'blue',
        'cyan',
        'magenta',
        'yellow',
        'red',
      ];
      const { result } = concurrently(commands, {
        prefix: 'name',
        killOthers: ['failure', 'success'],
        restartTries: 0,
        prefixColors: prefixColors.slice(0, commands.length),
      });

      // Wait for all processes to complete
      await result;
      console.log('Client and server completed successfully');
    } catch (error) {
      console.error('Error running client and server:');

      // Check if it's a concurrently error with process details
      if (Array.isArray(error) && error.length > 0) {
        error.forEach((processError, index) => {
          if (processError.command && processError.command.name) {
            console.error(
              `  ${processError.command.name} (exit code: ${processError.exitCode})`,
            );
            if (processError.command.name === 'ngrok') {
              console.error('  💡 ngrok failed - this might be due to:');
              console.error(
                "     - Authentication issues (run 'ngrok authtoken YOUR_TOKEN')",
              );
              console.error('     - Domain not available or not authorized');
              console.error('     - Network connectivity issues');
              console.error('     - Incorrect ngrok command syntax');
              console.error(
                "  💡 To disable ngrok, add 'enabled: false' to client.ngrok in config.yaml",
              );
            }
          }
        });
      } else {
        console.error(error);
      }
      process.exit(1);
    }
  } catch (error) {
    console.error('Error reading or parsing config file:', error);
    process.exit(1);
  }
}

// Handle process termination
process.on('SIGINT', () => {
  console.log('\nReceived SIGINT, shutting down gracefully...');
  process.exit(0);
});

process.on('SIGTERM', () => {
  console.log('\nReceived SIGTERM, shutting down gracefully...');
  process.exit(0);
});

main().catch((error) => {
  console.error('Unexpected error:', error);
  process.exit(1);
});
