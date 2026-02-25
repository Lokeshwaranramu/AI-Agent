// ============================================================================
// APEX Agent — Core Agent Loop
// ============================================================================

import { OllamaClient } from './ollama';
import { executeToolCall } from './tool-executor';
import { getOllamaTools } from '@/config/tool-definitions';
import { SYSTEM_PROMPT, AGENT_CONFIG } from '@/config/system-prompt';
import { Message, ToolCall, ToolResult, OllamaMessage, StreamChunk } from './types';
import { v4 as uuid } from 'uuid';

export class ApexAgent {
  private ollama: OllamaClient;
  private conversationHistory: OllamaMessage[] = [];
  private maxToolCalls: number;

  constructor() {
    this.ollama = new OllamaClient();
    this.maxToolCalls = AGENT_CONFIG.maxToolCalls;
    this.conversationHistory = [
      { role: 'system', content: SYSTEM_PROMPT },
    ];
  }

  async *processMessage(userMessage: string): AsyncGenerator<StreamChunk> {
    // Add user message to history
    this.conversationHistory.push({
      role: 'user',
      content: userMessage,
    });

    const tools = getOllamaTools();
    let toolCallCount = 0;

    while (toolCallCount < this.maxToolCalls) {
      try {
        // Call Ollama with tool definitions
        const response = await this.ollama.chat(
          this.conversationHistory,
          tools,
          false
        );

        const assistantMessage = response.message;

        // Check if the model wants to call tools
        if (assistantMessage.tool_calls && assistantMessage.tool_calls.length > 0) {
          // Add assistant message with tool calls to history
          this.conversationHistory.push({
            role: 'assistant',
            content: assistantMessage.content || '',
            tool_calls: assistantMessage.tool_calls,
          });

          // If there's text content before tool calls, yield it
          if (assistantMessage.content) {
            yield { type: 'text', content: assistantMessage.content };
          }

          // Execute each tool call
          for (const tc of assistantMessage.tool_calls) {
            const toolCall: ToolCall = {
              id: uuid(),
              name: tc.function.name,
              arguments: tc.function.arguments,
            };

            // Yield tool call info
            yield { type: 'tool_call', toolCall };

            // Execute the tool
            const toolResult = await executeToolCall(toolCall);
            toolCallCount++;

            // Yield tool result
            yield { type: 'tool_result', toolResult };

            // Add tool result to conversation history
            this.conversationHistory.push({
              role: 'tool',
              content: toolResult.result,
            });
          }

          // Continue the loop to let the model process tool results
          continue;
        }

        // No tool calls — model is responding with text
        if (assistantMessage.content) {
          this.conversationHistory.push({
            role: 'assistant',
            content: assistantMessage.content,
          });
          yield { type: 'text', content: assistantMessage.content };
        }

        // Done
        yield { type: 'done' };
        return;
      } catch (error) {
        const errorMsg = error instanceof Error ? error.message : String(error);
        yield { type: 'error', error: errorMsg };
        yield { type: 'done' };
        return;
      }
    }

    // Max tool calls reached
    yield {
      type: 'text',
      content: `I've reached the maximum number of tool calls (${this.maxToolCalls}) for this request. Here's what I've accomplished so far. Let me know if you'd like me to continue.`,
    };
    yield { type: 'done' };
  }

  resetConversation() {
    this.conversationHistory = [
      { role: 'system', content: SYSTEM_PROMPT },
    ];
  }

  getHistory(): OllamaMessage[] {
    return [...this.conversationHistory];
  }
}

// Singleton agent instance
let agentInstance: ApexAgent | null = null;

export function getAgent(): ApexAgent {
  if (!agentInstance) {
    agentInstance = new ApexAgent();
  }
  return agentInstance;
}

export function resetAgent(): ApexAgent {
  agentInstance = new ApexAgent();
  return agentInstance;
}

// Helper to convert internal messages to UI format
export function toUIMessage(
  role: 'user' | 'assistant',
  content: string,
  toolCalls?: ToolCall[],
  toolResults?: ToolResult[]
): Message {
  return {
    id: uuid(),
    role,
    content,
    timestamp: Date.now(),
    toolCalls,
    toolResults,
  };
}
