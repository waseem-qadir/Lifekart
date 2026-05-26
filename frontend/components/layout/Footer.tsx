import Link from 'next/link'
import { Package } from 'lucide-react'

export default function Footer() {
  return (
    <footer className="bg-black text-white">
      <div className="max-w-7xl mx-auto px-6 py-16 grid grid-cols-1 md:grid-cols-4 gap-10">
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <Package className="w-5 h-5 text-accent" strokeWidth={2.5} />
            <span className="font-display font-extrabold text-lg tracking-tight text-white">
              LIFE<span className="text-accent">KART</span>
            </span>
          </div>
          <p className="text-sm text-gray-400 leading-relaxed">
            Wholesale essentials locked in for 60 years. Manufacturer prices, lifetime delivery.
          </p>
        </div>

        <div>
          <h4 className="text-xs font-bold uppercase tracking-widest text-gray-500 mb-4">Product</h4>
          <div className="space-y-2">
            {['Categories', 'How It Works', 'For Business', 'Pricing'].map((item) => (
              <Link key={item} href="#" className="block text-sm text-gray-400 hover:text-white transition-colors">
                {item}
              </Link>
            ))}
          </div>
        </div>

        <div>
          <h4 className="text-xs font-bold uppercase tracking-widest text-gray-500 mb-4">Company</h4>
          <div className="space-y-2">
            {['About', 'Careers', 'Press', 'Contact'].map((item) => (
              <Link key={item} href="#" className="block text-sm text-gray-400 hover:text-white transition-colors">
                {item}
              </Link>
            ))}
          </div>
        </div>

        <div>
          <h4 className="text-xs font-bold uppercase tracking-widest text-gray-500 mb-4">Legal</h4>
          <div className="space-y-2">
            {['Privacy Policy', 'Terms of Service', 'Refund Policy', 'Cookie Settings'].map((item) => (
              <Link key={item} href="#" className="block text-sm text-gray-400 hover:text-white transition-colors">
                {item}
              </Link>
            ))}
          </div>
        </div>
      </div>

      <div className="border-t border-gray-800">
        <div className="max-w-7xl mx-auto px-6 py-6 text-center text-xs text-gray-600">
          © {new Date().getFullYear()} LifeKart Inc. All rights reserved.
        </div>
      </div>
    </footer>
  )
}
