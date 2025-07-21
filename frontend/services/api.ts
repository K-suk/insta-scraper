export async function startScrape(data: any) {
  const res = await fetch('/api/scrape', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) return null
  return res.json()
}

export async function checkProgress(jobId: string) {
  const res = await fetch(`/api/progress/${jobId}`)
  if (!res.ok) return null
  return res.json()
}

export async function downloadResult(jobId: string) {
  const res = await fetch(`/api/download/${jobId}`)
  if (!res.ok) throw new Error('Download failed')
  return res.blob()
}
