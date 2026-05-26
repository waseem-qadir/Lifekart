import Hero from '@/components/home/Hero'
import CategoryGrid from '@/components/home/CategoryGrid'
import HowItWorks from '@/components/home/HowItWorks'
import Stats from '@/components/home/Stats'
import CTABanner from '@/components/home/CTABanner'

export default function HomePage() {
  return (
    <>
      <Hero />
      <CategoryGrid />
      <HowItWorks />
      <Stats />
      <CTABanner />
    </>
  )
}
