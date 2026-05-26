'use client'

import { apiClient } from '@/lib/api'
import { useEffect, useState } from 'react'
import Link from 'next/link'
import {
  Handshake, Plus, FileSignature, Clock, CheckCircle, XCircle,
  TrendingDown, ArrowRight, Package
} from 'lucide-react'

interface AgreementItem {
  id: string
  product_id: string
  product?: { id: string; name: string }
  locked_unit_price: number
  committed_monthly_qty: number
  frequency_days: number
  total_item_value: number | null
}

interface AgreementData {
  id: string
  status: string
  start_date: string
  end_date: string
  price_ceiling_agreed: number | null
  total_contract_value: number | null
  signed_at: string | null
  items: AgreementItem[]
}

export default function AgreementsPage() {
  const [agreements, setAgreements] = useState<AgreementData[]>([])
  const [loading, setLoading] = useState(true)

  async function load() {
    try {
      const data = await apiClient('/agreements/').catch(() => [])
      setAgreements(Array.isArray(data) ? data : [])
    } catch (err: any) {
      if (err?.message?.includes('permission')) setAgreements([])
      else setAgreements([])
    } finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  if (loading) {
    return (
      <div className="space-y-4 animate-pulse">
        <div className="h-8 bg-gray-200 rounded w-64" />
        {[1,2].map(i => <div key={i} className="h-32 bg-gray-100 rounded-2xl" />)}
      </div>
    )
  }

  const statusIcon = (status: string) => {
    switch (status) {
      case 'active': return <CheckCircle className="w-5 h-5 text-green-600" />
      case 'draft': return <Clock className="w-5 h-5 text-amber-600" />
      case 'cancelled': return <XCircle className="w-5 h-5 text-red-500" />
      default: return <FileSignature className="w-5 h-5 text-gray-400" />
    }
  }

  const statusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-50 text-green-700'
      case 'draft': return 'bg-amber-50 text-amber-700'
      case 'cancelled': return 'bg-red-50 text-red-500'
      default: return 'bg-gray-100 text-gray-500'
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl md:text-4xl font-display font-extrabold uppercase tracking-tighter">Agreements</h1>
          <p className="text-gray-500 mt-1">Your 60-year wholesale supply contracts.</p>
        </div>
        <Link
          href="/dashboard/customer/build-contract"
          className="flex items-center gap-2 px-5 py-2.5 text-sm font-bold text-white bg-accent rounded-lg
                     shadow-button hover:shadow-button-hover hover:-translate-y-0.5 transition-all"
        >
          <Plus className="w-4 h-4" />
          Build Contract
        </Link>
      </div>

      {agreements.length === 0 ? (
        <div className="bg-white rounded-2xl p-8 shadow-card text-center">
          <Handshake className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500 font-bold uppercase tracking-wider mb-2">No agreements yet</p>
          <p className="text-sm text-gray-400 mb-6">Lock in wholesale prices for 60 years by creating your first contract.</p>
          <Link
            href="/dashboard/customer/build-contract"
            className="inline-flex items-center gap-2 px-6 py-3 text-sm font-bold text-white bg-accent rounded-lg
                       shadow-button hover:shadow-button-hover hover:-translate-y-0.5 transition-all"
          >
            <Plus className="w-4 h-4" />
            Build Your First Contract
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {agreements.map((agreement) => (
            <div key={agreement.id} className="bg-white rounded-2xl p-6 shadow-card">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                    agreement.status === 'active' ? 'bg-green-50' :
                    agreement.status === 'draft' ? 'bg-amber-50' :
                    'bg-gray-100'
                  }`}>
                    {statusIcon(agreement.status)}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className={`text-xs font-bold uppercase px-2 py-0.5 rounded-full ${statusColor(agreement.status)}`}>
                        {agreement.status}
                      </span>
                    </div>
                    <p className="text-xs text-gray-400 mt-1">
                      {new Date(agreement.start_date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
                      {' → '}
                      {new Date(agreement.end_date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
                    </p>
                  </div>
                </div>

                <div className="text-right">
                  <p className="text-lg font-display font-extrabold">
                    ₹{Number(agreement.total_contract_value || 0).toLocaleString('en-IN')}
                  </p>
                  <p className="text-xs text-gray-400">Total Contract Value</p>
                </div>
              </div>

              <div className="space-y-2">
                {agreement.items.slice(0, 3).map((item) => (
                  <div key={item.id} className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                      <Package className="w-4 h-4 text-gray-400" />
                      <span className="text-gray-600">{item.product?.name || item.product_id?.slice(0, 8)}</span>
                      <span className="text-gray-400">{item.committed_monthly_qty} units</span>
                    </div>
                    <span className="font-semibold">₹{Number(item.locked_unit_price).toLocaleString('en-IN')}/unit</span>
                  </div>
                ))}
                {agreement.items.length > 3 && (
                  <p className="text-xs text-gray-400">+{agreement.items.length - 3} more items</p>
                )}
              </div>

              <div className="flex gap-3 mt-4 pt-4 border-t border-surface-border">
                <Link
                  href={`/dashboard/customer/agreements/${agreement.id}`}
                  className="flex items-center gap-1 text-sm font-medium text-accent hover:underline"
                >
                  {agreement.status === 'draft' ? 'Edit Contract' : 'View Details'}
                  <ArrowRight className="w-4 h-4" />
                </Link>
                {agreement.price_ceiling_agreed && (
                  <span className="flex items-center gap-1 text-xs text-gray-400">
                    <TrendingDown className="w-3 h-3" />
                    {agreement.price_ceiling_agreed}% price ceiling
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}