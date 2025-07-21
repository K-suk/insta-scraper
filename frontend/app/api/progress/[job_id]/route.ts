import { NextRequest, NextResponse } from 'next/server'

export async function GET(req: NextRequest, { params }: { params: { job_id: string } }) {
  const res = await fetch(`http://localhost:8000/progress/${params.job_id}`)
  const json = await res.json()
  return NextResponse.json(json)
}
