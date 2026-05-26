'use client'

import { apiClient } from '@/lib/api'
import { useEffect, useState } from 'react'
import { Truck, CheckCircle, Clock, XCircle, AlertTriangle, Package, Calendar } from 'lucide-react'

interface Delivery {
  id: string
  subscription_id: string
  product_id: string
  scheduled_date: string
  actual_delivery_date: string | null
  status: string
  quantity: number
  unit_price_applied: number
  tracking_number: string | null
  notes: string | null
}

export default function DeliveriesPage() {
  const [deliveries, setDeliveries] = useState<Delivery[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const household = await apiClient('/profiling/households/me').catch(() => null)
        if (household) {
          const data = await apiClient(`/scheduling/deliveries?household_id=${household.id}`).catch(() => [])
          setDeliveries(Array.isArray(data) ? data : [])
        }
      } catch {} finally { setLoading(false) }
    }
    load()
  }, [])

  const statusIcon = (status: string) => {
    switch (status) {
      case 'delivered': return <CheckCircle className="w-5 h-5 text-green-500" />
      case 'pending': return <Clock className="w-5 h-5 text-amber-500" />
      case 'partially_filled': return <AlertTriangle className="w-5 h-5 text-orange-500" />
      case 'in_transit': return <Truck className="w-5 h-5 text-blue-500" />
      case 'failed': return <XCircle className="w-5 h-5 text-red-500" />
      default: return <Package className="w-5 h-5 text-gray-300" />
    }
  }

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
      <h1 className="text-3xl md:text-4xl font-display font-extrabold uppercase tracking-tighter">Deliveries</h1>

      {deliveries.length === 0 ? (
        <div className="bg-white rounded-2xl p-8 shadow-card text-center">
          <Truck className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500 font-bold uppercase tracking-wider">No deliveries yet</p>
          <p className="text-sm text-gray-400 mt-1">Your first delivery will appear once a subscription is active</p>
        </div>
      ) : (
        <div className="space-y-3">
          {deliveries.slice(0, 50).map((d) => (
            <div key={d.id} className="bg-white rounded-2xl p-5 shadow-card flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                  d.status === 'delivered' ? 'bg-green-50' :
                  d.status === 'pending' ? 'bg-amber-50' :
                  d.status === 'in_transit' ? 'bg-blue-50' :
                  d.status === 'failed' ? 'bg-red-50' :
                  'bg-gray-100'
                }`}>
                  {statusIcon(d.status)}
                </div>
                <div>
                  <p className="text-sm font-semibold">{d.product_id?.slice(0, 8)}</p>
                  <p className="text-xs text-gray-400">
                    {d.quantity} units · ₹{Number(d.unit_price_applied).toLocaleString('en-IN')}/unit
                  </p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-xs text-gray-400">
                  <Calendar className="w-3 h-3 inline mr-1" />
                  {new Date(d.scheduled_date).toLocaleDateString('en-IN')}
                </p>
                <span className={`text-xs font-bold uppercase ${
                  d.status === 'delivered' ? 'text-green-600' :
                  d.status === 'pending' ? 'text-amber-600' :
                  d.status === 'failed' ? 'text-red-500' :
                  'text-gray-500'
                }`}>
                  {d.status.replace('_', ' ')}
                </span>
                {d.tracking_number && (
                  <p className="text-xs text-gray-400 mt-0.5">Track: {d.tracking_number}</p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}