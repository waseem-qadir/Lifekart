'use client'

import { useState } from 'react'
import Link from 'next/link'
import { ArrowRight, Loader2, Package } from 'lucide-react'
import { useAuth } from '@/lib/auth'

export default function LoginPage() {
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(email, password)
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
            Welcome Back
          </h1>
          <p className="text-gray-500 mt-2">Sign in to manage your lifetime contract.</p>
        </div>

        <form onSubmit={handleSubmit} className="bg-white rounded-2xl p-8 shadow-card space-y-5">
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-gray-500 mb-1.5">
              Email
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-3 border border-surface-border rounded-lg text-sm
                         focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent
                         transition-colors"
              placeholder="priya@example.com"
            />
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-gray-500 mb-1.5">
              Password
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-3 border border-surface-border rounded-lg text-sm
                         focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent
                         transition-colors"
              placeholder="Enter your password"
            />
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
                Sign In
                <ArrowRight className="w-4 h-4" strokeWidth={2.5} />
              </>
            )}
          </button>

          <p className="text-center text-sm text-gray-500">
            Don&apos;t have an account?{' '}
            <Link href="/register" className="font-semibold text-accent hover:underline">
              Create one
            </Link>
          </p>

          <div className="pt-3 border-t border-surface-border">
            <p className="text-xs text-gray-400 text-center">
              Demo credentials: <span className="font-mono text-gray-500">demo-manufacturer@lifekart.com / demo123</span>
            </p>
          </div>
        </form>
      </div>
    </div>
  )
}