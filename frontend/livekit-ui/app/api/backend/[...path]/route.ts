import { NextRequest, NextResponse } from 'next/server';

const backendUrl = process.env.BACKEND_API_URL || 'http://localhost:8000';

async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  const url = new URL(`/${path.map(encodeURIComponent).join('/')}`, backendUrl);
  url.search = request.nextUrl.search;

  const headers = new Headers();
  const contentType = request.headers.get('content-type');
  if (contentType) {
    headers.set('content-type', contentType);
  }
  if (process.env.BACKEND_API_TOKEN) {
    headers.set('X-API-Key', process.env.BACKEND_API_TOKEN);
  }

  const body = ['GET', 'HEAD'].includes(request.method)
  ? undefined
  : await request.arrayBuffer();

  const response = await fetch(url, {
    method: request.method,
    headers,
    body,
  });

  return new NextResponse(response.body, {
    status: response.status,
    headers: { 'content-type': response.headers.get('content-type') || 'application/json' },
  });
}

export const GET = proxy;
export const POST = proxy;
