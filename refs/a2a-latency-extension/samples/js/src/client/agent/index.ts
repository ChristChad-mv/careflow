import fs from 'fs';
import path from 'path';

import yaml from 'js-yaml';

import Agent from './agent';

// Function to read config from YAML file
function readConfig() {
  try {
    const configPath = path.join(process.cwd(), 'config.yaml');
    const fileContents = fs.readFileSync(configPath, 'utf8');
    return yaml.load(fileContents) as any;
  } catch (error) {
    console.error('Error reading config.yaml:', error);
    throw error;
  }
}

// Read configuration
const yamlConfig = readConfig();

const agent = new Agent({
  systemMessage: yamlConfig.client.system,
  a2aServers: yamlConfig.servers.map((s: any) => `http://localhost:${s.port}`),
});

agent.init();

export { agent };
