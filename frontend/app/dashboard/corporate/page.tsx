'use client'

import { useAuth } from '@/lib/auth'
import { apiClient } from '@/lib/api'
import { useEffect, useState } from 'react'
import { Users, TrendingUp, Building2 } from 'lucide-react'

export default function CorporateDashboard() {
  const { user } = useAuth()
  const [partner, setPartner] = useState<any>(null)
  const [employees, setEmployees] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const [p, emps] = await Promise.all([
          apiClient('/corporate/partners/me').catch(() => null),
          apiClient('/corporate/partners/me/employees').catch(() => []),
        ])
        setPartner(p)
        setEmployees(Array.isArray(emps) ? emps : [])
      } catch {} finally { setLoading(false) }
    }
    load()
  }, [])

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-8 bg-gray-200 rounded w-48" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[1,2,3].map(i => <div key={i} className="h-32 bg-gray-100 rounded-2xl" />)}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl md:text-4xl font-display font-extrabold uppercase tracking-tighter">
          {partner?.company_name || 'Corporate Dashboard'}
        </h1>
        <p className="text-gray-500 mt-1">
          {partner?.partnership_status === 'active' ? 'Active partnership' : 'Pending approval'}
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-2xl p-6 shadow-card">
          <span className="text-xs font-bold uppercase tracking-wider text-gray-400">Employees</span>
          <div className="text-3xl font-display font-extrabold mt-2">{employees.length}</div>
        </div>
        <div className="bg-white rounded-2xl p-6 shadow-card">
          <span className="text-xs font-bold uppercase tracking-wider text-gray-400">Status</span>
          <div className={`text-xl font-display font-bold mt-2 ${partner?.partnership_status === 'active' ? 'text-green-600' : 'text-amber-600'}`}>
            {partner?.partnership_status || 'Unknown'}
          </div>
        </div>
        <div className="bg-white rounded-2xl p-6 shadow-card">
          <span className="text-xs font-bold uppercase tracking-wider text-gray-400">Industry</span>
          <div className="text-xl font-display font-bold mt-2">{partner?.industry || '—'}</div>
        </div>
      </div>
    </div>
  )
}