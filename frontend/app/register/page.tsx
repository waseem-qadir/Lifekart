'use client'

import { useState } from 'react'
import Link from 'next/link'
import { ArrowRight, Loader2, ShieldCheck, Package } from 'lucide-react'
import { useAuth } from '@/lib/auth'

export default function RegisterPage() {
  const { register } = useAuth()
  const [form, setForm] = useState({ full_name: '', email: '', phone: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [role, setRole] = useState('customer')

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await register({ ...form, phone: form.phone || undefined, role })
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-[calc(100vh-64px)] bg-surface-muted flex items-center justify-center px-6 py-12">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center gap-2 mb-6">
            <Package className="w-8 h-8 text-accent" strokeWidth={2.5} />
            <span className="font-display font-extrabold text-2xl tracking-tight">
              LIFE<span className="text-accent">KART</span>
            </span>
          </Link>
          <h1 className="text-3xl md:text-4xl font-display font-extrabold uppercase tracking-tighter">
            Create Your Account
          </h1>
          <p className="text-gray-500 mt-2">Lock in wholesale prices for 60 years.</p>
        </div>

        <form onSubmit={handleSubmit} className="bg-white rounded-2xl p-8 shadow-card space-y-5">
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-gray-500 mb-1.5">
              Full Name
            </label>
            <input
              type="text"
              required
              value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              className="w-full px-4 py-3 border border-surface-border rounded-lg text-sm
                         focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent
                         transition-colors"
              placeholder="Priya Sharma"
            />
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-gray-500 mb-1.5">
              Email
            </label>
            <input
              type="email"
              required
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              className="w-full px-4 py-3 border border-surface-border rounded-lg text-sm
                         focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent
                         transition-colors"
              placeholder="priya@example.com"
            />
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-gray-500 mb-1.5">
              Phone
            </label>
            <input
              type="tel"
              value={form.phone}
              onChange={(e) => setForm({ ...form, phone: e.target.value })}
              className="w-full px-4 py-3 border border-surface-border rounded-lg text-sm
                         focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent
                         transition-colors"
              placeholder="+91 9876543210"
            />
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-gray-500 mb-1.5">
              Password
            </label>
            <input
              type="password"
              required
              minLength={8}
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              className="w-full px-4 py-3 border border-surface-border rounded-lg text-sm
                         focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent
                         transition-colors"
              placeholder="Min 8 characters"
            />
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-gray-500 mb-1.5">
              I am a
            </label>
            <div className="grid grid-cols-3 gap-2">
              {[
                { value: 'customer', label: 'Household' },
                { value: 'manufacturer', label: 'Manufacturer' },
                { value: 'corporate_admin', label: 'Corporate' },
              ].map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => setRole(opt.value)}
                  className={`px-4 py-2.5 text-sm font-bold rounded-lg border transition-all ${
                    role === opt.value
                      ? 'bg-accent text-white border-accent shadow-button'
                      : 'bg-white text-gray-600 border-surface-border hover:border-accent'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 px-6 py-3.5 text-sm font-bold
                       text-white bg-accent rounded-lg shadow-button hover:shadow-button-hover
                       hover:-translate-y-0.5 transition-all duration-200 disabled:opacity-50
                       disabled:cursor-not-allowed"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <>
                Create Account
                <ArrowRight className="w-4 h-4" strokeWidth={2.5} />
              </>
            )}
          </button>

          <p className="text-center text-sm text-gray-500">
            Already have an account?{' '}
            <Link href="/login" className="font-semibold text-accent hover:underline">
              Sign In
            </Link>
          </p>

          <div className="flex items-center gap-2 pt-2 text-xs text-gray-400">
            <ShieldCheck className="w-4 h-4" />
            256-bit encrypted. We never share your data.
          </div>
        </form>
      </div>
    </div>
  )
}