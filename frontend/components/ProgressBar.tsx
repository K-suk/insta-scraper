'use client'

export default function ProgressBar({ progress }: { progress: number }) {
  return (
    <div className="w-full bg-gray-200 h-4 rounded">
      <div
        className="bg-green-500 h-4 rounded"
        style={{ width: `${progress}%` }}
      />
    </div>
  )
}
