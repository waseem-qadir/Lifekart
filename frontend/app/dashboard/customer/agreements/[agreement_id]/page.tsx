'use client'

import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { apiClient } from '@/lib/api'
import Link from 'next/link'
import {
  FileSignature, ShieldCheck, Loader2, ArrowLeft, ShoppingBag, Package, Sparkles
} from 'lucide-react'

interface AgreementItem {
  id: string
  product_id: string
  locked_unit_price: number
  committed_monthly_qty: number
  frequency_days: number
  total_item_value: number | null
}

interface Agreement {
  id: string
  household_id: string
  manufacturer_id: string
  status: string
  start_date: string
  end_date: string
  price_ceiling_agreed: number | null
  total_contract_value: number | null
  signed_at: string | null
  items: AgreementItem[]
}

async function fetchLifetimeYears(): Promise<number> {
  try {
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/analytics/public/config`, { cache: 'no-store' })
    if (!res.ok) return 60
    const data = await res.json()
    return data.max_lifetime_years || 60
  } catch { return 60 }
}

export default function AgreementReviewPage() {
  const params = useParams()
  const router = useRouter()
  const [agreement, setAgreement] = useState<Agreement | null>(null)
  const [loading, setLoading] = useState(true)
  const [signing, setSigning] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState('')
  const [years, setYears] = useState(60)

  useEffect(() => { fetchLifetimeYears().then(setYears) }, [])

  async function load() {
    try {
      const data = await apiClient(`/agreements/${params.agreement_id}`)
      setAgreement(data)
    } catch (err: any) { setError(err.message) } finally { setLoading(false) }
  }

  useEffect(() => { load() }, [params.agreement_id])

  async function handleSign() {
    if (!agreement) return
    setSigning(true)
    setError('')
    try {
      await apiClient(`/agreements/${agreement.id}/sign`, { method: 'POST' })
      setGenerating(true)

      try {
        const res = await apiClient('/subscriptions/generate', { method: 'POST', body: JSON.stringify({}) })
        await pollTask(res.task_id)
      } catch {
        router.push('/dashboard/customer/subscriptions')
      }
    } catch (err: any) {
      setError(err.message)
      setSigning(false)
    }
  }

  async function pollTask(taskId: string) {
    for (let i = 0; i < 30; i++) {
      await new Promise(r => setTimeout(r, 2000))
      try {
        const status = await apiClient(`/subscriptions/tasks/${taskId}`)
        if (status.status === 'SUCCESS' || status.status === 'FAILURE') {
          router.push('/dashboard/customer/subscriptions')
          return
        }
      } catch {}
    }
    router.push('/dashboard/customer/subscriptions')
  }

  function calculateYearlyCost(): number {
    if (!agreement?.items) return 0
    return agreement.items.reduce((sum, item) => {
      return sum + (item.locked_unit_price || 0) * item.committed_monthly_qty * (30 / item.frequency_days) * 12
    }, 0)
  }

  if (loading) {
    return (
      <div className="space-y-4 animate-pulse p-6 max-w-3xl mx-auto">
        <div className="h-8 bg-gray-200 rounded w-64" />
        <div className="h-64 bg-gray-100 rounded-2xl" />
      </div>
    )
  }

  if (error || !agreement) {
    return (
      <div className="max-w-3xl mx-auto px-6 py-32 text-center">
        <h2 className="text-4xl font-display font-extrabold uppercase tracking-tighter mb-4">Agreement Not Found</h2>
        <p className="text-gray-500 mb-8">{error || 'This agreement may have been cancelled.'}</p>
        <Link href="/dashboard/customer/agreements" className="text-accent font-bold hover:underline">Back to Agreements</Link>
      </div>
    )
  }

  const start = new Date(agreement.start_date)
  const end = new Date(agreement.end_date)
  const durationYears = Math.round((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24 * 365.25))
  const yearlyCost = calculateYearlyCost()

  if (agreement.status === 'active') {
    return (
      <div className="max-w-3xl mx-auto px-6 py-16 text-center">
        <div className="bg-green-50 border border-green-200 rounded-2xl p-8 mb-8">
          <ShieldCheck className="w-16 h-16 text-green-500 mx-auto mb-4" />
          <h2 className="text-2xl font-display font-extrabold uppercase tracking-tighter text-green-800">
            Contract Active
          </h2>
          <p className="text-green-600 mt-2 mb-6">
            Signed on {agreement.signed_at ? new Date(agreement.signed_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' }) : '—'}
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link
              href="/dashboard/customer/subscriptions"
              className="px-6 py-3 text-sm font-bold text-white bg-green-600 rounded-lg shadow-button hover:shadow-button-hover hover:-translate-y-0.5 transition-all"
            >
              View Subscriptions
            </Link>
            <Link
              href="/dashboard/customer/agreements"
              className="px-6 py-3 text-sm font-bold text-green-700 bg-green-100 rounded-lg hover:bg-green-200 transition-all"
            >
              All Agreements
            </Link>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-3xl mx-auto px-6 py-8 space-y-8">
      <Link
        href="/dashboard/customer/agreements"
        className="inline-flex items-center gap-2 text-sm font-medium text-gray-500 hover:text-accent transition-colors"
      >
        <ArrowLeft className="w-4 h-4" /> Back to Agreements
      </Link>

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl md:text-4xl font-display font-extrabold uppercase tracking-tighter">Review & Sign</h1>
          <p className="text-gray-500 mt-1 text-sm">
            {start.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
            {' → '}
            {end.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
          </p>
        </div>
        <span className="text-xs font-bold uppercase px-3 py-1.5 rounded-full bg-amber-50 text-amber-700">Draft</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-2xl p-5 shadow-card">
          <p className="text-xs text-gray-400 uppercase tracking-wider mb-1">Duration</p>
          <p className="text-2xl font-display font-extrabold">{durationYears} years</p>
        </div>
        <div className="bg-white rounded-2xl p-5 shadow-card">
          <p className="text-xs text-gray-400 uppercase tracking-wider mb-1">Yearly Cost</p>
          <p className="text-2xl font-display font-extrabold">₹{Math.round(yearlyCost).toLocaleString('en-IN')}</p>
        </div>
        <div className="bg-white rounded-2xl p-5 shadow-card">
          <p className="text-xs text-gray-400 uppercase tracking-wider mb-1">Price Ceiling</p>
          <p className="text-2xl font-display font-extrabold">{Number(agreement.price_ceiling_agreed || 0)}%</p>
        </div>
      </div>

      <div className="bg-white rounded-2xl p-6 shadow-card">
        <h3 className="text-lg font-display font-bold uppercase tracking-tight mb-4">Products ({agreement.items.length})</h3>
        <div className="space-y-3">
          {agreement.items.map((item) => {
            const yearly = (item.locked_unit_price || 0) * item.committed_monthly_qty * (30 / item.frequency_days) * 12
            return (
              <div key={item.id} className="flex items-center justify-between py-3 border-b border-surface-border last:border-0">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-surface-muted rounded-lg flex items-center justify-center">
                    <Package className="w-5 h-5 text-gray-400" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold">{item.product_id?.slice(0, 8)}</p>
                    <p className="text-xs text-gray-400">
                      {item.committed_monthly_qty} × every {item.frequency_days}d · ₹{Number(item.locked_unit_price).toLocaleString('en-IN')}/unit
                    </p>
                  </div>
                </div>
                <p className="text-sm font-display font-bold">₹{Math.round(yearly).toLocaleString('en-IN')}/yr</p>
              </div>
            )
          })}
        </div>
      </div>

      <div className="bg-black text-white rounded-2xl p-6">
        <div className="flex items-center gap-2 mb-4">
          <ShieldCheck className="w-5 h-5 text-accent" />
          <h3 className="text-lg font-display font-bold uppercase tracking-tight">Lifetime Protection</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div>
            <p className="font-bold mb-1">Price Ceiling</p>
            <p className="text-white/60">Max {Number(agreement.price_ceiling_agreed || 0)}% annual increase — legally enforceable.</p>
          </div>
          <div>
            <p className="font-bold mb-1">No Cancellation Fees</p>
            <p className="text-white/60">Cancel any subscription anytime with no penalty.</p>
          </div>
          <div>
            <p className="font-bold mb-1">Auto-Substitution</p>
            <p className="text-white/60">Out-of-stock products auto-substituted at no extra cost.</p>
          </div>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl px-4 py-3 text-sm text-red-700">{error}</div>
      )}

      {generating && (
        <div className="bg-accent/5 border border-accent/20 rounded-2xl p-6 text-center">
          <Sparkles className="w-8 h-8 text-accent mx-auto mb-3 animate-pulse" />
          <h3 className="text-lg font-display font-bold uppercase tracking-tight mb-1">Mapping Your Schedule</h3>
          <p className="text-sm text-gray-500">Computing delivery schedules for every household member based on age, health, and consumption patterns.</p>
          <div className="mt-4 w-full bg-gray-200 rounded-full h-1.5 overflow-hidden">
            <div className="bg-accent h-full rounded-full animate-pulse w-3/4" />
          </div>
        </div>
      )}

      <button
        onClick={handleSign}
        disabled={signing || generating}
        className="w-full flex items-center justify-center gap-3 px-6 py-5 text-sm font-bold
                   text-white bg-accent rounded-lg shadow-button hover:shadow-button-hover
                   hover:-translate-y-1 transition-all duration-200 disabled:opacity-50"
      >
        {signing ? <Loader2 className="w-5 h-5 animate-spin" /> : <FileSignature className="w-5 h-5" />}
        {signing ? 'Activating...' : `Sign & Activate ${durationYears}-Year Contract`}
      </button>
    </div>
  )
}