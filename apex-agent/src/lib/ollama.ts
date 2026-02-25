// ============================================================================
// APEX Agent — Ollama Client
// ============================================================================

import { OllamaMessage, OllamaTool } from './types';
import { AGENT_CONFIG } from '@/config/system-prompt';

interface OllamaChatRequest {
  model: string;
  messages: OllamaMessage[];
  tools?: OllamaTool[];
  stream?: boolean;
  options?: {
    temperature?: number;
    num_predict?: number;
  };
}

interface OllamaChatResponse {
  model: string;
  message: {
    role: string;
    content: string;
    tool_calls?: Array<{
      function: {
        name: string;
        arguments: Record<string, unknown>;
      };
    }>;
  };
  done: boolean;
  done_reason?: string;
}

export class OllamaClient {
  private baseUrl: string;
  private model: string;

  constructor(baseUrl?: string, model?: string) {
    this.baseUrl = baseUrl || AGENT_CONFIG.ollamaUrl;
    this.model = model || AGENT_CONFIG.model;
  }

  async chat(
    messages: OllamaMessage[],
    tools?: OllamaTool[],
    stream = false
  ): Promise<OllamaChatResponse> {
    const body: OllamaChatRequest = {
      model: this.model,
      messages,
      stream,
      options: {
        temperature: AGENT_CONFIG.temperature,
      },
    };

    if (tools && tools.length > 0) {
      body.tools = tools;
    }

    const response = await fetch(`${this.baseUrl}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Ollama API error (${response.status}): ${error}`);
    }

    const data = await response.json();
    return data as OllamaChatResponse;
  }

  async *chatStream(
    messages: OllamaMessage[],
    tools?: OllamaTool[]
  ): AsyncGenerator<OllamaChatResponse> {
    const body: OllamaChatRequest = {
      model: this.model,
      messages,
      stream: true,
      options: {
        temperature: AGENT_CONFIG.temperature,
      },
    };

    if (tools && tools.length > 0) {
      body.tools = tools;
    }

    const response = await fetch(`${this.baseUrl}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Ollama API error (${response.status}): ${error}`);
    }

    const reader = response.body?.getReader();
    if (!reader) throw new Error('No response body');

    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.trim()) {
          try {
            const data = JSON.parse(line);
            yield data as OllamaChatResponse;
          } catch {
            // Skip malformed JSON lines
          }
        }
      }
    }

    // Process remaining buffer
    if (buffer.trim()) {
      try {
        const data = JSON.parse(buffer);
        yield data as OllamaChatResponse;
      } catch {
        // Skip
      }
    }
  }

  async listModels(): Promise<string[]> {
    const response = await fetch(`${this.baseUrl}/api/tags`);
    if (!response.ok) throw new Error('Failed to list models');
    const data = await response.json();
    return data.models?.map((m: { name: string }) => m.name) || [];
  }

  async isAvailable(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/api/tags`, {
        signal: AbortSignal.timeout(3000),
      });
      return response.ok;
    } catch {
      return false;
    }
  }
}

export const ollamaClient = new OllamaClient();
