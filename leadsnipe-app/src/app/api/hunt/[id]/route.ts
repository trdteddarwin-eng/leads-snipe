import { NextRequest, NextResponse } from 'next/server';
import { getHunt, deleteHunt } from '@/lib/store';

interface RouteContext {
  params: Promise<{ id: string }>;
}

export async function GET(request: NextRequest, context: RouteContext) {
  try {
    const { id: huntId } = await context.params;
    const hunt = getHunt(huntId);

    if (!hunt) {
      return NextResponse.json(
        { error: 'Hunt not found' },
        { status: 404 }
      );
    }

    return NextResponse.json(hunt);
  } catch (error) {
    console.error('Failed to fetch hunt:', error);
    return NextResponse.json(
      { error: 'Failed to fetch hunt' },
      { status: 500 }
    );
  }
}

export async function DELETE(request: NextRequest, context: RouteContext) {
  try {
    const { id: huntId } = await context.params;
    const deleted = deleteHunt(huntId);

    if (!deleted) {
      return NextResponse.json(
        { error: 'Hunt not found' },
        { status: 404 }
      );
    }

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Failed to delete hunt:', error);
    return NextResponse.json(
      { error: 'Failed to delete hunt' },
      { status: 500 }
    );
  }
}
