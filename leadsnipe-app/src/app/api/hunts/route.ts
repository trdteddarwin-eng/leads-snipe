import { NextResponse } from 'next/server';
import { getAllHunts } from '@/lib/store';

export async function GET() {
  try {
    const hunts = getAllHunts();
    return NextResponse.json({ hunts });
  } catch (error) {
    console.error('Failed to fetch hunts:', error);
    return NextResponse.json(
      { error: 'Failed to fetch hunts' },
      { status: 500 }
    );
  }
}
