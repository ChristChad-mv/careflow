# Agent-to-Agent (A2A) Latency Extension Sample

This is a sample implementation of Twilio's Agent-to-Agent framework with latency extension support. It demonstrates a voice-enabled delegator agent that can route requests to multiple movie information agents running on different ports with configurable latency settings.

## Architecture

- **Client**: Voice interface (`src/client/voice.ts`) that handles Twilio voice calls
- **Delegator Agent**: Main agent (`src/client/agent.ts`) that receives voice input and delegates to appropriate remote agents
- **Movie Info Servers**: Multiple server instances (`src/server/`) that provide movie information using TMDB API
- **Configuration**: YAML-based configuration for managing multiple agents with different latency characteristics

## Setup

1. Get API keys:
   - TMDB API key: https://developer.themoviedb.org/docs/getting-started
   - Gemini API key: https://aistudio.google.com/app/apikey

2. Set environment variables:

**Option 1: Using .env file (recommended)**
```bash
# Copy the example file and edit it with your API keys
cp .env.example .env
# Then edit .env with your actual API keys
```

**Option 2: Export environment variables**
```bash
export TMDB_API_KEY=<your_tmdb_api_key>
export GEMINI_API_KEY=<your_gemini_api_key>
```

3. Configure agents in `config.yaml`:
   - Set client port and ngrok settings
   - Configure multiple server instances with different latency profiles
   - Adjust skill latencies for testing different performance scenarios

4. Run the system:
```bash
npm start
```

This will start:
- Voice client on the configured port (default: 3004)
- Multiple movie info servers on different ports (default: 41241, 41242, 41243)
- ngrok tunnel (if configured) for external access

## Features

### Voice Interface
- Twilio voice integration for phone-based interactions
- Real-time voice conversation with delegator agent
- WebSocket-based communication for low latency

### Agent Delegation
- Smart routing of requests to appropriate remote agents
- Discovery of available remote agents via `list_remote_agents`
- Message passing to remote agents via `send_message`
- Support for multiple agents with different capabilities

### Movie Information Services
- Search for movies and TV shows using TMDB API
- Get information about actors and directors
- Parallel tool execution for efficient data retrieval
- Full image URL generation for movie posters and backdrops

### Latency Testing
- Configurable latency per skill/tool
- Multiple server instances with different performance profiles
- Support for latency task updates
- Extension support for advanced features

### Technologies Used
- **Gemini 2.5 Pro**: Natural language understanding and generation
- **Langchain/Langgraph**: Agent orchestration and tool management
- **Twilio**: Voice interface and telephony
- **TMDB API**: Movie and entertainment data
- **Express**: Web server framework
- **WebSocket**: Real-time communication
- **TypeScript**: Type-safe development

## Configuration

The `config.yaml` file allows you to configure:

- **Client settings**: Port, latency support, ngrok tunnel
- **Server instances**: Multiple agents with different latency profiles
- **Skill latencies**: Per-tool latency simulation for testing
- **Extension support**: Advanced features and capabilities

## File Structure

```
src/
├── client/
│   ├── agent/            # Delegator agent logic
│   ├── voice.ts          # Twilio voice interface
│   └── public/           # Static assets
├── server/
│   ├── index.ts          # Server entry point
│   ├── agent.ts          # Movie info agent
│   ├── llm.ts           # OpenAI model configuration
│   ├── tools.ts         # TMDB search tools
│   └── tmdb.ts          # TMDB API integration
└── types/
    ├── index.ts         # Type definitions
    └── conversationRelay.ts  # A2A conversation types
```
