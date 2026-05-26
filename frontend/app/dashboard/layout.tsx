'use client'

import { useAuth } from '@/lib/auth'
import { useRouter, usePathname } from 'next/navigation'
import { useEffect } from 'react'
import Link from 'next/link'
import {
  Package, ShoppingBag, Truck, FileText, Users, Home, Handshake,
  Building2, TrendingUp, Settings, LogOut, ShieldCheck, CreditCard,
  Gift, HeartPulse, Clock, ChevronRight, LayoutDashboard
} from 'lucide-react'
import { Loader2 } from 'lucide-react'

interface NavItem {
  href: string
  label: string
  icon: React.ReactNode
}

const ROLE_NAV: Record<string, NavItem[]> = {
  customer: [
    { href: '/dashboard/customer', label: 'Overview', icon: <LayoutDashboard className="w-5 h-5" /> },
    { href: '/dashboard/customer/subscriptions', label: 'Subscriptions', icon: <ShoppingBag className="w-5 h-5" /> },
    { href: '/dashboard/customer/deliveries', label: 'Deliveries', icon: <Truck className="w-5 h-5" /> },
    { href: '/dashboard/customer/invoices', label: 'Invoices', icon: <FileText className="w-5 h-5" /> },
    { href: '/dashboard/customer/household', label: 'Household', icon: <Users className="w-5 h-5" /> },
    { href: '/dashboard/customer/agreements', label: 'Agreements', icon: <Handshake className="w-5 h-5" /> },
    { href: '/dashboard/customer/community', label: 'Community', icon: <Building2 className="w-5 h-5" /> },
  ],
  manufacturer: [
    { href: '/dashboard/manufacturer', label: 'Overview', icon: <LayoutDashboard className="w-5 h-5" /> },
    { href: '/dashboard/manufacturer/products', label: 'Products', icon: <Package className="w-5 h-5" /> },
    { href: '/dashboard/manufacturer/catalogue', label: 'Catalogue', icon: <TrendingUp className="w-5 h-5" /> },
  ],
  corporate_admin: [
    { href: '/dashboard/corporate', label: 'Overview', icon: <LayoutDashboard className="w-5 h-5" /> },
    { href: '/dashboard/corporate/employees', label: 'Employees', icon: <Users className="w-5 h-5" /> },
    { href: '/dashboard/corporate/deductions', label: 'Payroll', icon: <CreditCard className="w-5 h-5" /> },
  ],
  superadmin: [
    { href: '/dashboard/admin', label: 'Overview', icon: <LayoutDashboard className="w-5 h-5" /> },
    { href: '/dashboard/admin/users', label: 'Users', icon: <Users className="w-5 h-5" /> },
    { href: '/dashboard/admin/partners', label: 'Partners', icon: <Building2 className="w-5 h-5" /> },
    { href: '/dashboard/admin/catalogue', label: 'Catalogue', icon: <Package className="w-5 h-5" /> },
    { href: '/dashboard/admin/analytics', label: 'Analytics', icon: <TrendingUp className="w-5 h-5" /> },
  ],
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user, isLoading, logout } = useAuth()
  const router = useRouter()
  const pathname = usePathname()

  useEffect(() => {
    if (!isLoading && !user) {
      router.push('/login')
    }
  }, [user, isLoading, router])

  if (isLoading) {
    return (
      <div className="min-h-[calc(100vh-64px)] flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-accent animate-spin" />
      </div>
    )
  }

  if (!user) return null

  const navItems = ROLE_NAV[user.role] || []

  return (
    <div className="flex min-h-[calc(100vh-64px)]">
      <aside className="hidden lg:flex flex-col w-64 bg-white border-r border-surface-border">
        <div className="p-6 border-b border-surface-border">
          <p className="text-xs font-bold uppercase tracking-wider text-gray-400 mb-1">
            {user.role.replace('_', ' ')}
          </p>
          <p className="text-sm font-semibold text-black truncate">{user.full_name}</p>
          <p className="text-xs text-gray-400 truncate">{user.email}</p>
        </div>

        <nav className="flex-1 p-4 space-y-1">
          {navItems.map((item) => {
            const isActive = pathname === item.href || pathname?.startsWith(item.href + '/')
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium
                  transition-all duration-150 ${
                    isActive
                      ? 'bg-accent/10 text-accent'
                      : 'text-gray-600 hover:bg-surface-muted hover:text-black'
                  }`}
              >
                {item.icon}
                {item.label}
                {isActive && <ChevronRight className="w-4 h-4 ml-auto" />}
              </Link>
            )
          })}
        </nav>

        <div className="p-4 border-t border-surface-border space-y-2">
          <button
            onClick={logout}
            className="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm font-medium
                       text-gray-500 hover:bg-red-50 hover:text-red-600 transition-all duration-150"
          >
            <LogOut className="w-5 h-5" />
            Sign Out
          </button>
        </div>
      </aside>

      <div className="flex-1 bg-surface-muted overflow-auto">
        <div className="lg:hidden bg-white border-b border-surface-border px-6 py-3">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-bold uppercase tracking-wider text-accent">
                {user.role.replace('_', ' ')}
              </p>
              <p className="text-sm font-semibold">{user.full_name}</p>
            </div>
            <button onClick={logout} className="text-gray-400 hover:text-red-500">
              <LogOut className="w-5 h-5" />
            </button>
          </div>
          <nav className="flex gap-2 mt-3 overflow-x-auto pb-2">
            {navItems.map((item) => {
              const isActive = pathname === item.href
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-bold
                    whitespace-nowrap transition-all ${
                      isActive
                        ? 'bg-accent text-white'
                        : 'bg-surface-muted text-gray-500 hover:bg-gray-200'
                    }`}
                >
                  {item.label}
                </Link>
              )
            })}
          </nav>
        </div>

        <div className="p-6">{children}</div>
      </div>
    </div>
  )
}