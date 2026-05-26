import { Metadata } from 'next'
import Link from 'next/link'
import { ArrowLeft, ShoppingBag, Tag, TrendingDown } from 'lucide-react'
import { apiClient } from '@/lib/api'
import ProductCard from '@/components/ui/ProductCard'

interface Category {
  id: string
  name: string
  slug: string
  description: string | null
  image_url: string | null
  product_count: number
  avg_savings: string | null
  icon: string | null
  unit_type: string | null
}

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
  min_order_quantity: number
  max_order_quantity: number | null
  stock_quantity: number
  is_active: boolean
}

async function getCategory(slug: string): Promise<Category | null> {
  try {
    return await apiClient(`/catalog/categories/slug/${slug}`, { cache: 'no-store' })
  } catch {
    return null
  }
}

async function getProducts(categoryId: string): Promise<Product[]> {
  try {
    return await apiClient(`/catalog/products?category_id=${categoryId}&limit=50`, { cache: 'no-store' })
  } catch {
    return []
  }
}

export async function generateMetadata({ params }: { params: { slug: string } }): Promise<Metadata> {
  const category = await getCategory(params.slug)
  if (!category) return { title: 'Category Not Found - LifeKart' }
  return {
    title: `${category.name} - LifeKart`,
    description: category.description || `Browse ${category.name} at wholesale prices`,
  }
}

export default async function CategoryPage({ params }: { params: { slug: string } }) {
  const category = await getCategory(params.slug)

  if (!category) {
    return (
      <div className="max-w-7xl mx-auto px-6 py-32 text-center">
        <h2 className="text-4xl font-display font-extrabold uppercase tracking-tighter mb-4">
          Category Not Found
        </h2>
        <p className="text-gray-500 mb-8">The category you are looking for does not exist.</p>
        <Link
          href="/"
          className="inline-flex items-center gap-2 px-6 py-3 text-sm font-bold text-white bg-accent rounded-md
                     shadow-button hover:shadow-button-hover hover:-translate-y-0.5 transition-all duration-200"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Home
        </Link>
      </div>
    )
  }

  const products = await getProducts(category.id)

  const avgSavingsPercent = category.avg_savings || '30%'
  const heroImage =
    category.image_url || 'https://images.unsplash.com/photo-1542838132-92c53300491e?w=1200&q=80'

  return (
    <main>
      <section className="relative bg-surface-muted overflow-hidden">
        <div className="max-w-7xl mx-auto px-6 pt-20 pb-16 md:pt-28 md:pb-20">
          <Link
            href="/#categories"
            className="inline-flex items-center gap-2 text-sm font-medium text-gray-500 hover:text-accent
                       transition-colors mb-8"
          >
            <ArrowLeft className="w-4 h-4" />
            All Categories
          </Link>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div className="space-y-6">
              <h1 className="text-4xl md:text-6xl lg:text-7xl font-display font-extrabold uppercase tracking-tighter leading-[0.95]">
                {category.name}
              </h1>

              <p className="text-lg text-gray-600 leading-relaxed max-w-lg">
                {category.description || `Premium ${category.name.toLowerCase()} at manufacturer-direct wholesale prices.`}
              </p>

              <div className="flex flex-wrap gap-4">
                <div className="flex items-center gap-2 bg-white rounded-lg px-4 py-3 shadow-card">
                  <ShoppingBag className="w-5 h-5 text-accent" />
                  <div>
                    <div className="text-lg font-display font-bold">{category.product_count}</div>
                    <div className="text-xs text-gray-500 uppercase tracking-wider">Products</div>
                  </div>
                </div>

                <div className="flex items-center gap-2 bg-white rounded-lg px-4 py-3 shadow-card">
                  <TrendingDown className="w-5 h-5 text-accent" />
                  <div>
                    <div className="text-lg font-display font-bold">{avgSavingsPercent} off</div>
                    <div className="text-xs text-gray-500 uppercase tracking-wider">Retail</div>
                  </div>
                </div>
              </div>

              {category.unit_type && (
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <Tag className="w-4 h-4" />
                  Unit: {category.unit_type}
                </div>
              )}
            </div>

            <div className="relative">
              <div className="relative rounded-2xl overflow-hidden shadow-float-lg">
                <img
                  src={heroImage}
                  alt={category.name}
                  className="w-full h-[300px] md:h-[400px] object-cover"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent" />
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="bg-surface">
        <div className="max-w-7xl mx-auto px-6 py-16">
          <div className="flex items-center justify-between mb-10">
            <h2 className="text-3xl md:text-4xl font-display font-extrabold uppercase tracking-tighter">
              All Products
            </h2>
            <span className="text-sm text-gray-500 font-medium">
              {products.length} item{products.length !== 1 ? 's' : ''}
            </span>
          </div>

          {products.length === 0 ? (
            <div className="text-center p-16 border-2 border-dashed border-gray-300 rounded-2xl">
              <ShoppingBag className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500 font-bold uppercase tracking-wider">
                No products in this category yet
              </p>
              <p className="text-sm text-gray-400 mt-1">
                Manufacturers are adding inventory soon
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {products.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
          )}
        </div>
      </section>
    </main>
  )
}