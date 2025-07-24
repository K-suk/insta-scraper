'use client'

import { useState } from 'react'
import { startScrape } from '../services/api'

export default function ScrapeForm() {
  const [usernames, setUsernames] = useState('')
  const [hashtags, setHashtags] = useState('')
  const [maxItems, setMaxItems] = useState(10)
  const [columns, setColumns] = useState<string[]>([])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const res = await startScrape({
      usernames: usernames.split('\n').filter(Boolean),
      hashtags: hashtags.split(',').map(h => h.trim()).filter(Boolean),
      max_items: maxItems,
      columns,
    })
    if (res?.job_id) {
      window.location.href = `/result?job_id=${res.job_id}`
    }
  }

  const toggleColumn = (col: string) => {
    setColumns(cols =>
      cols.includes(col) ? cols.filter(c => c !== col) : [...cols, col]
    )
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <textarea
        className="w-full border p-2"
        rows={4}
        placeholder="スクレイピング対象のユーザー名を1行ずつ入力してください (例: username1\nusername2)"
        value={usernames}
        onChange={e => setUsernames(e.target.value)}
      />
      <input
        className="w-full border p-2"
        placeholder="スクレイピング対象のハッシュタグをカンマ区切りで入力 (例: hashtag1, hashtag2)"
        value={hashtags}
        onChange={e => setHashtags(e.target.value)}
      />
      <input
        type="number"
        className="w-full border p-2"
        placeholder="取得する最大投稿数 (例: 10)"
        value={maxItems}
        onChange={e => setMaxItems(Number(e.target.value))}
      />
      <div>
        {['likes', 'comments', 'video_view_count'].map(col => (
          <label key={col} className="mr-4">
            <input
              type="checkbox"
              checked={columns.includes(col)}
              onChange={() => toggleColumn(col)}
            />{' '}
            {col}
          </label>
        ))}
      </div>
      <button className="px-4 py-2 bg-blue-500 text-white" type="submit">
        Start Scraping
      </button>
    </form>
  )
}
