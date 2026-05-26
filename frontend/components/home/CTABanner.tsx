'use client'

import Link from 'next/link'
import { ArrowRight } from 'lucide-react'
import FadeIn from '@/components/ui/FadeIn'

export default function CTABanner() {
  return (
    <section className="bg-white">
      <div className="max-w-7xl mx-auto px-6 py-24">
        <FadeIn>
          <div className="relative rounded-3xl bg-black overflow-hidden shadow-float-xl">
            <div className="absolute inset-0 opacity-10">
              <div className="absolute -top-24 -right-24 w-96 h-96 bg-accent rounded-full blur-3xl" />
              <div className="absolute -bottom-24 -left-24 w-96 h-96 bg-accent rounded-full blur-3xl" />
            </div>
            <div className="relative px-8 py-16 md:px-16 md:py-24 text-center space-y-6">
              <h2 className="text-3xl md:text-5xl font-display font-extrabold uppercase tracking-tighter text-white">
                Ready to lock in
                <br />
                <span className="text-accent">lifetime savings?</span>
              </h2>
              <p className="text-gray-400 text-lg max-w-xl mx-auto">
                Join 12,400+ households already saving an average of INR 3,200 every month.
              </p>
              <Link
                href="/register"
                className="inline-flex items-center gap-2 px-8 py-4 text-sm font-bold text-white
                           bg-accent rounded-md shadow-button hover:shadow-button-hover
                           hover:-translate-y-0.5 transition-all duration-200"
              >
                Start Your 60-Year Contract
                <ArrowRight className="w-4 h-4" strokeWidth={2.5} />
              </Link>
            </div>
          </div>
        </FadeIn>
      </div>
    </section>
  )
}
