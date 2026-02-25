'use client';

import React, { useEffect, useState } from 'react';
import {
  Zap,
  Plus,
  CircleDot,
  Wifi,
  WifiOff,
} from 'lucide-react';

interface StatusData {
  status: string;
  ollama: {
    url: string;
    available: boolean;
    models: string[];
    activeModel: string;
  };
  agent: {
    version: string;
    name: string;
    maxToolCalls: number;
  };
}

interface SidebarProps {
  onNewChat: () => void;
}

export function Sidebar({ onNewChat }: SidebarProps) {
  const [status, setStatus] = useState<StatusData | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function checkStatus() {
      try {
        const res = await fetch('/api/status');
        const data = await res.json();
        setStatus(data);
      } catch {
        setStatus(null);
      } finally {
        setIsLoading(false);
      }
    }

    checkStatus();
    const interval = setInterval(checkStatus, 30000); // Check every 30s
    return () => clearInterval(interval);
  }, []);

  const isConnected = status?.ollama?.available ?? false;

  return (
    <div className="w-72 bg-zinc-900 border-r border-zinc-800 flex flex-col h-full">
      {/* Logo */}
      <div className="p-4 border-b border-zinc-800">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <Zap className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white tracking-tight">APEX</h1>
            <p className="text-xs text-zinc-500">v{status?.agent?.version || '1.0.0'}</p>
          </div>
        </div>
      </div>

      {/* New Chat Button */}
      <div className="p-3">
        <button
          onClick={onNewChat}
          className="w-full flex items-center gap-2 px-4 py-2.5 rounded-xl bg-zinc-800 border border-zinc-700 text-zinc-300 hover:bg-zinc-700 hover:border-cyan-500/30 hover:text-white transition-all duration-200"
        >
          <Plus className="w-4 h-4" />
          <span className="text-sm font-medium">New Chat</span>
        </button>
      </div>

      {/* Status & Info */}
      <div className="flex-1 overflow-y-auto px-3">
        {/* Capabilities */}
        <div className="mt-4">
          <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider px-2 mb-2">
            Capabilities
          </h3>
          <div className="space-y-0.5">
            {[
              'Code Execution',
              'Web Search',
              'Image Generation',
              'Video Creation',
              'File Management',
              'Browser Automation',
              'Data Analytics',
              'Content Creation',
              'ML Inference',
              'DevOps',
            ].map((cap) => (
              <div
                key={cap}
                className="flex items-center gap-2 px-2 py-1.5 text-zinc-400 text-xs"
              >
                <CircleDot className="w-2.5 h-2.5 text-cyan-500" />
                {cap}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Connection Status */}
      <div className="p-3 border-t border-zinc-800">
        <div
          className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs ${
            isLoading
              ? 'bg-zinc-800 text-zinc-400'
              : isConnected
                ? 'bg-green-500/10 text-green-400 border border-green-500/20'
                : 'bg-red-500/10 text-red-400 border border-red-500/20'
          }`}
        >
          {isLoading ? (
            <>
              <div className="w-2 h-2 rounded-full bg-zinc-500 animate-pulse" />
              Checking Ollama...
            </>
          ) : isConnected ? (
            <>
              <Wifi className="w-3 h-3" />
              <div>
                <div className="font-medium">Ollama Connected</div>
                <div className="text-green-500/70 text-[10px]">
                  {status?.ollama?.activeModel || 'default model'}
                </div>
              </div>
            </>
          ) : (
            <>
              <WifiOff className="w-3 h-3" />
              <div>
                <div className="font-medium">Ollama Offline</div>
                <div className="text-red-500/70 text-[10px]">
                  Run: ollama serve
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
