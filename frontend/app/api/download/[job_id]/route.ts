import { NextRequest } from "next/server";

export async function GET(
  req: NextRequest,
  { params }: { params: { job_id: string } }
) {
  const res = await fetch(`http://127.0.0.1:8000/download/${params.job_id}`);
  const blob = await res.blob();
  return new Response(blob, {
    headers: {
      "Content-Type": "text/csv",
      "Content-Disposition": `attachment; filename=instagram_reels_${params.job_id}.csv`,
    },
  });
}
