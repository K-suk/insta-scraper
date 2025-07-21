'use client'

import { saveAs } from 'file-saver'
import { useEffect } from 'react'
import { downloadResult } from '../services/api'

export default function DownloadCard({ jobId }: { jobId: string }) {
  const handleDownload = async () => {
    const blob = await downloadResult(jobId)
    saveAs(blob, `instagram_reels_${jobId}.csv`)
  }

  useEffect(() => {
    handleDownload()
  }, [])

  return (
    <div className="p-4 border">
      <button className="px-4 py-2 bg-green-500 text-white" onClick={handleDownload}>
        Download CSV
      </button>
    </div>
  )
}
