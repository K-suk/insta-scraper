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
  const [error, setError] = useState('')
  const [debugInfo, setDebugInfo] = useState('')

  useEffect(() => {
    if (!jobId) {
      setError('Job IDが見つかりません')
      return
    }

    setDebugInfo(`Job ID: ${jobId}`)

    const interval = setInterval(async () => {
      try {
        const data = await checkProgress(jobId)
        if (data) {
          setProgress(data.progress || 0)
          setStatus(data.status || 'unknown')
          setDebugInfo(`Job ID: ${jobId}, Progress: ${data.progress}%, Status: ${data.status}`)
          if (data.status === 'done') {
            clearInterval(interval)
          }
        } else {
          setError('プログレス情報を取得できませんでした')
          setDebugInfo(`Job ID: ${jobId} - データなし`)
        }
      } catch (err) {
        setError(`エラー: ${err}`)
        clearInterval(interval)
      }
    }, 1000)

    return () => clearInterval(interval)
  }, [jobId])

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-2xl font-bold">スクレイピング結果</h1>

      {/* デバッグ情報 */}
      <div className="p-2 bg-gray-100 text-sm">
        {debugInfo}
      </div>

      {error && (
        <div className="p-4 bg-red-100 text-red-700 border border-red-300 rounded">
          {error}
        </div>
      )}

      {!error && (
        <>
          {status === 'done' ? (
            <DownloadCard jobId={jobId} />
          ) : (
            <>
              <div className="text-lg">進捗: {progress}%</div>
              <ProgressBar progress={progress} />
              <div className="text-gray-600">ステータス: {status}</div>
            </>
          )}
        </>
      )}
    </div>
  )
}
