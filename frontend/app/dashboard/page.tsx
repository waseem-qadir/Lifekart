'use client'

import { useAuth } from '@/lib/auth'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'
import { Loader2 } from 'lucide-react'

export default function DashboardRedirect() {
  const { user, isLoading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (isLoading) return
    if (!user) {
      router.push('/login')
      return
    }
    switch (user.role) {
      case 'customer': router.push('/dashboard/customer'); break
      case 'manufacturer': router.push('/dashboard/manufacturer'); break
      case 'corporate_admin': router.push('/dashboard/corporate'); break
      case 'superadmin': router.push('/dashboard/admin'); break
      default: router.push('/login')
    }
  }, [user, isLoading, router])

  return (
    <div className="min-h-[calc(100vh-64px)] flex items-center justify-center">
      <Loader2 className="w-8 h-8 text-accent animate-spin" />
    </div>
  )
}