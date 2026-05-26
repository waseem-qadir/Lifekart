'use client'

import { useState, useEffect } from 'react'
import { Calculator, Loader2, TrendingDown, ShieldCheck, X, ShoppingCart } from 'lucide-react'
import { apiClient } from '@/lib/api'

interface Product {
  id: string
  name: string
  sku: string
  unit_price_wholesale: number
  unit_price_retail: number
  unit_size: string | null
  stock_quantity: number
}

interface AddToContractModalProps {
  product: Product
  onClose: () => void
  onCreated: (agreementId: string) => void
  lifetimeYears?: number
}

const FREQUENCIES = [
  { days: 7, label: 'Weekly' },
  { days: 15, label: 'Bi-weekly' },
  { days: 30, label: 'Monthly' },
]

async function fetchLifetimeYears(): Promise<number> {
  try {
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/analytics/public/config`, { cache: 'no-store' })
    if (!res.ok) return 60
    const data = await res.json()
    return data.max_lifetime_years || 60
  } catch {
    return 60
  }
}

export default function AddToContractModal({ product, onClose, onCreated, lifetimeYears: propYears }: AddToContractModalProps) {
  const [quantity, setQuantity] = useState(10)
  const [frequency, setFrequency] = useState(30)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [years, setYears] = useState(propYears || 60)

  useEffect(() => {
    if (propYears) { setYears(propYears); return }
    fetchLifetimeYears().then(setYears)
  }, [propYears])

  const monthlyQty = quantity * (30 / frequency)
  const retailMonthly = product.unit_price_retail * monthlyQty
  const wholesaleMonthly = product.unit_price_wholesale * monthlyQty
  const monthlySavings = retailMonthly - wholesaleMonthly
  const lifetimeSavings = monthlySavings * 12 * years
  const savingsPercent = retailMonthly > 0 ? Math.round((monthlySavings / retailMonthly) * 100) : 0

  async function handleAddToContract(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const tokens = typeof window !== 'undefined' ? localStorage.getItem('auth_tokens') : null
      if (!tokens) throw new Error('Please sign in to create a contract')

      const household = await apiClient('/profiling/households/me')
      if (!household) throw new Error('Create your household profile first')

      const manufacturers = await apiClient('/catalog/manufacturers?limit=5')
      const verified = manufacturers.find((m: any) => m.is_verified)
      if (!verified) throw new Error('No verified manufacturer available')

      const startDate = new Date()
      const endDate = new Date()
      endDate.setFullYear(endDate.getFullYear() + years)

      const agreement = await apiClient('/agreements/', {
        method: 'POST',
        body: JSON.stringify({
          manufacturer_id: verified.id,
          start_date: startDate.toISOString().split('T')[0],
          end_date: endDate.toISOString().split('T')[0],
          price_ceiling_agreed: '10.00',
          items: [{
            product_id: product.id,
            locked_unit_price: String(product.unit_price_wholesale),
            committed_monthly_qty: quantity,
            frequency_days: frequency,
          }],
        }),
      })

      onCreated(agreement.id)
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-white rounded-2xl shadow-float-xl w-full max-w-md max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-surface-border">
          <div className="flex items-center gap-2">
            <ShoppingCart className="w-5 h-5 text-accent" />
            <h2 className="text-xl font-display font-extrabold uppercase tracking-tighter">Add to Contract</h2>
          </div>
          <button onClick={onClose} className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-surface-muted">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleAddToContract} className="p-6 space-y-5">
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-xl px-4 py-3 text-sm text-red-700">{error}</div>
          )}

          <div className="bg-surface-muted rounded-2xl p-4">
            <h3 className="text-sm font-display font-extrabold uppercase tracking-tight">{product.name}</h3>
            <p className="text-xs text-gray-400 mt-0.5">{product.sku} · {product.unit_size || 'unit'}</p>
            <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-200">
              <div>
                <span className="text-xs text-gray-400 line-through">₹{Number(product.unit_price_retail).toLocaleString('en-IN')}</span>
                <span className="ml-2 text-lg font-display font-extrabold">₹{Number(product.unit_price_wholesale).toLocaleString('en-IN')}</span>
                <span className="text-xs text-gray-400"> / {product.unit_size || 'unit'}</span>
              </div>
              <span className="text-xs font-bold text-green-600 bg-green-50 px-2 py-0.5 rounded-full">
                Save {savingsPercent}%
              </span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-400 mb-1">Quantity/Month</label>
              <input
                type="number" min="1" required value={quantity}
                onChange={(e) => setQuantity(Number(e.target.value))}
                className="w-full px-4 py-3 border border-surface-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/20"
              />
            </div>
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-400 mb-1">Frequency</label>
              <select
                value={frequency}
                onChange={(e) => setFrequency(Number(e.target.value))}
                className="w-full px-4 py-3 border border-surface-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/20"
              >
                {FREQUENCIES.map(f => <option key={f.days} value={f.days}>{f.label}</option>)}
              </select>
            </div>
          </div>

          <div className="bg-surface-muted rounded-2xl p-5">
            <div className="flex items-center gap-2 mb-3">
              <Calculator className="w-4 h-4 text-accent" />
              <span className="text-xs font-bold uppercase tracking-wider text-gray-500">{years}-Year Savings Projection</span>
            </div>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">Retail / month</span>
                <span className="text-sm font-bold text-gray-400 line-through">₹{Math.round(retailMonthly).toLocaleString('en-IN')}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-500">Wholesale / month</span>
                <span className="text-sm font-bold text-green-600">₹{Math.round(wholesaleMonthly).toLocaleString('en-IN')}</span>
              </div>
              <div className="flex justify-between border-t border-gray-200 pt-3">
                <span className="text-sm font-bold text-black">Monthly Savings</span>
                <span className="text-sm font-bold text-green-600">₹{Math.round(monthlySavings).toLocaleString('en-IN')} ({savingsPercent}%)</span>
              </div>
              <div className="flex justify-between border-t border-gray-200 pt-3">
                <span className="font-display font-extrabold uppercase tracking-tight text-black">{years}-Year Total</span>
                <span className="font-display font-extrabold text-green-600 text-lg">₹{Math.round(lifetimeSavings).toLocaleString('en-IN')}</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 text-xs text-gray-400">
            <ShieldCheck className="w-4 h-4 text-accent" />
            Price locked for {years} years. Protected against inflation.
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 px-6 py-3.5 text-sm font-bold
                       text-white bg-accent rounded-lg shadow-button hover:shadow-button-hover
                       hover:-translate-y-0.5 transition-all disabled:opacity-50"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <TrendingDown className="w-4 h-4" />}
            Lock In {years}-Year Price
          </button>
        </form>
      </div>
    </div>
  )
}