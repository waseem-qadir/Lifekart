import Link from 'next/link'
import { ArrowRight, ShoppingBag } from 'lucide-react'
import FadeIn from '@/components/ui/FadeIn'
import { apiClient } from '@/lib/api'

interface Category {
  id: string
  name: string
  slug: string
  description: string | null
  image_url: string | null
  product_count: number
  avg_savings: string | null
}

async function getLiveCategories(): Promise<Category[]> {
  try {
    return await apiClient('/catalog/categories?limit=20', { cache: 'no-store' })
  } catch {
    return []
  }
}

export default async function CategoryGrid() {
  const categories = await getLiveCategories()

  const fallbackImage = (cat: Category) =>
    cat.image_url || 'https://images.unsplash.com/photo-1542838132-92c53300491e?w=800&q=80'

  return (
    <section id="categories" className="bg-surface-muted">
      <div className="max-w-7xl mx-auto px-6 py-24">
        <div className="text-center mb-16 space-y-4">
          <h2 className="text-4xl md:text-6xl font-display font-extrabold uppercase tracking-tighter">
            Explore
            <span className="text-accent"> Categories</span>
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Browse our live wholesale catalog. Prices locked for 60 years.
          </p>
        </div>

        {categories.length === 0 && (
          <div className="text-center p-12 border-2 border-dashed border-gray-300 rounded-2xl">
            <p className="text-gray-500 font-bold uppercase tracking-wider">
              No categories found in database.
            </p>
            <p className="text-sm text-gray-400 mt-1">
              Seed the catalog via <code className="bg-gray-100 px-1 rounded">python scripts/seed_catalog.py</code>
            </p>
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {categories.map((cat, i) => (
            <FadeIn key={cat.id} delay={i * 0.1}>
              <Link
                href={`/categories/${cat.slug}`}
                className="group block relative bg-white rounded-2xl overflow-hidden
                           shadow-card hover:shadow-card-hover hover:-translate-y-1
                           transition-all duration-300"
              >
                <div className="relative h-52 overflow-hidden">
                  <img
                    src={fallbackImage(cat)}
                    alt={cat.name}
                    className="w-full h-full object-cover transition-transform duration-500
                               group-hover:scale-110"
                    loading="lazy"
                  />
                  <div className="absolute top-3 left-3">
                    <span className="inline-block bg-white rounded-md px-3 py-1.5
                                     text-xs font-bold uppercase tracking-wider text-accent
                                     shadow-badge">
                      {cat.avg_savings || '30%'} off retail
                    </span>
                  </div>
                </div>

                <div className="p-5 space-y-2">
                  <div className="flex items-start justify-between">
                    <h3 className="text-lg font-display font-bold uppercase tracking-tight leading-tight">
                      {cat.name}
                    </h3>
                    <ArrowRight className="w-4 h-4 text-gray-400 mt-0.5 group-hover:text-accent
                                            group-hover:translate-x-1 transition-all duration-200" />
                  </div>
                  <p className="text-sm text-gray-500 leading-relaxed line-clamp-2">
                    {cat.description || 'Premium wholesale products at manufacturer prices.'}
                  </p>
                  <div className="flex items-center gap-2 pt-1">
                    <ShoppingBag className="w-3.5 h-3.5 text-gray-400" />
                    <span className="text-xs font-medium text-gray-500">
                      {cat.product_count} products
                    </span>
                  </div>
                </div>
              </Link>
            </FadeIn>
          ))}
        </div>
      </div>
    </section>
  )
}