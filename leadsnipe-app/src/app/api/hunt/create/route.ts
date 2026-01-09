import { NextRequest, NextResponse } from 'next/server';
import { createHunt } from '@/lib/store';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { industry, location, target, category } = body;

    // Validate required fields
    if (!industry || !location || !target) {
      return NextResponse.json(
        { error: 'Missing required fields: industry, location, target' },
        { status: 400 }
      );
    }

    // Create the hunt
    const hunt = createHunt({
      industry,
      location,
      target: parseInt(target),
      category: category || 'ceo',
    });

    return NextResponse.json({
      hunt_id: hunt.hunt_id,
      status: hunt.status,
      created_at: hunt.created_at,
    });
  } catch (error) {
    console.error('Failed to create hunt:', error);
    return NextResponse.json(
      { error: 'Failed to create hunt' },
      { status: 500 }
    );
  }
}
