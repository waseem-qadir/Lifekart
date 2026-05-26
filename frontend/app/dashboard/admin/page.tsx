'use client'

import { useAuth } from '@/lib/auth'
import { apiClient } from '@/lib/api'
import { useEffect, useState } from 'react'
import { Users, Building2, Package, TrendingUp, Shield, ArrowRight } from 'lucide-react'
import Link from 'next/link'

export default function AdminDashboard() {
  const { user } = useAuth()
  const [stats, setStats] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const [landingStats] = await Promise.all([
          apiClient('/analytics/public/landing-stats').catch(() => null),
        ])
        setStats(landingStats)
      } catch {} finally { setLoading(false) }
    }
    load()
  }, [])

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-8 bg-gray-200 rounded w-48" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => <div key={i} className="h-32 bg-gray-100 rounded-2xl" />)}
        </div>
      </div>
    )
  }

  const statCards = [
    { label: 'Active Households', value: stats?.total_active_households?.toLocaleString('en-IN') || '—', icon: <Users className="w-6 h-6" />, href: '/dashboard/admin/users' },
    { label: 'Corporate Partners', value: stats?.total_corporate_partners || '—', icon: <Building2 className="w-6 h-6" />, href: '/dashboard/admin/partners' },
    { label: 'Lifetime Contracts', value: stats?.total_lifetime_contracts?.toLocaleString('en-IN') || '—', icon: <Shield className="w-6 h-6" />, href: '/dashboard/admin/analytics' },
    { label: 'Avg Monthly Saved', value: stats ? `₹${Number(stats.advertised_avg_monthly_savings).toLocaleString('en-IN')}` : '—', icon: <TrendingUp className="w-6 h-6" />, href: '/dashboard/admin/analytics' },
  ]

  const quickLinks = [
    { label: 'Manage Users', desc: 'View, activate, and deactivate user accounts', icon: <Users className="w-5 h-5" />, href: '/dashboard/admin/users' },
    { label: 'Approve Partners', desc: 'Review and approve corporate partnership requests', icon: <Building2 className="w-5 h-5" />, href: '/dashboard/admin/partners' },
    { label: 'Manage Catalogue', desc: 'Create and update product categories', icon: <Package className="w-5 h-5" />, href: '/dashboard/admin/catalogue' },
    { label: 'Platform Analytics', desc: 'View platform savings and growth metrics', icon: <TrendingUp className="w-5 h-5" />, href: '/dashboard/admin/analytics' },
  ]

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl md:text-4xl font-display font-extrabold uppercase tracking-tighter">
          Admin Dashboard
        </h1>
        <p className="text-gray-500 mt-1">Platform overview and management</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((stat) => (
          <Link
            key={stat.label}
            href={stat.href}
            className="group bg-white rounded-2xl p-6 shadow-card hover:shadow-card-hover
                       hover:-translate-y-1 transition-all duration-200"
          >
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-bold uppercase tracking-wider text-gray-400">{stat.label}</span>
              <div className="text-accent/60 group-hover:text-accent transition-colors">{stat.icon}</div>
            </div>
            <div className="text-3xl font-display font-extrabold">{stat.value}</div>
          </Link>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {quickLinks.map((link) => (
          <Link
            key={link.label}
            href={link.href}
            className="group bg-white rounded-2xl p-6 shadow-card hover:shadow-card-hover
                       hover:-translate-y-1 transition-all duration-200"
          >
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-accent/10 rounded-xl flex items-center justify-center
                              text-accent group-hover:bg-accent group-hover:text-white transition-all">
                {link.icon}
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-display font-bold uppercase tracking-tight">{link.label}</h3>
                <p className="text-sm text-gray-500">{link.desc}</p>
              </div>
              <ArrowRight className="w-5 h-5 text-gray-300 group-hover:text-accent transition-colors" strokeWidth={2} />
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
}