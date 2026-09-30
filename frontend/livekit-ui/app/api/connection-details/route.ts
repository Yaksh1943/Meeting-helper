import { NextRequest, NextResponse } from 'next/server';

const backendUrl = process.env.BACKEND_API_URL || 'http://localhost:8000';

export async function GET(request: NextRequest) {
  try {
    const roomName = request.nextUrl.searchParams.get('roomName');
    const participantName = request.nextUrl.searchParams.get('participantName');

    if (!roomName || !participantName) {
      return new NextResponse('Missing required query parameters', { status: 400 });
    }

    const url = new URL('/connection-details', backendUrl);
    url.searchParams.set('roomName', roomName);
    url.searchParams.set('participantName', participantName);

    const res = await fetch(url, {
      headers: process.env.BACKEND_API_TOKEN
        ? { 'X-API-Key': process.env.BACKEND_API_TOKEN }
        : undefined,
    });

    if (!res.ok) {
      return new NextResponse('Failed to fetch from backend', { status: 500 });
    }

    const data = await res.json();

    return NextResponse.json(data);
  } catch (error) {
    return new NextResponse('Internal Server Error', { status: 500 });
  }
}
