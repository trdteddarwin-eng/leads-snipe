import { NextRequest } from 'next/server';
import { getHunt, getHuntProgress, getHuntEvents } from '@/lib/store';

interface RouteContext {
  params: Promise<{ id: string }>;
}

export async function GET(request: NextRequest, context: RouteContext) {
  const { id: huntId } = await context.params;

  const encoder = new TextEncoder();

  const stream = new ReadableStream({
    async start(controller) {
      let lastEventCount = 0;
      let lastProgress = 0;
      let checkCount = 0;
      const maxChecks = 600; // 5 minutes max

      const sendEvent = (data: object) => {
        controller.enqueue(encoder.encode(`data: ${JSON.stringify(data)}\n\n`));
      };

      const checkProgress = async () => {
        try {
          const hunt = getHunt(huntId);
          const progress = getHuntProgress(huntId);
          const events = getHuntEvents(huntId);

          if (!hunt) {
            sendEvent({ type: 'error', error: 'Hunt not found' });
            controller.close();
            return;
          }

          // Send progress update if changed
          if (progress && progress.percentage !== lastProgress) {
            lastProgress = progress.percentage;
            sendEvent({ type: 'progress', progress });
          }

          // Send new events
          if (events.length > lastEventCount) {
            const newEvents = events.slice(lastEventCount);
            newEvents.forEach(event => {
              sendEvent({
                type: 'event',
                event_type: event.type,
                message: event.message,
                timestamp: event.timestamp,
              });
            });
            lastEventCount = events.length;
          }

          // Check completion
          if (hunt.status === 'completed') {
            sendEvent({ type: 'completed', stats: hunt.stats });
            controller.close();
            return;
          }

          if (hunt.status === 'failed') {
            sendEvent({ type: 'failed', error: 'Hunt failed' });
            controller.close();
            return;
          }

          // Continue checking
          checkCount++;
          if (checkCount < maxChecks) {
            setTimeout(checkProgress, 500);
          } else {
            sendEvent({ type: 'timeout', error: 'Timeout waiting for hunt completion' });
            controller.close();
          }
        } catch (error) {
          console.error('SSE error:', error);
          sendEvent({ type: 'error', error: 'Internal server error' });
          controller.close();
        }
      };

      // Start checking
      checkProgress();
    },
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
    },
  });
}
