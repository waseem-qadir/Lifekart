'use client'

import { apiClient } from '@/lib/api'
import { useEffect, useState } from 'react'
import { FileText, Download, IndianRupee } from 'lucide-react'

interface Invoice {
  id: string
  amount_total: number
  amount_paid: number
  status: string
  issued_at: string
  billing_period_start: string
  billing_period_end: string
}

export default function InvoicesPage() {
  const [invoices, setInvoices] = useState<Invoice[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const data = await apiClient('/payments/invoices').catch(() => [])
        setInvoices(Array.isArray(data) ? data : [])
      } catch {} finally { setLoading(false) }
    }
    load()
  }, [])

  if (loading) {
    return (
      <div className="space-y-4 animate-pulse">
        <div className="h-8 bg-gray-200 rounded w-48" />
        {[1,2,3].map(i => <div key={i} className="h-20 bg-gray-100 rounded-2xl" />)}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl md:text-4xl font-display font-extrabold uppercase tracking-tighter">Invoices</h1>

      {invoices.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-2xl shadow-card">
          <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500 font-bold uppercase tracking-wider">No invoices yet</p>
          <p className="text-sm text-gray-400 mt-1">Invoices are generated monthly</p>
        </div>
      ) : (
        <div className="space-y-3">
          {invoices.map((inv) => (
            <div key={inv.id} className="bg-white rounded-2xl p-5 shadow-card flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                  inv.status === 'paid' ? 'bg-green-50 text-green-600' :
                  inv.status === 'draft' ? 'bg-gray-100 text-gray-400' :
                  'bg-red-50 text-red-500'
                }`}>
                  <FileText className="w-5 h-5" />
                </div>
                <div>
                  <p className="text-sm font-semibold">
                    {new Date(inv.billing_period_start).toLocaleDateString('en-IN', { month: 'long', year: 'numeric' })}
                  </p>
                  <p className="text-xs text-gray-400">
                    {new Date(inv.billing_period_start).toLocaleDateString('en-IN')} — {new Date(inv.billing_period_end).toLocaleDateString('en-IN')}
                  </p>
                </div>
              </div>
              <div className="text-right">
                <div className="text-lg font-display font-extrabold">
                  ₹{Number(inv.amount_total).toLocaleString('en-IN')}
                </div>
                <span className={`text-xs font-bold uppercase ${
                  inv.status === 'paid' ? 'text-green-600' : 'text-gray-400'
                }`}>
                  {inv.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}