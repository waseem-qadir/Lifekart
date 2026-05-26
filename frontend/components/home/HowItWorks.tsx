'use client'

import { FileSignature, Truck, ShieldCheck, Repeat } from 'lucide-react'
import FadeIn from '@/components/ui/FadeIn'

const steps = [
  {
    icon: FileSignature,
    title: 'Sign a 60-Year Contract',
    description: 'Pick your essentials and lock in the wholesale price today. No annual renegotiation, no price hikes.',
  },
  {
    icon: Truck,
    title: 'Automated Deliveries',
    description: 'Our AI scheduler calculates exactly what you need and when. Right quantity, right time, every time.',
  },
  {
    icon: ShieldCheck,
    title: 'Price Protected Forever',
    description: 'Market prices may fluctuate, but your contract price is fixed. Manufacturers eat the inflation, not you.',
  },
  {
    icon: Repeat,
    title: 'Auto-Substitutions',
    description: 'If a product goes out of stock or gets discontinued, our engine auto-finds the nearest equivalent at the same price.',
  },
]

export default function HowItWorks() {
  return (
    <section id="how-it-works" className="bg-white">
      <div className="max-w-7xl mx-auto px-6 py-24">
        <FadeIn>
          <div className="text-center mb-16 space-y-4">
            <h2 className="text-4xl md:text-6xl font-display font-extrabold uppercase tracking-tighter">
              How It
              <span className="text-accent"> Works</span>
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Four steps. Zero middlemen. Maximum savings for 60 years.
            </p>
          </div>
        </FadeIn>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {steps.map((step, i) => (
            <FadeIn key={step.title} delay={i * 0.1}>
              <div className="group text-center space-y-4">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl
                                bg-accent-light group-hover:bg-accent transition-colors duration-200
                                shadow-card group-hover:shadow-card-hover group-hover:-translate-y-1">
                  <step.icon className="w-7 h-7 text-accent group-hover:text-white transition-colors duration-200" strokeWidth={2} />
                </div>
                <h3 className="text-base font-display font-bold uppercase tracking-tight leading-tight">
                  {step.title}
                </h3>
                <p className="text-sm text-gray-500 leading-relaxed">
                  {step.description}
                </p>
              </div>
            </FadeIn>
          ))}
        </div>
      </div>
    </section>
  )
}
