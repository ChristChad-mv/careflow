import { tool } from '@langchain/core/tools';
import { z } from 'zod';

import { config } from '../utils';
import { callTmdbApi } from './tmdb.js';

// Helper function to create synthetic delay promise
function createSyntheticDelay(toolName: string): Promise<void> {
  const latency = config.skillLatencies[toolName];
  if (latency && latency > 0) {
    console.log(
      `[Tools] Setting ${latency}ms minimum execution time for ${toolName}`,
    );
    return new Promise((resolve) => setTimeout(resolve, latency));
  }
  return Promise.resolve();
}

// Helper function to execute with minimum latency
async function executeWithMinimumLatency<T>(
  toolName: string,
  operation: () => Promise<T>,
): Promise<T> {
  const startTime = Date.now();
  const delayPromise = createSyntheticDelay(toolName);

  try {
    // Run the operation and delay in parallel
    const [result] = await Promise.all([operation(), delayPromise]);

    const actualDuration = Date.now() - startTime;
    const configuredLatency = config.skillLatencies[toolName] || 0;

    if (configuredLatency > 0) {
      console.log(
        `[Tools] ${toolName} completed in ${actualDuration}ms (minimum: ${configuredLatency}ms)`,
      );
    }

    console.log(result);

    return result;
  } catch (error) {
    // Still wait for the minimum delay even if the operation fails
    await delayPromise;
    throw error;
  }
}

export const searchMovies = tool(
  async ({ query }) => {
    console.log('[tmdb:searchMovies]', JSON.stringify(query));

    return executeWithMinimumLatency('searchMovies', async () => {
      const data = (await callTmdbApi('movie', query)) as any;

      // Only modify image paths to be full URLs
      const results = data.results.map((movie: any) => {
        if (movie.poster_path) {
          movie.poster_path = `https://image.tmdb.org/t/p/w500${movie.poster_path}`;
        }
        if (movie.backdrop_path) {
          movie.backdrop_path = `https://image.tmdb.org/t/p/w500${movie.backdrop_path}`;
        }
        return movie;
      });

      return JSON.stringify({
        ...data,
        results,
      });
    });
  },
  {
    name: 'searchMovies',
    description: 'search TMDB for movies by title',
    schema: z.object({
      query: z.string().describe('The movie title to search for'),
    }),
  },
);

export const searchPeople = tool(
  async ({ query }) => {
    console.log('[tmdb:searchPeople]', JSON.stringify(query));

    return executeWithMinimumLatency('searchPeople', async () => {
      const data = (await callTmdbApi('person', query)) as any;

      // Only modify image paths to be full URLs
      const results = data.results.map((person: any) => {
        if (person.profile_path) {
          person.profile_path = `https://image.tmdb.org/t/p/w500${person.profile_path}`;
        }

        // Also modify poster paths in known_for works
        if (person.known_for && Array.isArray(person.known_for)) {
          person.known_for = person.known_for.map((work: any) => {
            if (work.poster_path) {
              work.poster_path = `https://image.tmdb.org/t/p/w500${work.poster_path}`;
            }
            if (work.backdrop_path) {
              work.backdrop_path = `https://image.tmdb.org/t/p/w500${work.backdrop_path}`;
            }
            return work;
          });
        }

        return person;
      });

      return JSON.stringify({
        ...data,
        results,
      });
    });
  },
  {
    name: 'searchPeople',
    description: 'search TMDB for people by name',
    schema: z.object({
      query: z.string().describe("The person's name to search for"),
    }),
  },
);
