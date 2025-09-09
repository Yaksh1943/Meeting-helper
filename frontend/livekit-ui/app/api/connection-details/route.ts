import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    const roomName = request.nextUrl.searchParams.get('roomName');
    const participantName = request.nextUrl.searchParams.get('participantName');

    if (!roomName || !participantName) {
      return new NextResponse('Missing required query parameters', { status: 400 });
    }

    const res = await fetch(
  `http://localhost:8000/api/connection-details?roomName=${roomName}&participantName=${participantName}`
);

    if (!res.ok) {
      return new NextResponse('Failed to fetch from backend', { status: 500 });
    }

    const data = await res.json();

    return NextResponse.json(data);
  } catch (error) {
    return new NextResponse('Internal Server Error', { status: 500 });
  }
}
