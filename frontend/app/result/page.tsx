'use client'
import { useSearchParams } from 'next/navigation'
import { useEffect, useState } from 'react'
import ProgressBar from '../../components/ProgressBar'
import DownloadCard from '../../components/DownloadCard'
import { checkProgress } from '../../services/api'

export default function ResultPage() {
  const params = useSearchParams()
  const jobId = params.get('job_id') || ''
  const [progress, setProgress] = useState(0)
  const [status, setStatus] = useState('running')

  useEffect(() => {
    if (!jobId) return
    const interval = setInterval(async () => {
      const data = await checkProgress(jobId)
      if (data) {
        setProgress(data.progress)
        setStatus(data.status)
        if (data.status === 'done') clearInterval(interval)
      }
    }, 1000)
    return () => clearInterval(interval)
  }, [jobId])

  return (
    <div className="p-4">
      {status === 'done' ? (
        <DownloadCard jobId={jobId} />
      ) : (
        <ProgressBar progress={progress} />
      )}
    </div>
  )
}
