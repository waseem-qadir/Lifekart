import type { Metadata } from 'next'
import './globals.css'
import { AuthProvider } from '@/lib/auth'
import Navbar from '@/components/layout/Navbar'
import Footer from '@/components/layout/Footer'

export const metadata: Metadata = {
  title: 'LifeKart — Lifetime Wholesale Buying',
  description: 'Lock in wholesale prices for 60 years. Bulk essentials delivered to your doorstep at manufacturer rates.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen flex flex-col">
        <AuthProvider>
          <Navbar />
          <main className="flex-1">{children}</main>
          <Footer />
        </AuthProvider>
      </body>
    </html>
  )
}