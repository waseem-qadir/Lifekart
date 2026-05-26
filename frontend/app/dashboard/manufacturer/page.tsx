'use client'

import { useAuth } from '@/lib/auth'
import { apiClient, getStoredTokens } from '@/lib/api'
import { useEffect, useState } from 'react'
import { Package, TrendingUp, Users, ShoppingBag, ArrowRight, Plus } from 'lucide-react'
import Link from 'next/link'

export default function ManufacturerDashboard() {
  const { user } = useAuth()
  const [products, setProducts] = useState<any[]>([])
  const [manufacturer, setManufacturer] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const [profile, productList] = await Promise.all([
          apiClient('/catalog/manufacturers/me').catch(() => null),
          apiClient('/catalog/products?limit=10').catch(() => []),
        ])
        setManufacturer(profile)
        setProducts(Array.isArray(productList) ? productList : [])
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
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl md:text-4xl font-display font-extrabold uppercase tracking-tighter">
          {manufacturer?.company_name || 'Manufacturer Dashboard'}
        </h1>
        <p className="text-gray-500 mt-1">
          {manufacturer?.is_verified ? 'Verified manufacturer' : 'Pending verification'}
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-2xl p-6 shadow-card">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-bold uppercase tracking-wider text-gray-400">Products</span>
            <Package className="w-6 h-6 text-accent/60" />
          </div>
          <div className="text-3xl font-display font-extrabold">{products.length}</div>
          <p className="text-xs text-gray-400 mt-1">Active listings</p>
        </div>

        <div className="bg-white rounded-2xl p-6 shadow-card">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-bold uppercase tracking-wider text-gray-400">Status</span>
            <TrendingUp className="w-6 h-6 text-accent/60" />
          </div>
          <div className={`text-lg font-display font-bold ${manufacturer?.is_verified ? 'text-green-600' : 'text-red-500'}`}>
            {manufacturer?.is_verified ? 'Verified' : 'Pending'}
          </div>
          <p className="text-xs text-gray-400 mt-1">Verification status</p>
        </div>

        <div className="bg-white rounded-2xl p-6 shadow-card">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-bold uppercase tracking-wider text-gray-400">GSTIN</span>
            <Users className="w-6 h-6 text-accent/60" />
          </div>
          <div className="text-lg font-display font-bold truncate">
            {manufacturer?.gstin || 'Not set'}
          </div>
          <p className="text-xs text-gray-400 mt-1">Tax identifier</p>
        </div>
      </div>

      <div className="bg-white rounded-2xl p-6 shadow-card">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-xl font-display font-bold uppercase tracking-tight">Recent Products</h3>
          <Link
            href="/dashboard/manufacturer/products"
            className="text-sm font-bold text-accent inline-flex items-center gap-1
                       hover:-translate-y-0.5 transition-all"
          >
            Manage <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        {products.length === 0 ? (
          <div className="text-center py-12 text-gray-400">
            <Package className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p className="font-bold uppercase tracking-wider">No products listed</p>
            <Link
              href="/dashboard/manufacturer/products"
              className="inline-flex items-center gap-2 mt-4 px-5 py-2.5 text-sm font-bold
                         text-white bg-accent rounded-lg shadow-button hover:shadow-button-hover
                         hover:-translate-y-0.5 transition-all"
            >
              <Plus className="w-4 h-4" />
              Add Product
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {products.slice(0, 5).map((product: any) => (
              <div
                key={product.id}
                className="flex items-center justify-between py-3 border-b border-surface-border last:border-0"
              >
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 bg-surface-muted rounded-lg flex items-center justify-center">
                    <Package className="w-5 h-5 text-gray-400" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold">{product.name}</p>
                    <p className="text-xs text-gray-400">{product.sku}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-display font-bold">₹{Number(product.unit_price_wholesale).toLocaleString('en-IN')}</p>
                  <p className="text-xs text-gray-400">{product.stock_quantity} in stock</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}