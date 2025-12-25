import { BaseChatModel } from '@langchain/core/language_models/chat_models';
import { ChatGoogleGenerativeAI } from '@langchain/google-genai';
import { ChatOpenAI } from '@langchain/openai';

import config from './config';

type ModelConfig = {
  model: string;
  temperature: number;
  streaming: boolean;
};

export const getModel = (modelConfig?: Partial<ModelConfig>): BaseChatModel => {
  if (config.keys.geminiApiKey) {
    console.info('Using Gemini');
    return new ChatGoogleGenerativeAI({
      model: 'gemini-2.5-pro',
      temperature: 0.7,
      apiKey: config.keys.geminiApiKey,
      ...modelConfig,
    });
  }

  if (config.keys.openAIApiKey) {
    console.info('Using OpenAI');
    return new ChatOpenAI({
      model: 'gpt-4o',
      temperature: 0.7,
      openAIApiKey: config.keys.openAIApiKey,
      ...modelConfig,
    });
  }

  throw new Error('No API keys configured');
};

export { BaseChatModel };
