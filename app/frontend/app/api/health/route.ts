import { NextResponse } from 'next/server'

/**
 * Health check endpoint for Docker healthcheck
 */
export async function GET() {
  return NextResponse.json({ status: 'ok' }, { status: 200 })
}
