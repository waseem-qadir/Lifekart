'use client'

import Link from 'next/link'
import { ArrowRight, ShieldCheck } from 'lucide-react'
import { motion } from 'framer-motion'
import FadeIn from '@/components/ui/FadeIn'

export default function Hero() {
  return (
    <section className="relative overflow-hidden bg-surface">
      <div className="max-w-7xl mx-auto px-6 pt-24 pb-20 md:pt-32 md:pb-28">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          <div className="space-y-8">
            <FadeIn delay={0}>
              <h1 className="text-5xl md:text-7xl lg:text-8xl font-display font-extrabold uppercase tracking-tighter leading-[0.9]">
                Lock In
                <br />
                <span className="text-accent">Wholesale</span>
                <br />
                For Life
              </h1>
            </FadeIn>

            <FadeIn delay={0.15}>
              <p className="text-lg md:text-xl text-gray-600 font-body max-w-lg leading-relaxed">
                Sign a 60-year contract today. Pay manufacturer prices forever.
                Essentials delivered to your doorstep, never at retail markup again.
              </p>
            </FadeIn>

            <FadeIn delay={0.25}>
              <div className="flex flex-col sm:flex-row gap-4">
                <Link
                  href="/register"
                  className="inline-flex items-center justify-center gap-2 px-8 py-4
                             text-sm font-bold text-white bg-accent rounded-md
                             shadow-button hover:shadow-button-hover hover:-translate-y-0.5
                             transition-all duration-200"
                >
                  Start Saving Now
                  <ArrowRight className="w-4 h-4" strokeWidth={2.5} />
                </Link>
                <Link
                  href="#how-it-works"
                  className="inline-flex items-center justify-center gap-2 px-8 py-4
                             text-sm font-bold text-black bg-white border border-surface-border rounded-md
                             shadow-card hover:shadow-card-hover hover:-translate-y-0.5
                             transition-all duration-200"
                >
                  How It Works
                </Link>
              </div>
            </FadeIn>

            <FadeIn delay={0.35}>
              <div className="flex items-center gap-6 text-sm text-gray-500 font-medium">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-accent" strokeWidth={2.5} />
                  Price Protected
                </div>
                <span className="text-gray-300">|</span>
                <span>60-Year Contracts</span>
                <span className="text-gray-300">|</span>
                <span>Free Delivery</span>
              </div>
            </FadeIn>
          </div>

          <FadeIn delay={0.2} direction="none">
            <div className="relative">
              <div className="relative rounded-2xl overflow-hidden shadow-float-lg">
                <img
                  src="https://images.unsplash.com/photo-1542838132-92c53300491e?w=800&q=80"
                  alt="Wholesale grocery warehouse shelves"
                  className="w-full h-[400px] lg:h-[500px] object-cover"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent" />
              </div>
            </div>
          </FadeIn>
        </div>
      </div>
    </section>
  )
}
