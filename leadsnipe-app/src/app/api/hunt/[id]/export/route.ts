import { NextRequest, NextResponse } from 'next/server';
import { getHunt } from '@/lib/store';

interface RouteContext {
  params: Promise<{ id: string }>;
}

export async function GET(request: NextRequest, context: RouteContext) {
  try {
    const { id: huntId } = await context.params;
    const searchParams = request.nextUrl.searchParams;
    const format = searchParams.get('format') || 'json';

    const hunt = getHunt(huntId);

    if (!hunt) {
      return NextResponse.json(
        { error: 'Hunt not found' },
        { status: 404 }
      );
    }

    if (!hunt.leads || hunt.leads.length === 0) {
      return NextResponse.json(
        { error: 'No leads to export' },
        { status: 400 }
      );
    }

    if (format === 'csv') {
      // Generate CSV
      const headers = [
        'name',
        'address',
        'phone',
        'website',
        'business_email',
        'rating',
        'reviews',
        'decision_maker_name',
        'decision_maker_title',
        'decision_maker_email',
        'linkedin_url',
      ];

      const rows = hunt.leads.map(lead => [
        lead.name,
        lead.address,
        lead.phone,
        lead.website,
        lead.email,
        lead.rating,
        lead.user_ratings_total,
        lead.decision_maker?.full_name || '',
        lead.decision_maker?.job_title || '',
        lead.decision_maker?.email || '',
        lead.decision_maker?.linkedin_url || '',
      ]);

      const csvContent = [
        headers.join(','),
        ...rows.map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(',')),
      ].join('\n');

      return new Response(csvContent, {
        headers: {
          'Content-Type': 'text/csv',
          'Content-Disposition': `attachment; filename="leadsnipe_${huntId}.csv"`,
        },
      });
    } else {
      // Return JSON
      const exportData = {
        hunt_id: hunt.hunt_id,
        industry: hunt.industry,
        location: hunt.location,
        created_at: hunt.created_at,
        completed_at: hunt.completed_at,
        stats: hunt.stats,
        leads: hunt.leads,
      };

      return new Response(JSON.stringify(exportData, null, 2), {
        headers: {
          'Content-Type': 'application/json',
          'Content-Disposition': `attachment; filename="leadsnipe_${huntId}.json"`,
        },
      });
    }
  } catch (error) {
    console.error('Failed to export hunt:', error);
    return NextResponse.json(
      { error: 'Failed to export hunt' },
      { status: 500 }
    );
  }
}
