// ============================================================================
// APEX Agent — Status API Route
// ============================================================================

import { OllamaClient } from '@/lib/ollama';
import { AGENT_CONFIG } from '@/config/system-prompt';

export const runtime = 'nodejs';

export async function GET() {
  const ollama = new OllamaClient();
  
  try {
    const isAvailable = await ollama.isAvailable();
    let models: string[] = [];
    
    if (isAvailable) {
      try {
        models = await ollama.listModels();
      } catch {
        // ignore
      }
    }

    return Response.json({
      status: isAvailable ? 'connected' : 'disconnected',
      ollama: {
        url: AGENT_CONFIG.ollamaUrl,
        available: isAvailable,
        models,
        activeModel: AGENT_CONFIG.model,
      },
      agent: {
        version: '1.0.0',
        name: 'APEX',
        maxToolCalls: AGENT_CONFIG.maxToolCalls,
      },
    });
  } catch (error) {
    return Response.json({
      status: 'error',
      error: error instanceof Error ? error.message : 'Unknown error',
    });
  }
}
