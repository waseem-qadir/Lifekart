'use client'

import { apiClient } from '@/lib/api'
import { useEffect, useState } from 'react'
import { ShoppingBag, Pause, Play, X, Loader2 } from 'lucide-react'

interface Subscription {
  id: string
  product_id: string
  quantity_per_delivery: number
  frequency_days: number
  start_date: string
  end_date: string
  status: string
  locked_unit_price: number
  source: string
  product?: { name: string; unit_size: string }
}

export default function SubscriptionsPage() {
  const [subs, setSubs] = useState<Subscription[]>([])
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState<string | null>(null)

  async function load() {
    setLoading(true)
    try {
      const data = await apiClient('/subscriptions/').catch(() => [])
      setSubs(Array.isArray(data) ? data : [])
    } catch {} finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  async function toggleStatus(sub: Subscription) {
    setActionLoading(sub.id)
    try {
      if (sub.status === 'active') {
        await apiClient(`/subscriptions/${sub.id}/pause`, { method: 'POST' })
      } else if (sub.status === 'paused') {
        await apiClient(`/subscriptions/${sub.id}/resume`, { method: 'POST' })
      } else if (sub.status !== 'cancelled' && sub.status !== 'completed') {
        await apiClient(`/subscriptions/${sub.id}`, { method: 'DELETE' })
      }
      setSubs(prev => prev.map(s =>
        s.id === sub.id
          ? { ...s, status: sub.status === 'active' ? 'paused' : sub.status === 'paused' ? 'active' : 'cancelled' }
          : s
      ))
      await load()
    } catch {} finally { setActionLoading(null) }
  }

  if (loading) {
    return (
      <div className="space-y-4 animate-pulse">
        <div className="h-8 bg-gray-200 rounded w-48" />
        {[1,2,3].map(i => <div key={i} className="h-24 bg-gray-100 rounded-2xl" />)}
      </div>
    )
  }

  const aiSuggested = subs.filter(s => s.source === 'ai_generated')
  const directSubs = subs.filter(s => s.source !== 'ai_generated')

  return (
    <div className="space-y-6">
      <h1 className="text-3xl md:text-4xl font-display font-extrabold uppercase tracking-tighter">My Subscriptions</h1>

      {subs.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-2xl shadow-card">
          <ShoppingBag className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500 font-bold uppercase tracking-wider">No subscriptions yet</p>
          <p className="text-sm text-gray-400 mt-1">Sign an agreement or create a household to get started</p>
        </div>
      ) : (
        <div className="space-y-3">
          {subs.map((sub) => (
            <div key={sub.id} className="bg-white rounded-2xl p-5 shadow-card flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 bg-surface-muted rounded-xl flex items-center justify-center">
                  <ShoppingBag className="w-5 h-5 text-gray-400" />
                </div>
                <div>
                  <p className="text-sm font-semibold">{sub.product?.name || sub.product_id?.slice(0, 8)}</p>
                  <p className="text-xs text-gray-400">
                    {sub.quantity_per_delivery} × every {sub.frequency_days}d · ₹{Number(sub.locked_unit_price).toLocaleString('en-IN')}/unit
                    {sub.source === 'ai_generated' && (
                      <span className="ml-2 text-accent font-semibold">· AI Suggested</span>
                    )}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className={`text-xs font-bold uppercase px-2.5 py-1 rounded-full ${
                  sub.status === 'active' ? 'bg-green-50 text-green-700' :
                  sub.status === 'paused' ? 'bg-amber-50 text-amber-700' :
                  'bg-gray-100 text-gray-500'
                }`}>
                  {sub.source === 'ai_generated' ? 'Suggested' : sub.status}
                </span>
                {(sub.status === 'active' || sub.status === 'paused') && (
                  <button
                    onClick={() => toggleStatus(sub)}
                    disabled={actionLoading === sub.id}
                    className={`p-2 rounded-lg transition-all ${
                      sub.status === 'active'
                        ? 'bg-amber-50 text-amber-600 hover:bg-amber-100'
                        : 'bg-green-50 text-green-600 hover:bg-green-100'
                    }`}
                  >
                    {actionLoading === sub.id ? <Loader2 className="w-4 h-4 animate-spin" /> :
                     sub.status === 'active' ? <Pause className="w-4 h-4" /> :
                     <Play className="w-4 h-4" />}
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}