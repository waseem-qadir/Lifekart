import { Building2, TrendingDown, Users } from 'lucide-react'
import FadeIn from '@/components/ui/FadeIn'
import { apiClient } from '@/lib/api'

interface LandingStats {
  advertised_avg_monthly_savings: number
  total_active_households: number
  total_lifetime_contracts: number
  total_corporate_partners: number
}

async function getLandingStats(): Promise<LandingStats | null> {
  try {
    return await apiClient('/analytics/public/landing-stats', { cache: 'no-store' })
  } catch {
    return null
  }
}

function formatNumber(n: number): string {
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k+`
  return `${n.toLocaleString('en-IN')}+`
}

const icons = [Users, TrendingDown, Building2]

export default async function Stats() {
  const stats = await getLandingStats()

  const displayStats = stats
    ? [
        {
          label: 'Active Households',
          value: formatNumber(stats.total_active_households),
          sublabel: 'across 28 cities',
        },
        {
          label: 'Avg Monthly Savings',
          value: `₹${Number(stats.advertised_avg_monthly_savings).toLocaleString('en-IN')}`,
          sublabel: 'per household',
        },
        {
          label: 'Corporate Partners',
          value: `${stats.total_corporate_partners}+`,
          sublabel: 'employers onboard',
        },
      ]
    : [
        { label: 'Active Households', value: '12,400+', sublabel: 'across 28 cities' },
        { label: 'Avg Monthly Savings', value: '₹3,200', sublabel: 'per household' },
        { label: 'Corporate Partners', value: '140+', sublabel: 'employers onboard' },
      ]

  return (
    <section id="business" className="bg-accent">
      <div className="max-w-7xl mx-auto px-6 py-20">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {displayStats.map((stat, i) => {
            const Icon = icons[i]
            return (
              <FadeIn key={stat.label} delay={i * 0.1}>
                <div className="text-center space-y-3">
                  <Icon className="w-8 h-8 text-white/60 mx-auto" strokeWidth={1.5} />
                  <div className="text-4xl md:text-5xl font-display font-extrabold text-white">
                    {stat.value}
                  </div>
                  <div className="text-sm font-bold uppercase tracking-wider text-white/80">
                    {stat.label}
                  </div>
                  <div className="text-xs text-white/50">
                    {stat.sublabel}
                  </div>
                </div>
              </FadeIn>
            )
          })}
        </div>
      </div>
    </section>
  )
}
