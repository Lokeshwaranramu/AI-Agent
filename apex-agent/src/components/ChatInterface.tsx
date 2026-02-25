'use client';

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Send, RotateCcw, Zap, Loader2 } from 'lucide-react';
import { MessageBubble } from './MessageBubble';
import { ToolOutput } from './ToolOutput';
import { useVoiceInput, useTextToSpeech, VoiceButton, TtsToggle } from './VoiceInput';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
  toolCalls?: ToolCallData[];
  toolResults?: ToolResultData[];
  isStreaming?: boolean;
}

interface ToolCallData {
  id: string;
  name: string;
  arguments: Record<string, unknown>;
}

interface ToolResultData {
  toolCallId: string;
  toolName: string;
  result: string;
  success: boolean;
  duration?: number;
}

interface StreamChunk {
  type: 'text' | 'tool_call' | 'tool_result' | 'error' | 'done';
  content?: string;
  toolCall?: ToolCallData;
  toolResult?: ToolResultData;
  error?: string;
}

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [activeToolCalls, setActiveToolCalls] = useState<ToolCallData[]>([]);
  const [toolResults, setToolResults] = useState<ToolResultData[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Voice hooks
  const voice = useVoiceInput();
  const tts = useTextToSpeech();

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, activeToolCalls, toolResults, scrollToBottom]);

  // Sync voice transcript to input
  const { transcript, resetTranscript } = voice;
  useEffect(() => {
    if (transcript) {
      setInput((prev) => prev + transcript);
      resetTranscript();
    }
  }, [transcript, resetTranscript]);

  const handleSubmit = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: input.trim(),
      timestamp: Date.now(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setActiveToolCalls([]);
    setToolResults([]);

    let assistantContent = '';
    const collectedToolCalls: ToolCallData[] = [];
    const collectedToolResults: ToolResultData[] = [];

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage.content }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error('No response body');

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const chunk: StreamChunk = JSON.parse(line.slice(6));

              switch (chunk.type) {
                case 'text':
                  assistantContent += chunk.content || '';
                  // Update or create assistant message
                  setMessages((prev) => {
                    const lastMsg = prev[prev.length - 1];
                    if (lastMsg?.role === 'assistant' && lastMsg.isStreaming) {
                      return [
                        ...prev.slice(0, -1),
                        { ...lastMsg, content: assistantContent },
                      ];
                    }
                    return [
                      ...prev,
                      {
                        id: crypto.randomUUID(),
                        role: 'assistant',
                        content: assistantContent,
                        timestamp: Date.now(),
                        isStreaming: true,
                      },
                    ];
                  });
                  break;

                case 'tool_call':
                  if (chunk.toolCall) {
                    collectedToolCalls.push(chunk.toolCall);
                    setActiveToolCalls([...collectedToolCalls]);
                  }
                  break;

                case 'tool_result':
                  if (chunk.toolResult) {
                    collectedToolResults.push(chunk.toolResult);
                    setToolResults([...collectedToolResults]);
                    // Remove from active
                    setActiveToolCalls((prev) =>
                      prev.filter((tc) => tc.id !== chunk.toolResult?.toolCallId)
                    );
                  }
                  break;

                case 'error':
                  assistantContent += `\n\n⚠️ Error: ${chunk.error}`;
                  setMessages((prev) => {
                    const lastMsg = prev[prev.length - 1];
                    if (lastMsg?.role === 'assistant') {
                      return [
                        ...prev.slice(0, -1),
                        { ...lastMsg, content: assistantContent },
                      ];
                    }
                    return [
                      ...prev,
                      {
                        id: crypto.randomUUID(),
                        role: 'assistant',
                        content: assistantContent,
                        timestamp: Date.now(),
                      },
                    ];
                  });
                  break;

                case 'done':
                  // Finalize the assistant message
                  setMessages((prev) => {
                    const lastMsg = prev[prev.length - 1];
                    if (lastMsg?.role === 'assistant') {
                      return [
                        ...prev.slice(0, -1),
                        {
                          ...lastMsg,
                          content: assistantContent,
                          isStreaming: false,
                          toolCalls: collectedToolCalls.length > 0 ? collectedToolCalls : undefined,
                          toolResults: collectedToolResults.length > 0 ? collectedToolResults : undefined,
                        },
                      ];
                    }
                    return prev;
                  });
                  // Speak the final response if TTS is enabled
                  if (assistantContent) {
                    tts.speak(assistantContent);
                  }
                  break;
              }
            } catch {
              // Skip malformed SSE data
            }
          }
        }
      }
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Unknown error';
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: `⚠️ Connection error: ${errorMsg}\n\nMake sure Ollama is running (\`ollama serve\`) and the model is available.`,
          timestamp: Date.now(),
        },
      ]);
    } finally {
      setIsLoading(false);
      setActiveToolCalls([]);
      inputRef.current?.focus();
    }
  };

  const handleReset = async () => {
    await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reset: true }),
    });
    setMessages([]);
    setActiveToolCalls([]);
    setToolResults([]);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center mb-6 shadow-lg shadow-cyan-500/20">
              <Zap className="w-10 h-10 text-white" />
            </div>
            <h2 className="text-2xl font-bold text-white mb-2">APEX Agent</h2>
            <p className="text-zinc-400 max-w-md mb-8">
              Autonomous Personal EXecutive Agent. I execute code, search the web,
              generate images, create videos, manage files, and more — all locally
              via Ollama.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg w-full">
              {[
                'Write a Python script to analyze CSV data',
                'Search the web for latest AI news',
                'Generate an image of a cyberpunk city',
                'Create a README for my project',
              ].map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => {
                    setInput(suggestion);
                    inputRef.current?.focus();
                  }}
                  className="text-left p-3 rounded-xl bg-zinc-800/50 border border-zinc-700/50 text-zinc-300 text-sm hover:bg-zinc-700/50 hover:border-cyan-500/30 transition-all duration-200"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {/* Active Tool Calls */}
        {activeToolCalls.length > 0 && (
          <div className="space-y-2">
            {activeToolCalls.map((tc) => (
              <ToolOutput key={tc.id} toolCall={tc} isActive={true} />
            ))}
          </div>
        )}

        {/* Tool Results */}
        {toolResults.length > 0 && !messages[messages.length - 1]?.toolResults && (
          <div className="space-y-2">
            {toolResults.map((tr) => (
              <ToolOutput key={tr.toolCallId} toolResult={tr} isActive={false} />
            ))}
          </div>
        )}

        {/* Loading indicator */}
        {isLoading && activeToolCalls.length === 0 && !messages.find(m => m.isStreaming) && (
          <div className="flex items-center gap-2 text-zinc-400 pl-4">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span className="text-sm">APEX is thinking...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-zinc-800 bg-zinc-900/80 backdrop-blur-sm p-4">
        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
          <div className="relative flex items-end gap-2">
            <div className="flex-1 relative">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask APEX anything..."
                rows={1}
                className="w-full resize-none rounded-xl bg-zinc-800 border border-zinc-700 text-white placeholder-zinc-500 px-4 py-3 pr-12 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/20 transition-all duration-200 min-h-[48px] max-h-[200px]"
                style={{
                  height: 'auto',
                  minHeight: '48px',
                }}
                onInput={(e) => {
                  const target = e.target as HTMLTextAreaElement;
                  target.style.height = 'auto';
                  target.style.height = Math.min(target.scrollHeight, 200) + 'px';
                }}
                disabled={isLoading}
              />
            </div>

            <VoiceButton
              isListening={voice.isListening}
              isSupported={voice.isSupported}
              onClick={voice.toggleListening}
              disabled={isLoading}
            />

            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="h-12 w-12 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 text-white flex items-center justify-center hover:from-cyan-400 hover:to-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg shadow-cyan-500/20"
            >
              {isLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>

            <button
              type="button"
              onClick={handleReset}
              className="h-12 w-12 rounded-xl bg-zinc-800 border border-zinc-700 text-zinc-400 flex items-center justify-center hover:bg-zinc-700 hover:text-white transition-all duration-200"
              title="Reset conversation"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
          </div>

          <div className="flex items-center justify-between mt-2">
            <TtsToggle
              ttsEnabled={tts.ttsEnabled}
              isSpeaking={tts.isSpeaking}
              isSupported={tts.isSupported}
              onClick={tts.toggleTts}
            />
            <p className="text-xs text-zinc-500 text-center">
              {voice.isListening ? (
                <span className="text-red-400">🎙️ Listening... speak now</span>
              ) : voice.error ? (
                <span className="text-red-400">{voice.error}</span>
              ) : voice.interimTranscript ? (
                <span className="text-cyan-400 italic">{voice.interimTranscript}</span>
              ) : (
                'Press Enter to send, Shift+Enter for new line.'
              )}
            </p>
            <div className="w-20" />
          </div>
        </form>
      </div>
    </div>
  );
}
