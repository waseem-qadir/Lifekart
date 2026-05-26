'use client'

import { useAuth } from '@/lib/auth'
import { apiClient } from '@/lib/api'
import { useEffect, useState } from 'react'
import {
  ShoppingBag, Truck, FileText, TrendingDown, Users, Calendar,
  ArrowRight, ShieldCheck, Plus, Home, Handshake
} from 'lucide-react'
import Link from 'next/link'

interface SavingsData { total_saved: number; current_month_savings: number }
interface Subscription { id: string; product: { name: string }; status: string }
interface StatCard { label: string; value: string; icon: React.ReactNode; href: string }

export default function CustomerDashboard() {
  const { user } = useAuth()
  const [savings, setSavings] = useState<SavingsData | null>(null)
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([])
  const [hasHousehold, setHasHousehold] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const [savingsData, subs, household] = await Promise.all([
          apiClient('/auth/me/savings').catch(() => null),
          apiClient('/subscriptions/?status=active').catch(() => []),
          apiClient('/profiling/households/me').catch(() => null),
        ])
        setSavings(savingsData)
        setSubscriptions(Array.isArray(subs) ? subs : [])
        setHasHousehold(!!household)
      } catch {} finally { setLoading(false) }
    }
    load()
  }, [])

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-8 bg-gray-200 rounded w-48" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => <div key={i} className="h-32 bg-gray-100 rounded-2xl" />)}
        </div>
        <div className="h-64 bg-gray-100 rounded-2xl" />
      </div>
    )
  }

  const stats: StatCard[] = [
    {
      label: 'Monthly Savings',
      value: `₹${Number(savings?.current_month_savings || 0).toLocaleString('en-IN')}`,
      icon: <TrendingDown className="w-6 h-6" />,
      href: '/dashboard/customer/invoices',
    },
    {
      label: 'Active Subscriptions',
      value: `${subscriptions.length}`,
      icon: <ShoppingBag className="w-6 h-6" />,
      href: '/dashboard/customer/subscriptions',
    },
    {
      label: 'Total Saved',
      value: `₹${Number(savings?.total_saved || 0).toLocaleString('en-IN')}`,
      icon: <ShieldCheck className="w-6 h-6" />,
      href: '/dashboard/customer/invoices',
    },
  ]

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl md:text-4xl font-display font-extrabold uppercase tracking-tighter">
          Welcome back, {user?.full_name?.split(' ')[0]}
        </h1>
        <p className="text-gray-500 mt-1">Your lifetime savings at a glance.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {stats.map((stat) => (
          <Link
            key={stat.label}
            href={stat.href}
            className="group bg-white rounded-2xl p-6 shadow-card hover:shadow-card-hover
                       hover:-translate-y-1 transition-all duration-200"
          >
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-bold uppercase tracking-wider text-gray-400">
                {stat.label}
              </span>
              <div className="text-accent/60 group-hover:text-accent transition-colors">
                {stat.icon}
              </div>
            </div>
            <div className="text-3xl font-display font-extrabold">{stat.value}</div>
          </Link>
        ))}
      </div>

      {!hasHousehold && (
        <Link
          href="/dashboard/customer/household"
          className="block bg-accent/10 border border-accent/20 rounded-2xl p-6
                     hover:bg-accent/15 transition-colors"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-accent rounded-xl flex items-center justify-center">
                <Home className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="text-lg font-display font-bold uppercase tracking-tight">
                  Set Up Your Household
                </h3>
                <p className="text-sm text-gray-500">Add family members to unlock personalized subscriptions and savings.</p>
              </div>
            </div>
            <ArrowRight className="w-5 h-5 text-accent" strokeWidth={2.5} />
          </div>
        </Link>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Link
          href="/#categories"
          className="group bg-white rounded-2xl p-6 shadow-card hover:shadow-card-hover
                     hover:-translate-y-1 transition-all duration-200"
        >
          <div className="flex items-center gap-3 mb-3">
            <ShoppingBag className="w-5 h-5 text-accent" />
            <h3 className="text-lg font-display font-bold uppercase tracking-tight">
              Browse Categories
            </h3>
          </div>
          <p className="text-sm text-gray-500 mb-4">Explore 78 product categories and lock in wholesale prices.</p>
          <span className="text-sm font-bold text-accent inline-flex items-center gap-1">
            Shop Now <ArrowRight className="w-4 h-4" />
          </span>
        </Link>

        <Link
          href="/dashboard/customer/agreements"
          className="group bg-white rounded-2xl p-6 shadow-card hover:shadow-card-hover
                     hover:-translate-y-1 transition-all duration-200"
        >
          <div className="flex items-center gap-3 mb-3">
            <Handshake className="w-5 h-5 text-accent" />
            <h3 className="text-lg font-display font-bold uppercase tracking-tight">
              My Agreements
            </h3>
          </div>
          <p className="text-sm text-gray-500 mb-4">View and manage your wholesale supply agreements.</p>
          <span className="text-sm font-bold text-accent inline-flex items-center gap-1">
            View <ArrowRight className="w-4 h-4" />
          </span>
        </Link>
      </div>
    </div>
  )
}