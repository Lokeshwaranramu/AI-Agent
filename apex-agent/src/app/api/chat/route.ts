// ============================================================================
// APEX Agent — Chat API Route (Server-Sent Events)
// ============================================================================

import { NextRequest } from 'next/server';
import { getAgent, resetAgent } from '@/lib/agent';
import { StreamChunk } from '@/lib/types';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { message, reset } = body;

    if (reset) {
      resetAgent();
      return Response.json({ success: true, message: 'Conversation reset' });
    }

    if (!message || typeof message !== 'string') {
      return Response.json(
        { error: 'Message is required' },
        { status: 400 }
      );
    }

    const agent = getAgent();

    // Create a ReadableStream for SSE
    const stream = new ReadableStream({
      async start(controller) {
        const encoder = new TextEncoder();

        function sendEvent(data: StreamChunk) {
          controller.enqueue(
            encoder.encode(`data: ${JSON.stringify(data)}\n\n`)
          );
        }

        try {
          for await (const chunk of agent.processMessage(message)) {
            sendEvent(chunk);
          }
        } catch (error) {
          sendEvent({
            type: 'error',
            error: error instanceof Error ? error.message : 'Unknown error',
          });
          sendEvent({ type: 'done' });
        } finally {
          controller.close();
        }
      },
    });

    return new Response(stream, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        Connection: 'keep-alive',
      },
    });
  } catch (error) {
    return Response.json(
      { error: error instanceof Error ? error.message : 'Internal server error' },
      { status: 500 }
    );
  }
}

export async function GET() {
  return Response.json({
    status: 'APEX Agent API is running',
    version: '1.0.0',
    endpoints: {
      POST: 'Send a message to APEX',
      GET: 'Health check',
    },
  });
}
