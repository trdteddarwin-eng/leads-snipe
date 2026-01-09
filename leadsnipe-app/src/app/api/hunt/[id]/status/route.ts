import { NextRequest, NextResponse } from 'next/server';
import { getHunt, getHuntProgress } from '@/lib/store';

interface RouteContext {
  params: Promise<{ id: string }>;
}

export async function GET(request: NextRequest, context: RouteContext) {
  try {
    const { id: huntId } = await context.params;
    const hunt = getHunt(huntId);
    const progress = getHuntProgress(huntId);

    if (!hunt) {
      return NextResponse.json(
        { error: 'Hunt not found' },
        { status: 404 }
      );
    }

    return NextResponse.json({
      hunt_id: hunt.hunt_id,
      industry: hunt.industry,
      location: hunt.location,
      target: hunt.target,
      status: hunt.status,
      created_at: hunt.created_at,
      completed_at: hunt.completed_at,
      progress,
      stats: hunt.stats,
    });
  } catch (error) {
    console.error('Failed to fetch hunt status:', error);
    return NextResponse.json(
      { error: 'Failed to fetch hunt status' },
      { status: 500 }
    );
  }
}
