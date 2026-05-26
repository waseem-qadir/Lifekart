'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useAuth } from '@/lib/auth'
import { Menu, X, ShoppingCart, Package, LayoutDashboard, LogOut, User } from 'lucide-react'
import { navLinks } from '@/lib/data'

export default function Navbar() {
  const [open, setOpen] = useState(false)
  const { user, isLoading, logout } = useAuth()

  const roleDashboardUrl = user
    ? user.role === 'customer' ? '/dashboard/customer'
    : user.role === 'manufacturer' ? '/dashboard/manufacturer'
    : user.role === 'corporate_admin' ? '/dashboard/corporate'
    : '/dashboard/admin'
    : '/dashboard'

  return (
    <header className="sticky top-0 z-50 bg-white border-b border-surface-border">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 group">
          <Package className="w-6 h-6 text-accent" strokeWidth={2.5} />
          <span className="font-display font-extrabold text-lg tracking-tight">
            LIFE<span className="text-accent">KART</span>
          </span>
        </Link>

        <nav className="hidden md:flex items-center gap-8">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="text-sm font-medium text-gray-600 hover:text-black transition-colors"
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <div className="hidden md:flex items-center gap-4">
          {isLoading ? (
            <div className="w-20 h-9 bg-surface-muted rounded-lg animate-pulse" />
          ) : user ? (
            <>
              <Link
                href={roleDashboardUrl}
                className="flex items-center gap-2 px-4 py-2 text-sm font-semibold text-gray-700
                           hover:bg-surface-muted rounded-lg transition-colors"
              >
                <LayoutDashboard className="w-4 h-4" />
                Dashboard
              </Link>
              <button
                onClick={logout}
                className="flex items-center gap-2 px-4 py-2 text-sm font-semibold text-gray-500
                           hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
              >
                <LogOut className="w-4 h-4" />
                Sign Out
              </button>
            </>
          ) : (
            <>
              <Link
                href="/login"
                className="text-sm font-semibold text-gray-700 hover:text-black transition-colors"
              >
                Sign In
              </Link>
              <Link
                href="/register"
                className="px-5 py-2.5 text-sm font-bold text-white bg-accent rounded-md
                           shadow-button hover:shadow-button-hover hover:-translate-y-0.5
                           transition-all duration-200"
              >
                Get Started
              </Link>
            </>
          )}
        </div>

        <button
          className="md:hidden p-2"
          onClick={() => setOpen(!open)}
          aria-label="Toggle menu"
        >
          {open ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {open && (
        <div className="md:hidden bg-white border-t border-surface-border px-6 py-4 space-y-4">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="block text-sm font-medium text-gray-600 hover:text-black"
              onClick={() => setOpen(false)}
            >
              {link.label}
            </Link>
          ))}
          <div className="pt-4 border-t border-surface-border flex flex-col gap-3">
            {isLoading ? (
              <div className="w-full h-9 bg-surface-muted rounded-lg animate-pulse" />
            ) : user ? (
              <>
                <Link
                  href={roleDashboardUrl}
                  className="flex items-center gap-2 text-sm font-semibold text-gray-700"
                  onClick={() => setOpen(false)}
                >
                  <LayoutDashboard className="w-4 h-4" /> Dashboard
                </Link>
                <button
                  onClick={() => { logout(); setOpen(false) }}
                  className="flex items-center gap-2 text-sm font-semibold text-gray-500"
                >
                  <LogOut className="w-4 h-4" /> Sign Out
                </button>
              </>
            ) : (
              <>
                <Link href="/login" className="text-sm font-semibold text-gray-700" onClick={() => setOpen(false)}>
                  Sign In
                </Link>
                <Link
                  href="/register"
                  className="px-5 py-2.5 text-sm font-bold text-white bg-accent rounded-md text-center shadow-button"
                  onClick={() => setOpen(false)}
                >
                  Get Started
                </Link>
              </>
            )}
          </div>
        </div>
      )}
    </header>
  )
}