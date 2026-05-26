'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { ShoppingBag, ShieldCheck, Plus } from 'lucide-react'
import AddToContractModal from '@/components/ui/AddToContractModal'

interface Product {
  id: string
  category_id: string
  manufacturer_id: string
  name: string
  sku: string
  image_url: string | null
  unit_size: string | null
  unit_price_wholesale: number
  unit_price_retail: number
  stock_quantity: number
}

interface Props {
  product: Product
}

export default function ProductCard({ product }: Props) {
  const [showModal, setShowModal] = useState(false)
  const router = useRouter()

  const savings = product.unit_price_retail > 0
    ? Math.round(
        ((product.unit_price_retail - product.unit_price_wholesale) /
          product.unit_price_retail) *
          100
      )
    : 0

  function handleContractCreated(agreementId: string) {
    setShowModal(false)
    router.push(`/dashboard/customer/agreements/${agreementId}`)
  }

  return (
    <>
      <div
        className="group bg-white rounded-2xl overflow-hidden shadow-card hover:shadow-card-hover
                   hover:-translate-y-1 transition-all duration-300"
      >
        <div className="relative h-48 overflow-hidden bg-surface-muted">
          {product.image_url ? (
            <img
              src={product.image_url}
              alt={product.name}
              className="w-full h-full object-cover transition-transform duration-500
                         group-hover:scale-110"
              loading="lazy"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <ShoppingBag className="w-12 h-12 text-gray-300" />
            </div>
          )}

          {savings > 0 && (
            <div className="absolute top-3 left-3">
              <span className="inline-block bg-black text-white rounded-md px-3 py-1
                               text-xs font-bold uppercase tracking-wider shadow-badge">
                Save {savings}%
              </span>
            </div>
          )}
        </div>

        <div className="p-5 space-y-3">
          <h3 className="text-base font-display font-bold uppercase tracking-tight leading-tight line-clamp-2">
            {product.name}
          </h3>

          {product.unit_size && (
            <p className="text-xs text-gray-400 uppercase tracking-wider">
              {product.unit_size}
            </p>
          )}

          <div className="flex items-end justify-between pt-2">
            <div>
              <div className="text-2xl font-display font-extrabold">
                ₹{Number(product.unit_price_wholesale).toLocaleString('en-IN')}
              </div>
              {product.unit_price_retail > product.unit_price_wholesale && (
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="text-xs text-gray-400 line-through">
                    ₹{Number(product.unit_price_retail).toLocaleString('en-IN')}
                  </span>
                  <span className="text-xs font-semibold text-green-600">
                    {savings}% off
                  </span>
                </div>
              )}
            </div>

            {product.stock_quantity > 0 ? (
              <span className="text-xs font-medium text-green-600 flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5" />
                In Stock
              </span>
            ) : (
              <span className="text-xs font-medium text-gray-400">Out of Stock</span>
            )}
          </div>

          <button
            onClick={() => setShowModal(true)}
            className="w-full flex items-center justify-center gap-2 mt-2 px-4 py-2.5 text-xs font-bold
                       text-white bg-accent rounded-lg shadow-button hover:shadow-button-hover
                       hover:-translate-y-0.5 transition-all duration-200"
          >
            <Plus className="w-4 h-4" />
            Add to Contract
          </button>
        </div>
      </div>

      {showModal && (
        <AddToContractModal
          product={product}
          onClose={() => setShowModal(false)}
          onCreated={handleContractCreated}
        />
      )}
    </>
  )
}