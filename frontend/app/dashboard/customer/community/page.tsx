'use client'

import { apiClient } from '@/lib/api'
import { useEffect, useState } from 'react'
import { Users, MapPin, Plus, Loader2, CheckCircle } from 'lucide-react'

interface CommunityGroup {
  id: string
  name: string
  locality: string | null
  city: string | null
  state: string | null
  pincode: string | null
  admin_household_id: string
  min_households_for_pooling: number
  status: string
}

export default function CommunityPage() {
  const [groups, setGroups] = useState<CommunityGroup[]>([])
  const [loading, setLoading] = useState(true)
  const [joining, setJoining] = useState<string | null>(null)
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({
    name: '', locality: '', city: '', state: '', pincode: '', min_households_for_pooling: 100
  })
  const [creating, setCreating] = useState(false)
  const [household, setHousehold] = useState<any>(null)

  async function load() {
    try {
      const [groupsData, hhData] = await Promise.all([
        apiClient('/community/groups').catch(() => []),
        apiClient('/profiling/households/me').catch(() => null),
      ])
      setGroups(Array.isArray(groupsData) ? groupsData : [])
      setHousehold(hhData)
      if (hhData) {
        setForm(prev => ({
          ...prev,
          pincode: hhData.pincode || '',
          city: hhData.city || '',
          state: hhData.state || '',
        }))
      }
    } catch {} finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  async function joinGroup(groupId: string) {
    setJoining(groupId)
    try {
      await apiClient(`/community/groups/${groupId}/join`, { method: 'POST' })
      await load()
    } catch (err: any) {
      alert(err.message)
    } finally {
      setJoining(null)
    }
  }

  async function createGroup(e: React.FormEvent) {
    e.preventDefault()
    setCreating(true)
    try {
      await apiClient('/community/groups', {
        method: 'POST',
        body: JSON.stringify(form),
      })
      setShowCreate(false)
      await load()
    } catch (err: any) {
      alert(err.message)
    } finally {
      setCreating(false)
    }
  }

  if (loading) {
    return (
      <div className="space-y-4 animate-pulse">
        <div className="h-8 bg-gray-200 rounded w-64" />
        {[1,2,3].map(i => <div key={i} className="h-24 bg-gray-100 rounded-2xl" />)}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl md:text-4xl font-display font-extrabold uppercase tracking-tighter">Community Groups</h1>
          <p className="text-gray-500 mt-1">Pool orders with neighbors for bulk discounts.</p>
        </div>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="flex items-center gap-2 px-5 py-2.5 text-sm font-bold text-white bg-accent rounded-lg
                     shadow-button hover:shadow-button-hover hover:-translate-y-0.5 transition-all"
        >
          <Plus className="w-4 h-4" />
          Create Group
        </button>
      </div>

      {showCreate && (
        <form onSubmit={createGroup} className="bg-white rounded-2xl p-6 shadow-card space-y-4">
          <h3 className="text-lg font-display font-bold uppercase tracking-tight">Create New Group</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <input
              type="text" required placeholder="Group name (e.g. Sector 14 Residents)"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="px-4 py-2.5 border border-surface-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/20"
            />
            <input
              type="text" placeholder="Locality" value={form.locality}
              onChange={(e) => setForm({ ...form, locality: e.target.value })}
              className="px-4 py-2.5 border border-surface-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/20"
            />
            <input
              type="text" placeholder="City" value={form.city}
              onChange={(e) => setForm({ ...form, city: e.target.value })}
              className="px-4 py-2.5 border border-surface-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/20"
            />
            <input
              type="text" placeholder="State" value={form.state}
              onChange={(e) => setForm({ ...form, state: e.target.value })}
              className="px-4 py-2.5 border border-surface-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/20"
            />
            <input
              type="text" placeholder="Pincode" value={form.pincode}
              onChange={(e) => setForm({ ...form, pincode: e.target.value })}
              className="px-4 py-2.5 border border-surface-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/20"
            />
            <input
              type="number" placeholder="Min households" value={form.min_households_for_pooling}
              onChange={(e) => setForm({ ...form, min_households_for_pooling: Number(e.target.value) })}
              className="px-4 py-2.5 border border-surface-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/20"
            />
          </div>
          <div className="flex gap-3">
            <button
              type="submit" disabled={creating}
              className="px-5 py-2.5 text-sm font-bold text-white bg-accent rounded-lg shadow-button
                         hover:shadow-button-hover hover:-translate-y-0.5 transition-all disabled:opacity-50"
            >
              {creating ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Create'}
            </button>
            <button
              type="button" onClick={() => setShowCreate(false)}
              className="px-5 py-2.5 text-sm font-bold text-gray-600 bg-surface-muted rounded-lg hover:bg-gray-200 transition-all"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {groups.length === 0 ? (
        <div className="bg-white rounded-2xl p-8 shadow-card text-center">
          <Users className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500 font-bold uppercase tracking-wider">No groups yet</p>
          <p className="text-sm text-gray-400 mt-1">Create or join a group to start pooling orders</p>
        </div>
      ) : (
        <div className="space-y-4">
          {groups.map((group) => (
            <div key={group.id} className="bg-white rounded-2xl p-5 shadow-card flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 bg-accent/10 rounded-xl flex items-center justify-center">
                  <Users className="w-5 h-5 text-accent" />
                </div>
                <div>
                  <p className="text-sm font-semibold">{group.name}</p>
                  <p className="text-xs text-gray-400 capitalize">
                    {[group.locality, group.city, group.state, group.pincode].filter(Boolean).join(', ')}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-xs text-gray-400">Min {group.min_households_for_pooling} households</span>
                <button
                  onClick={() => joinGroup(group.id)}
                  disabled={joining === group.id}
                  className="flex items-center gap-2 px-4 py-2 text-sm font-bold text-white bg-accent rounded-lg
                             shadow-button hover:shadow-button-hover hover:-translate-y-0.5 transition-all
                             disabled:opacity-50"
                >
                  {joining === group.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
                  Join
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}