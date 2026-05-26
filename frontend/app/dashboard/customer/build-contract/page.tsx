'use client'

import { apiClient } from '@/lib/api'
import { useEffect, useState } from 'react'
import Link from 'next/link'
import {
  Handshake, Plus, Trash2, Package, FileSignature, Calculator, Clock,
  TrendingDown, ArrowRight, Loader2, ShieldCheck, Calendar
} from 'lucide-react'
import { useRouter } from 'next/navigation'

interface AgreementItem {
  id: string
  agreement_id: string
  product_id: string
  locked_unit_price: number
  committed_monthly_qty: number
  frequency_days: number
  total_item_value: number | null
  product?: any
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
  created_at: string
  items: AgreementItem[]
}

interface Category {
  id: string
  name: string
  slug: string
}

interface Product {
  id: string
  name: string
  sku: string
  category_id: string
  manufacturer_id: string
  unit_price_wholesale: number
  unit_price_retail: number
  unit_size: string | null
  stock_quantity: number
  min_order_quantity: number
}

const FREQUENCIES = [
  { days: 7, label: 'Weekly' },
  { days: 15, label: 'Bi-weekly' },
  { days: 30, label: 'Monthly' },
]

export default function BuildContractPage() {
  const router = useRouter()
  const [agreement, setAgreement] = useState<Agreement | null>(null)
  const [categories, setCategories] = useState<Category[]>([])
  const [products, setProducts] = useState<Product[]>([])
  const [selectedCategory, setSelectedCategory] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState<string | null>(null)

  const [addForm, setAddForm] = useState({
    product_id: '',
    committed_monthly_qty: 10,
    frequency_days: 30,
  })

  async function loadAgreements() {
    try {
      const data = await apiClient('/agreements/').catch(() => [])
      const drafts = (data as Agreement[]).filter((a: Agreement) => a.status === 'draft' && a.signed_at === null)
      const draft = drafts[0] || null
      setAgreement(draft)

      const cats = await apiClient('/catalog/categories?limit=100').catch(() => [])
      setCategories(cats)
      if (draft && cats.length > 0) {
        const itemProductIds = draft.items.map(i => i.product_id)
        const allProds = await apiClient('/catalog/products?limit=200').catch(() => [])
        const filtered = allProds.filter((p: any) => !itemProductIds.includes(p.id))
        setProducts(filtered)
      }
    } catch {} finally { setLoading(false) }
  }

  useEffect(() => { loadAgreements() }, [])

  useEffect(() => {
    async function loadProducts() {
      if (!selectedCategory) return
      try {
        const data = await apiClient(`/catalog/products?category_id=${selectedCategory}&limit=100`).catch(() => [])
        const filtered = agreement ? data.filter((p: any) => !agreement.items.some(i => i.product_id === p.id)) : data
        setProducts(filtered)
      } catch {}
    }
    loadProducts()
  }, [selectedCategory])

  async function createAgreement() {
    setActionLoading('create')

    const household = await apiClient('/profiling/households/me').catch(() => null)
    if (!household) {
      alert('Please set up your household first.')
      setActionLoading(null)
      return
    }

    try {
      const manufacturers = await apiClient('/catalog/manufacturers?limit=5').catch(() => [])
      const verified = manufacturers.find((m: any) => m.is_verified)
      if (!verified) { setActionLoading(null); alert('No verified manufacturer available'); return }

      const today = new Date()
      const startDate = new Date(today.getFullYear(), today.getMonth() + 1, 1).toISOString().split('T')[0]
      const endDate = new Date(today.getFullYear() + 60, today.getMonth() + 1, 0).toISOString().split('T')[0]

      const newAgreement = await apiClient('/agreements/', {
        method: 'POST',
        body: JSON.stringify({
          manufacturer_id: verified.id,
          start_date: startDate,
          end_date: endDate,
          price_ceiling_agreed: '10.00',
          items: [{
            product_id: products[0]?.id,
            locked_unit_price: String(products[0]?.unit_price_wholesale || 100),
            committed_monthly_qty: 10,
            frequency_days: 30,
          }],
        }),
      })
      setAgreement(newAgreement)
      setProducts(prev => prev.filter(p => p.id !== products[0]?.id))
    } catch (err: any) {
      alert(err.message)
    } finally {
      setActionLoading(null)
    }
  }

  async function addItem(e: React.FormEvent) {
    e.preventDefault()
    if (!agreement || !addForm.product_id) return
    setActionLoading('add')

    const product = products.find(p => p.id === addForm.product_id)
    if (!product) { setActionLoading(null); return }

    try {
      await apiClient(`/agreements/${agreement.id}/items`, {
        method: 'POST',
        body: JSON.stringify({
          product_id: addForm.product_id,
          locked_unit_price: String(product.unit_price_wholesale),
          committed_monthly_qty: addForm.committed_monthly_qty,
          frequency_days: addForm.frequency_days,
        }),
      })
      const refreshed = await apiClient(`/agreements/${agreement.id}`)
      setAgreement(refreshed)
      setProducts(prev => prev.filter(p => p.id !== addForm.product_id))
      setAddForm({ product_id: '', committed_monthly_qty: 10, frequency_days: 30 })
    } catch (err: any) {
      alert(err.message)
    } finally {
      setActionLoading(null)
    }
  }

  async function removeItem(itemId: string) {
    if (!agreement) return
    setActionLoading(itemId)
    try {
      await apiClient(`/agreements/items/${itemId}`, { method: 'DELETE' })
      const refreshed = await apiClient(`/agreements/${agreement.id}`)
      setAgreement(refreshed.items.length > 0 ? refreshed : null)

      if ((refreshed.items.length === 0)) return

      const allProds = await apiClient('/catalog/products?limit=200').catch(() => [])
      const refreshedItemIds = refreshed.items.map((i: any) => i.product_id)
      setProducts(allProds.filter((p: any) => !refreshedItemIds.includes(p.id)))
    } catch {} finally { setActionLoading(null) }
  }

  async function signAgreement() {
    if (!agreement) return
    setActionLoading('sign')
    try {
      await apiClient(`/agreements/${agreement.id}/sign`, { method: 'POST' })
      router.push('/dashboard/customer/subscriptions')
    } catch (err: any) {
      alert(err.message)
    } finally {
      setActionLoading(null)
    }
  }

  function calculateTotal(): number {
    if (!agreement?.items) return 0
    return agreement.items.reduce((sum, item) => {
      const monthly = (item.locked_unit_price || 0) * item.committed_monthly_qty
      const deliveriesPerMonth = 30 / item.frequency_days
      return sum + (monthly * deliveriesPerMonth)
    }, 0)
  }

  function calculateSavings(): number {
    if (!agreement?.items) return 0
    return agreement.items.reduce((sum, item) => {
      const product = products.find(p => p.id === item.product_id)
      if (!product) return sum
      const retail = product.unit_price_retail * item.committed_monthly_qty * (30 / item.frequency_days)
      const wholesale = item.locked_unit_price * item.committed_monthly_qty * (30 / item.frequency_days)
      return sum + (retail - wholesale)
    }, 0)
  }

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-8 bg-gray-200 rounded w-64" />
        <div className="h-64 bg-gray-100 rounded-2xl" />
      </div>
    )
  }

  const monthlyTotal = calculateTotal()
  const monthlySavings = calculateSavings()

  const filteredProducts = selectedCategory
    ? products.filter(p => p.category_id === selectedCategory)
    : products

  const productMap = products.reduce((acc: any, p) => { acc[p.id] = p; return acc }, {})

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl md:text-4xl font-display font-extrabold uppercase tracking-tighter">
          Build Your Contract
        </h1>
        <p className="text-gray-500 mt-1">Select products, set quantities, and lock in wholesale prices for 60 years.</p>
      </div>

      {agreement && (
        <div className="bg-black text-white rounded-2xl p-6 shadow-card">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <p className="text-xs text-white/50 uppercase tracking-wider mb-1">Monthly Cost</p>
              <div className="text-2xl font-display font-extrabold">₹{monthlyTotal.toLocaleString('en-IN')}</div>
            </div>
            <div>
              <p className="text-xs text-white/50 uppercase tracking-wider mb-1">Monthly Savings</p>
              <div className="text-2xl font-display font-extrabold text-green-400">₹{monthlySavings.toLocaleString('en-IN')}</div>
            </div>
            <div>
              <p className="text-xs text-white/50 uppercase tracking-wider mb-1">60-Year Savings</p>
              <div className="text-2xl font-display font-extrabold text-green-400">₹{(monthlySavings * 12 * 60).toLocaleString('en-IN')}</div>
            </div>
            <div>
              <p className="text-xs text-white/50 uppercase tracking-wider mb-1">Status</p>
              <div className="text-lg font-display font-bold">{agreement.status.toUpperCase()}</div>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white rounded-2xl p-6 shadow-card">
            <h3 className="text-lg font-display font-bold uppercase tracking-tight mb-4 flex items-center gap-2">
              <Plus className="w-5 h-5 text-accent" />
              Add Products
            </h3>

            {!agreement && (
              <div className="text-center py-8">
                <Handshake className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500 font-bold uppercase tracking-wider mb-4">No active draft</p>
                <button
                  onClick={createAgreement}
                  disabled={actionLoading === 'create'}
                  className="px-6 py-3 text-sm font-bold text-white bg-accent rounded-lg
                             shadow-button hover:shadow-button-hover hover:-translate-y-0.5
                             transition-all disabled:opacity-50"
                >
                  {actionLoading === 'create' ? <Loader2 className="w-4 h-4 animate-spin inline mr-2" /> : null}
                  Create New Contract
                </button>
              </div>
            )}

            {agreement && (
              <>
                <div className="flex gap-3 mb-4">
                  <select
                    value={selectedCategory}
                    onChange={(e) => setSelectedCategory(e.target.value)}
                    className="flex-1 px-4 py-2.5 border border-surface-border rounded-lg text-sm
                               focus:outline-none focus:ring-2 focus:ring-accent/20"
                  >
                    <option value="">All categories</option>
                    {categories.map((cat) => (
                      <option key={cat.id} value={cat.id}>{cat.name}</option>
                    ))}
                  </select>
                </div>

                <form onSubmit={addItem} className="space-y-3">
                  <select
                    value={addForm.product_id}
                    onChange={(e) => setAddForm({ ...addForm, product_id: e.target.value })}
                    required
                    className="w-full px-4 py-2.5 border border-surface-border rounded-lg text-sm
                               focus:outline-none focus:ring-2 focus:ring-accent/20"
                  >
                    <option value="">Select a product...</option>
                    {filteredProducts.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name} — ₹{Number(p.unit_price_wholesale).toLocaleString('en-IN')}/{p.unit_size || 'unit'}
                      </option>
                    ))}
                  </select>

                  <div className="grid grid-cols-3 gap-3">
                    <input
                      type="number"
                      min="1"
                      required
                      value={addForm.committed_monthly_qty}
                      onChange={(e) => setAddForm({ ...addForm, committed_monthly_qty: Number(e.target.value) })}
                      className="px-4 py-2.5 border border-surface-border rounded-lg text-sm
                                 focus:outline-none focus:ring-2 focus:ring-accent/20"
                      placeholder="Qty/month"
                    />
                    <select
                      value={addForm.frequency_days}
                      onChange={(e) => setAddForm({ ...addForm, frequency_days: Number(e.target.value) })}
                      className="px-4 py-2.5 border border-surface-border rounded-lg text-sm
                                 focus:outline-none focus:ring-2 focus:ring-accent/20"
                    >
                      {FREQUENCIES.map((f) => (
                        <option key={f.days} value={f.days}>{f.label}</option>
                      ))}
                    </select>
                    <button
                      type="submit"
                      disabled={actionLoading === 'add'}
                      className="flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-bold
                                 text-white bg-accent rounded-lg shadow-button hover:shadow-button-hover
                                 hover:-translate-y-0.5 transition-all disabled:opacity-50"
                    >
                      {actionLoading === 'add' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                      Add
                    </button>
                  </div>
                </form>
              </>
            )}
          </div>

          {agreement && (
            <div className="bg-white rounded-2xl p-6 shadow-card">
              <h3 className="text-lg font-display font-bold uppercase tracking-tight mb-4">
                Contract Items ({agreement.items.length})
              </h3>
              <div className="space-y-3">
                {agreement.items.map((item) => {
                  const prod = productMap[item.product_id]
                  const monthly = (item.locked_unit_price || 0) * item.committed_monthly_qty * (30 / item.frequency_days)
                  return (
                    <div key={item.id} className="flex items-center justify-between py-3 border-b border-surface-border last:border-0">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-surface-muted rounded-lg flex items-center justify-center">
                          <Package className="w-5 h-5 text-gray-400" />
                        </div>
                        <div>
                          <p className="text-sm font-semibold">{prod?.name || item.product_id?.slice(0, 8)}</p>
                          <p className="text-xs text-gray-400">
                            {item.committed_monthly_qty} × every {item.frequency_days}d · @ ₹{Number(item.locked_unit_price).toLocaleString('en-IN')}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <p className="text-sm font-display font-bold">₹{Math.round(monthly).toLocaleString('en-IN')}/mo</p>
                          <p className="text-xs text-gray-400">₹{Number(item.locked_unit_price).toLocaleString('en-IN')}/unit</p>
                        </div>
                        <button
                          onClick={() => removeItem(item.id)}
                          disabled={actionLoading === item.id}
                          className="p-2 text-gray-400 hover:text-red-500 rounded-lg hover:bg-red-50 transition-colors"
                        >
                          {actionLoading === item.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
                        </button>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </div>

        {agreement && (
          <div className="space-y-4">
            <div className="bg-white rounded-2xl p-6 shadow-card">
              <h3 className="text-lg font-display font-bold uppercase tracking-tight mb-4 flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-accent" />
                Contract Summary
              </h3>
              <div className="space-y-3">
                <div>
                  <p className="text-xs text-gray-400 uppercase tracking-wider">Duration</p>
                  <p className="text-sm font-bold">
                    {agreement.start_date ? new Date(agreement.start_date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) : '—'}
                    {' → '}
                    {agreement.end_date ? new Date(agreement.end_date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) : '—'}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-400 uppercase tracking-wider">Monthly Cost</p>
                  <p className="text-lg font-display font-extrabold">₹{monthlyTotal.toLocaleString('en-IN')}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-400 uppercase tracking-wider">Monthly Savings</p>
                  <p className="text-lg font-display font-extrabold text-green-600">₹{monthlySavings.toLocaleString('en-IN')}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-400 uppercase tracking-wider">Price Ceiling</p>
                  <p className="text-sm font-bold">{agreement.price_ceiling_agreed}%</p>
                </div>
              </div>
            </div>

            <button
              onClick={signAgreement}
              disabled={actionLoading === 'sign' || !agreement.items.length}
              className="w-full flex items-center justify-center gap-2 px-6 py-4 text-sm font-bold
                         text-white bg-accent rounded-lg shadow-button hover:shadow-button-hover
                         hover:-translate-y-0.5 transition-all duration-200 disabled:opacity-50"
            >
              {actionLoading === 'sign' ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileSignature className="w-5 h-5" />}
              Sign 60-Year Contract
            </button>

            <Link
              href="/dashboard/customer/subscriptions"
              className="block w-full text-center px-6 py-4 text-sm font-bold text-gray-700
                         bg-white rounded-lg shadow-card hover:shadow-card-hover hover:-translate-y-0.5
                         transition-all"
            >
              View Existing Subscriptions
            </Link>
          </div>
        )}
      </div>
    </div>
  )
}