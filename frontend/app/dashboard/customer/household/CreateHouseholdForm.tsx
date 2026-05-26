'use client'

import { useState } from 'react'
import { Home, Users, Loader2, MapPin, Calendar, User } from 'lucide-react'

interface CreateProps {
  onCreated: () => void
}

export default function CreateHouseholdForm({ onCreated }: CreateProps) {
  const [step, setStep] = useState(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [conditionInput, setConditionInput] = useState('')
  const [allergyInput, setAllergyInput] = useState('')

  const [form, setForm] = useState({
    address_line1: '',
    address_line2: '',
    city: '',
    state: '',
    pincode: '',
    monthly_grocery_budget: '15000',
    prefer_organic: false,
  })

  const [self, setSelf] = useState({
    full_name: '',
    date_of_birth: '',
    gender: 'male',
    dietary_preference: '',
    blood_group: '',
    height_cm: '',
    weight_kg: '',
    existing_conditions: [] as string[],
    allergies: [] as string[],
  })

  const RELATIONS = ['self', 'spouse', 'child', 'parent', 'sibling', 'grandparent']
  const GENDERS = ['male', 'female', 'other']
  const DIETS = [
    { value: '', label: 'No preference' },
    { value: 'vegetarian', label: 'Vegetarian' },
    { value: 'non_veg', label: 'Non-Vegetarian' },
    { value: 'vegan', label: 'Vegan' },
    { value: 'jain', label: 'Jain' },
    { value: 'keto', label: 'Keto' },
    { value: 'diabetic', label: 'Diabetic' },
  ]
  const BLOOD_GROUPS = ['', 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']

  const CONDITIONS = [
    'Diabetes Type 2', 'High Blood Pressure', 'Thyroid', 'Asthma', 'Lactose Intolerant',
    'Gluten Intolerant', 'Arthritis', 'PCOD/PCOS', 'Low B12', 'High Cholesterol',
  ]

  const ALLERGIES = [
    'Peanuts', 'Tree Nuts', 'Dairy', 'Eggs', 'Soy', 'Wheat', 'Shellfish', 'Gluten',
    'Latex', 'Dust', 'Pollen',
  ]

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError('')

    const members = [{
      full_name: self.full_name,
      family_relation: 'self',
      date_of_birth: self.date_of_birth,
      gender: self.gender,
      dietary_preference: self.dietary_preference || undefined,
      lifestyle_tags: [] as string[],
    }]

    try {
      const { apiClient } = await import('@/lib/api')

      const household = await apiClient('/profiling/households', {
        method: 'POST',
        body: JSON.stringify({
          address_line1: form.address_line1,
          address_line2: form.address_line2 || undefined,
          city: form.city,
          state: form.state,
          pincode: form.pincode,
          monthly_grocery_budget: form.monthly_grocery_budget,
          prefer_organic: form.prefer_organic,
          members,
        }),
      })

      const selfMember = household.members?.[0]
      if (selfMember) {
        await apiClient(`/health/profiles/${selfMember.id}`, {
          method: 'PATCH',
          body: JSON.stringify({
            blood_group: self.blood_group || null,
            height_cm: self.height_cm ? parseFloat(self.height_cm) : null,
            weight_kg: self.weight_kg ? parseFloat(self.weight_kg) : null,
            existing_conditions: self.existing_conditions,
            allergies: self.allergies,
          }),
        })
      }

      onCreated()
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const addCondition = (c: string) => {
    if (c && !self.existing_conditions.includes(c)) {
      setSelf({ ...self, existing_conditions: [...self.existing_conditions, c] })
    }
    setConditionInput('')
  }

  const addAllergy = (a: string) => {
    if (a && !self.allergies.includes(a)) {
      setSelf({ ...self, allergies: [...self.allergies, a] })
    }
    setAllergyInput('')
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl px-4 py-3 text-sm text-red-700">{error}</div>
      )}

      <div className="flex gap-2 mb-6">
        {[1, 2].map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => setStep(s)}
            className={`flex-1 py-3 text-sm font-bold rounded-lg transition-all ${
              step === s
                ? 'bg-accent text-white shadow-button'
                : 'bg-surface-muted text-gray-500'
            }`}
          >
            {s === 1 ? 'Address' : 'Your Profile'}
          </button>
        ))}
      </div>

      {step === 1 && (
        <div className="bg-white rounded-2xl p-6 shadow-card space-y-4">
          <div className="flex items-center gap-2 mb-4">
            <Home className="w-5 h-5 text-accent" />
            <h3 className="text-lg font-display font-bold uppercase tracking-tight">Delivery Address</h3>
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-gray-400 mb-1">Address Line 1 *</label>
            <input
              type="text" required value={form.address_line1}
              onChange={(e) => setForm({ ...form, address_line1: e.target.value })}
              className="w-full px-4 py-3 border border-surface-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/20"
              placeholder="Flat 302, Sunshine Apartments"
            />
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-gray-400 mb-1">Address Line 2</label>
            <input
              type="text" value={form.address_line2}
              onChange={(e) => setForm({ ...form, address_line2: e.target.value })}
              className="w-full px-4 py-3 border border-surface-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/20"
              placeholder="Near Central Park"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-400 mb-1">City *</label>
              <input
                type="text" required value={form.city}
                onChange={(e) => setForm({ ...form, city: e.target.value })}
                className="w-full px-4 py-3 border border-surface-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/20"
                placeholder="Mumbai"
              />
            </div>
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-400 mb-1">State *</label>
              <input
                type="text" required value={form.state}
                onChange={(e) => setForm({ ...form, state: e.target.value })}
                className="w-full px-4 py-3 border border-surface-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/20"
                placeholder="Maharashtra"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-400 mb-1">Pincode *</label>
              <input
                type="text" required value={form.pincode}
                onChange={(e) => setForm({ ...form, pincode: e.target.value })}
                className="w-full px-4 py-3 border border-surface-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/20"
                placeholder="400001"
              />
            </div>
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-400 mb-1">Monthly Budget</label>
              <input
                type="number" value={form.monthly_grocery_budget}
                onChange={(e) => setForm({ ...form, monthly_grocery_budget: e.target.value })}
                className="w-full px-4 py-3 border border-surface-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/20"
              />
            </div>
          </div>

          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox" checked={form.prefer_organic}
              onChange={(e) => setForm({ ...form, prefer_organic: e.target.checked })}
              className="w-4 h-4 rounded border-gray-300 text-accent focus:ring-accent"
            />
            Prefer organic products
          </label>

          <button
            type="button"
            onClick={() => setStep(2)}
            disabled={!form.address_line1 || !form.city || !form.state || !form.pincode}
            className="w-full px-6 py-3.5 text-sm font-bold text-white bg-accent rounded-lg
                       shadow-button hover:shadow-button-hover hover:-translate-y-0.5
                       transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next: Your Profile
          </button>
        </div>
      )}

      {step === 2 && (
        <div className="space-y-4">
          <div className="bg-white rounded-2xl p-6 shadow-card space-y-4">
            <div className="flex items-center gap-2 mb-4">
              <User className="w-5 h-5 text-accent" />
              <h3 className="text-lg font-display font-bold uppercase tracking-tight">Your Details</h3>
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-400 mb-1">Full Name *</label>
              <input
                type="text" required value={self.full_name}
                onChange={(e) => setSelf({ ...self, full_name: e.target.value })}
                className="w-full px-4 py-3 border border-surface-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/20"
                placeholder="Priya Sharma"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-gray-400 mb-1">Date of Birth *</label>
                <input
                  type="date" required value={self.date_of_birth}
                  onChange={(e) => setSelf({ ...self, date_of_birth: e.target.value })}
                  className="w-full px-4 py-3 border border-surface-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/20"
                />
              </div>
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-gray-400 mb-1">Gender *</label>
                <select
                  value={self.gender}
                  onChange={(e) => setSelf({ ...self, gender: e.target.value })}
                  className="w-full px-4 py-3 border border-surface-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/20"
                >
                  {GENDERS.map(g => <option key={g} value={g}>{g}</option>)}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-400 mb-1">Dietary Preference</label>
              <select
                value={self.dietary_preference}
                onChange={(e) => setSelf({ ...self, dietary_preference: e.target.value })}
                className="w-full px-4 py-3 border border-surface-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/20"
              >
                {DIETS.map(d => <option key={d.value} value={d.value}>{d.label}</option>)}
              </select>
            </div>
          </div>

          <div className="bg-white rounded-2xl p-6 shadow-card space-y-4">
            <div className="flex items-center gap-2 mb-4">
              <User className="w-5 h-5 text-accent" />
              <h3 className="text-lg font-display font-bold uppercase tracking-tight">Health Profile</h3>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-gray-400 mb-1">Blood Group</label>
                <select
                  value={self.blood_group}
                  onChange={(e) => setSelf({ ...self, blood_group: e.target.value })}
                  className="w-full px-4 py-3 border border-surface-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/20"
                >
                  {BLOOD_GROUPS.map(bg => <option key={bg} value={bg}>{bg || 'Unknown'}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-gray-400 mb-1">Height (cm)</label>
                <input
                  type="number" value={self.height_cm}
                  onChange={(e) => setSelf({ ...self, height_cm: e.target.value })}
                  className="w-full px-4 py-3 border border-surface-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/20"
                  placeholder="165"
                />
              </div>
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-gray-400 mb-1">Weight (kg)</label>
                <input
                  type="number" value={self.weight_kg}
                  onChange={(e) => setSelf({ ...self, weight_kg: e.target.value })}
                  className="w-full px-4 py-3 border border-surface-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/20"
                  placeholder="62"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-400 mb-2">Existing Conditions</label>
              <div className="flex gap-2 mb-3">
                <input type="text" value={conditionInput}
                  onChange={(e) => setConditionInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addCondition(conditionInput), setConditionInput(''))}
                  placeholder="Other condition..."
                  className="flex-1 px-3 py-1.5 border border-surface-border rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-accent/20" />
                <button type="button" onClick={() => { addCondition(conditionInput); setConditionInput('') }}
                  className="px-3 py-1.5 bg-surface-muted text-gray-600 rounded-lg text-xs font-bold hover:bg-gray-200">Add</button>
              </div>
              <div className="flex flex-wrap gap-2 mb-2">
                {self.existing_conditions.map(c => (
                  <span key={c} className="inline-flex items-center gap-1 px-3 py-1 bg-amber-50 text-amber-700 rounded-full text-xs font-medium">
                    {c}
                    <button
                      type="button"
                      onClick={() => setSelf({ ...self, existing_conditions: self.existing_conditions.filter(x => x !== c) })}
                      className="text-amber-400 hover:text-amber-600"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
              <div className="flex flex-wrap gap-2">
                {CONDITIONS.filter(c => !self.existing_conditions.includes(c)).map(c => (
                  <button
                    key={c}
                    type="button"
                    onClick={() => addCondition(c)}
                    className="px-3 py-1.5 text-xs font-medium text-gray-500 bg-surface-muted rounded-full hover:bg-amber-50 hover:text-amber-700 transition-colors"
                  >
                    + {c}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-400 mb-2">Allergies</label>
              <div className="flex gap-2 mb-3">
                <input type="text" value={allergyInput}
                  onChange={(e) => setAllergyInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addAllergy(allergyInput), setAllergyInput(''))}
                  placeholder="Other allergy..."
                  className="flex-1 px-3 py-1.5 border border-surface-border rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-accent/20" />
                <button type="button" onClick={() => { addAllergy(allergyInput); setAllergyInput('') }}
                  className="px-3 py-1.5 bg-surface-muted text-gray-600 rounded-lg text-xs font-bold hover:bg-gray-200">Add</button>
              </div>
              <div className="flex flex-wrap gap-2 mb-2">
                {self.allergies.map(a => (
                  <span key={a} className="inline-flex items-center gap-1 px-3 py-1 bg-red-50 text-red-700 rounded-full text-xs font-medium">
                    {a}
                    <button
                      type="button"
                      onClick={() => setSelf({ ...self, allergies: self.allergies.filter(x => x !== a) })}
                      className="text-red-400 hover:text-red-600"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
              <div className="flex flex-wrap gap-2">
                {ALLERGIES.filter(a => !self.allergies.includes(a)).map(a => (
                  <button
                    key={a}
                    type="button"
                    onClick={() => addAllergy(a)}
                    className="px-3 py-1.5 text-xs font-medium text-gray-500 bg-surface-muted rounded-full hover:bg-red-50 hover:text-red-700 transition-colors"
                  >
                    + {a}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="flex gap-3">
            <button
              type="button"
              onClick={() => setStep(1)}
              className="flex-1 px-6 py-3.5 text-sm font-bold text-gray-600 bg-surface-muted rounded-lg
                         hover:bg-gray-200 transition-all"
            >
              Back
            </button>
            <button
              type="submit"
              disabled={loading || !self.full_name || !self.date_of_birth}
              className="flex-1 flex items-center justify-center gap-2 px-6 py-3.5 text-sm font-bold
                         text-white bg-accent rounded-lg shadow-button hover:shadow-button-hover
                         hover:-translate-y-0.5 transition-all disabled:opacity-50"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Home className="w-4 h-4" />}
              Create Household
            </button>
          </div>
        </div>
      )}
    </form>
  )
}