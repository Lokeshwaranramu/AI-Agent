'use client';

import React, { useState } from 'react';
import {
  Terminal,
  Search,
  ImageIcon,
  Film,
  FolderOpen,
  Globe,
  BarChart3,
  FileText,
  Brain,
  Server,
  Loader2,
  CheckCircle2,
  XCircle,
  ChevronDown,
  ChevronUp,
  Clock,
} from 'lucide-react';

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

const TOOL_ICONS: Record<string, React.ReactNode> = {
  execute_code: <Terminal className="w-3.5 h-3.5" />,
  run_shell_command: <Terminal className="w-3.5 h-3.5" />,
  web_search: <Search className="w-3.5 h-3.5" />,
  fetch_url: <Globe className="w-3.5 h-3.5" />,
  generate_image: <ImageIcon className="w-3.5 h-3.5" />,
  create_video: <Film className="w-3.5 h-3.5" />,
  read_file: <FolderOpen className="w-3.5 h-3.5" />,
  write_file: <FolderOpen className="w-3.5 h-3.5" />,
  list_directory: <FolderOpen className="w-3.5 h-3.5" />,
  browser_action: <Globe className="w-3.5 h-3.5" />,
  analyze_data: <BarChart3 className="w-3.5 h-3.5" />,
  create_content: <FileText className="w-3.5 h-3.5" />,
  ml_inference: <Brain className="w-3.5 h-3.5" />,
  devops_action: <Server className="w-3.5 h-3.5" />,
};

const TOOL_LABELS: Record<string, string> = {
  execute_code: 'Running Code',
  run_shell_command: 'Shell Command',
  web_search: 'Searching Web',
  fetch_url: 'Fetching URL',
  generate_image: 'Generating Image',
  create_video: 'Creating Video',
  read_file: 'Reading File',
  write_file: 'Writing File',
  list_directory: 'Listing Directory',
  browser_action: 'Browser Action',
  analyze_data: 'Analyzing Data',
  create_content: 'Creating Content',
  ml_inference: 'ML Inference',
  devops_action: 'DevOps Action',
};

export function ToolOutput({
  toolCall,
  toolResult,
  isActive,
}: {
  toolCall?: ToolCallData;
  toolResult?: ToolResultData;
  isActive: boolean;
}) {
  const [expanded, setExpanded] = useState(false);

  const toolName = toolCall?.name || toolResult?.toolName || 'unknown';
  const icon = TOOL_ICONS[toolName] || <Terminal className="w-3.5 h-3.5" />;
  const label = TOOL_LABELS[toolName] || toolName;

  return (
    <div
      className={`rounded-xl border overflow-hidden text-sm transition-all duration-200 ${
        isActive
          ? 'border-cyan-500/30 bg-cyan-500/5'
          : toolResult?.success
            ? 'border-green-500/20 bg-green-500/5'
            : 'border-red-500/20 bg-red-500/5'
      }`}
    >
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-2 px-3 py-2 hover:bg-white/5 transition-colors"
      >
        <div
          className={`p-1 rounded ${
            isActive
              ? 'text-cyan-400'
              : toolResult?.success
                ? 'text-green-400'
                : 'text-red-400'
          }`}
        >
          {icon}
        </div>

        <span className="text-zinc-300 font-medium text-xs">{label}</span>

        {isActive && (
          <Loader2 className="w-3 h-3 text-cyan-400 animate-spin ml-1" />
        )}
        {toolResult && !isActive && (
          <>
            {toolResult.success ? (
              <CheckCircle2 className="w-3 h-3 text-green-400 ml-1" />
            ) : (
              <XCircle className="w-3 h-3 text-red-400 ml-1" />
            )}
          </>
        )}

        {toolResult?.duration && (
          <span className="text-zinc-500 text-xs flex items-center gap-0.5 ml-auto mr-2">
            <Clock className="w-2.5 h-2.5" />
            {toolResult.duration < 1000
              ? `${toolResult.duration}ms`
              : `${(toolResult.duration / 1000).toFixed(1)}s`}
          </span>
        )}

        {expanded ? (
          <ChevronUp className="w-3 h-3 text-zinc-500 ml-auto" />
        ) : (
          <ChevronDown className="w-3 h-3 text-zinc-500 ml-auto" />
        )}
      </button>

      {/* Expanded Content */}
      {expanded && (
        <div className="border-t border-zinc-700/50 px-3 py-2">
          {/* Tool Arguments */}
          {toolCall && (
            <div className="mb-2">
              <div className="text-xs text-zinc-500 mb-1 font-medium">Arguments:</div>
              <pre className="text-xs text-zinc-400 bg-zinc-800/50 rounded-lg p-2 overflow-x-auto font-mono">
                {JSON.stringify(toolCall.arguments, null, 2)}
              </pre>
            </div>
          )}

          {/* Tool Result */}
          {toolResult && (
            <div>
              <div className="text-xs text-zinc-500 mb-1 font-medium">Result:</div>
              <pre className="text-xs text-zinc-300 bg-zinc-800/50 rounded-lg p-2 overflow-x-auto font-mono whitespace-pre-wrap max-h-64 overflow-y-auto">
                {toolResult.result.length > 2000
                  ? toolResult.result.slice(0, 2000) + '\n\n[... truncated]'
                  : toolResult.result}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
