import dotenv from 'dotenv';

dotenv.config();

if (!process.env.TMDB_API_KEY) {
  console.error('TMDB_API_KEY environment variables is required');
  process.exit(1);
}
if (!process.env.OPENAI_API_KEY && !process.env.GEMINI_API_KEY) {
  console.error(
    'OPENAI_API_KEY or GEMINI_API_KEY environment variables is required',
  );
  process.exit(1);
}

const DEFAULT_LATENCY_BY_TOOL: { [key: string]: number } = {
  searchMovies: 2000,
  searchPeople: 3500,
};

const config = {
  keys: {
    openAIApiKey: process.env.OPENAI_API_KEY,
    geminiApiKey: process.env.GEMINI_API_KEY,
    tmdbApiKey: process.env.TMDB_API_KEY!,
  },
  supportsExtensions: process.env.SUPPORTS_EXTENSION === 'true',
  supportsLatencyTaskUpdates:
    process.env.SUPPORTS_LATENCY_TASK_UPDATES === 'true',
  skillLatencies: DEFAULT_LATENCY_BY_TOOL,
  port: process.env.PORT || 41241,
  ngrokUrl: process.env.NGROK_URL,
};

// Override default skill latencies with configured values
if (process.env.SKILL_LATENCY) {
  try {
    const skillLatencyArray = JSON.parse(process.env.SKILL_LATENCY) as Array<{
      skill: string;
      latency: number;
    }>;
    const configuredLatency = skillLatencyArray.reduce(
      (acc, item) => {
        acc[item.skill] = item.latency;
        return acc;
      },
      {} as { [key: string]: number },
    );

    // Merge with defaults, giving priority to configured values
    config.skillLatencies = {
      ...DEFAULT_LATENCY_BY_TOOL,
      ...configuredLatency,
    };
    console.log(
      '[MovieAgent] Loaded skill latency configuration for task updates:',
      config.skillLatencies,
    );
  } catch (error) {
    console.warn(
      '[MovieAgent] Failed to parse SKILL_LATENCY environment variable:',
      error,
    );
  }
}

export default config;
