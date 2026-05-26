'use client'

import { apiClient } from '@/lib/api'
import { useEffect, useState } from 'react'
import { Users, Plus, Trash2, Loader2 } from 'lucide-react'
import CreateHouseholdForm from './CreateHouseholdForm'
import AddMemberModal from './AddMemberModal'

interface Member {
  id: string
  full_name: string
  family_relation: string
  date_of_birth: string
  gender: string
  dietary_preference: string
  is_active: boolean
}

interface Household {
  id: string
  address_line1: string
  city: string
  state: string
  pincode: string
  monthly_grocery_budget: number
  members: Member[]
}

const relations = ['spouse', 'child', 'parent', 'sibling', 'grandparent']
const genders = ['male', 'female', 'other']
const diets = ['', 'vegetarian', 'non_veg', 'vegan', 'jain', 'keto', 'diabetic']

export default function HouseholdPage() {
  const [household, setHousehold] = useState<Household | null>(null)
  const [loading, setLoading] = useState(true)
  const [isModalOpen, setIsModalOpen] = useState(false)

  async function load() {
    setLoading(true)
    try {
      const data = await apiClient('/profiling/households/me').catch(() => null)
      if (data) setHousehold(data)
    } catch {} finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  async function deactivateMember(memberId: string) {
    try {
      await apiClient(`/profiling/members/${memberId}`, { method: 'DELETE' })
      await load()
    } catch (err: any) { alert(err.message) }
  }

  if (loading) {
    return (
      <div className="space-y-4 animate-pulse">
        <div className="h-8 bg-gray-200 rounded w-48" />
        <div className="h-40 bg-gray-100 rounded-2xl" />
      </div>
    )
  }

  if (!household) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl md:text-4xl font-display font-extrabold uppercase tracking-tighter">Set Up Household</h1>
        <CreateHouseholdForm onCreated={load} />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl md:text-4xl font-display font-extrabold uppercase tracking-tighter">My Household</h1>

      <div className="bg-white rounded-2xl p-6 shadow-card">
        <div className="flex items-center gap-3 mb-4">
          <Users className="w-5 h-5 text-accent" />
          <h3 className="text-lg font-display font-bold uppercase tracking-tight">Household Details</h3>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <p className="text-xs text-gray-400 uppercase tracking-wider">Address</p>
            <p className="font-semibold">{household.address_line1}</p>
          </div>
          <div>
            <p className="text-xs text-gray-400 uppercase tracking-wider">City</p>
            <p className="font-semibold">{household.city}, {household.state}</p>
          </div>
          <div>
            <p className="text-xs text-gray-400 uppercase tracking-wider">Pincode</p>
            <p className="font-semibold">{household.pincode}</p>
          </div>
          <div>
            <p className="text-xs text-gray-400 uppercase tracking-wider">Monthly Budget</p>
            <p className="font-semibold">₹{Number(household.monthly_grocery_budget || 0).toLocaleString('en-IN')}</p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-2xl p-6 shadow-card">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <Users className="w-5 h-5 text-accent" />
            <h3 className="text-lg font-display font-bold uppercase tracking-tight">
              Members ({household.members.length})
            </h3>
          </div>
        </div>

        <div className="space-y-3 mb-6">
          {household.members.map((member) => (
            <div key={member.id} className="flex items-center justify-between py-3 border-b border-surface-border last:border-0">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-surface-muted rounded-full flex items-center justify-center">
                  <span className="text-sm font-bold text-gray-500">
                    {member.full_name?.charAt(0)?.toUpperCase()}
                  </span>
                </div>
                <div>
                  <p className="text-sm font-semibold">
                    {member.full_name}
                    {member.family_relation === 'self' && (
                      <span className="ml-2 text-xs bg-accent/10 text-accent px-2 py-0.5 rounded-full">You</span>
                    )}
                  </p>
                  <p className="text-xs text-gray-400">
                    {member.family_relation} · {member.gender} · {new Date(member.date_of_birth).toLocaleDateString('en-IN')}
                    {member.dietary_preference && ` · ${member.dietary_preference}`}
                  </p>
                </div>
              </div>
              {member.family_relation !== 'self' && member.is_active && (
                <button
                  onClick={() => deactivateMember(member.id)}
                  className="p-2 text-gray-400 hover:text-red-500 rounded-lg hover:bg-red-50 transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              )}
            </div>
          ))}
        </div>

        <div className="border-t border-surface-border pt-4 mt-4">
          <button
            onClick={() => setIsModalOpen(true)}
            className="w-full py-4 border-2 border-dashed border-gray-300 rounded-lg text-sm font-bold text-gray-500 hover:border-accent hover:text-accent hover:bg-orange-50 transition-all flex items-center justify-center gap-2"
          >
            <Plus className="w-5 h-5" />
            Add Family Member
          </button>
        </div>

        {isModalOpen && (
          <AddMemberModal onClose={() => setIsModalOpen(false)} onAdded={load} />
        )}
      </div>
    </div>
  )
}