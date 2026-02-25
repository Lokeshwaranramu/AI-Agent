// ============================================================================
// APEX Agent — Type Definitions
// ============================================================================

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  timestamp: number;
  toolCalls?: ToolCall[];
  toolResults?: ToolResult[];
  isStreaming?: boolean;
}

export interface ToolCall {
  id: string;
  name: string;
  arguments: Record<string, unknown>;
}

export interface ToolResult {
  toolCallId: string;
  toolName: string;
  result: string;
  success: boolean;
  duration?: number;
  artifacts?: Artifact[];
}

export interface Artifact {
  type: 'image' | 'video' | 'file' | 'code' | 'chart' | 'link';
  name: string;
  path?: string;
  url?: string;
  content?: string;
  mimeType?: string;
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  createdAt: number;
  updatedAt: number;
}

export interface ToolDefinition {
  name: string;
  description: string;
  category: ToolCategory;
  parameters: {
    type: 'object';
    properties: Record<string, ToolParameter>;
    required?: string[];
  };
}

export interface ToolParameter {
  type: string;
  description: string;
  enum?: string[];
  items?: { type: string };
  default?: unknown;
}

export type ToolCategory =
  | 'code_execution'
  | 'web_search'
  | 'image_generation'
  | 'video_creation'
  | 'file_management'
  | 'browser_automation'
  | 'data_analytics'
  | 'content_creation'
  | 'ml_tools'
  | 'devops';

export interface AgentConfig {
  model: string;
  ollamaUrl: string;
  maxToolCalls: number;
  temperature: number;
  systemPrompt: string;
}

export interface StreamChunk {
  type: 'text' | 'tool_call' | 'tool_result' | 'error' | 'done';
  content?: string;
  toolCall?: ToolCall;
  toolResult?: ToolResult;
  error?: string;
}

export interface OllamaMessage {
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  tool_calls?: Array<{
    function: {
      name: string;
      arguments: Record<string, unknown>;
    };
  }>;
}

export interface OllamaTool {
  type: 'function';
  function: {
    name: string;
    description: string;
    parameters: {
      type: 'object';
      properties: Record<string, unknown>;
      required?: string[];
    };
  };
}
