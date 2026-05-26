'use client'

import { useState } from 'react'
import { Plus, X, Loader2, User, HeartPulse } from 'lucide-react'

interface Props {
  onClose: () => void
  onAdded: () => void
}

const RELATIONS = ['spouse', 'child', 'parent', 'sibling', 'grandparent']
const GENDERS = ['male', 'female', 'other']
const DIETS = ['', 'vegetarian', 'non_veg', 'vegan', 'jain', 'keto', 'diabetic']
const BLOOD_GROUPS = ['', 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
const CONDITIONS = [
  'Diabetes Type 2', 'High Blood Pressure', 'Thyroid', 'Asthma', 'Lactose Intolerant',
  'Gluten Intolerant', 'Arthritis', 'PCOD/PCOS', 'Low B12', 'High Cholesterol',
]
const ALLERGIES = [
  'Peanuts', 'Tree Nuts', 'Dairy', 'Eggs', 'Soy', 'Wheat', 'Shellfish', 'Gluten',
  'Latex', 'Dust', 'Pollen',
]

export default function AddMemberModal({ onClose, onAdded }: Props) {
  const [step, setStep] = useState(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [conditionInput, setConditionInput] = useState('')
  const [allergyInput, setAllergyInput] = useState('')

  const [form, setForm] = useState({
    full_name: '',
    family_relation: 'spouse',
    date_of_birth: '',
    gender: 'female',
    dietary_preference: '',
    blood_group: '',
    height_cm: '',
    weight_kg: '',
    existing_conditions: [] as string[],
    allergies: [] as string[],
  })

  const addCondition = (c: string) => {
    if (c && !form.existing_conditions.includes(c)) {
      setForm({ ...form, existing_conditions: [...form.existing_conditions, c] })
    }
  }

  const addAllergy = (a: string) => {
    if (a && !form.allergies.includes(a)) {
      setForm({ ...form, allergies: [...form.allergies, a] })
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (step === 1) { setStep(2); return }

    setLoading(true)
    setError('')

    try {
      const { apiClient } = await import('@/lib/api')

      const member = await apiClient('/profiling/households/me/members', {
        method: 'POST',
        body: JSON.stringify({
          full_name: form.full_name,
          family_relation: form.family_relation,
          date_of_birth: form.date_of_birth,
          gender: form.gender,
          dietary_preference: form.dietary_preference || undefined,
          lifestyle_tags: [],
        }),
      })

      await apiClient(`/health/profiles/${member.id}`, {
        method: 'PATCH',
        body: JSON.stringify({
          blood_group: form.blood_group || null,
          height_cm: form.height_cm ? parseFloat(form.height_cm) : null,
          weight_kg: form.weight_kg ? parseFloat(form.weight_kg) : null,
          existing_conditions: form.existing_conditions,
          allergies: form.allergies,
        }),
      })

      onAdded()
      onClose()
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-white rounded-2xl shadow-float-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-surface-border">
          <h2 className="text-xl font-display font-extrabold uppercase tracking-tighter">Add Family Member</h2>
          <button onClick={onClose} className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-surface-muted transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-xl px-4 py-3 text-sm text-red-700">{error}</div>
          )}

          <div className="flex gap-2 mb-4">
            {[1, 2].map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => setStep(s)}
                className={`flex-1 py-2 text-xs font-bold rounded-lg transition-all ${
                  step === s ? 'bg-accent text-white shadow-button' : 'bg-surface-muted text-gray-500'
                }`}
              >
                {s === 1 ? 'Basic Info' : 'Health Profile'}
              </button>
            ))}
          </div>

          {step === 1 && (
            <div className="space-y-4">
              <div className="flex items-center gap-2 mb-2">
                <User className="w-5 h-5 text-accent" />
                <h3 className="text-sm font-display font-bold uppercase tracking-tight">Personal Details</h3>
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-gray-400 mb-1">Full Name *</label>
                <input type="text" required value={form.full_name}
                  onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                  className="w-full px-4 py-3 border border-surface-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/20"
                  placeholder="Rahul Sharma" />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-gray-400 mb-1">Relation *</label>
                  <select value={form.family_relation}
                    onChange={(e) => setForm({ ...form, family_relation: e.target.value })}
                    className="w-full px-4 py-3 border border-surface-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/20">
                    {RELATIONS.map(r => <option key={r} value={r}>{r}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-gray-400 mb-1">Gender *</label>
                  <select value={form.gender}
                    onChange={(e) => setForm({ ...form, gender: e.target.value })}
                    className="w-full px-4 py-3 border border-surface-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/20">
                    {GENDERS.map(g => <option key={g} value={g}>{g}</option>)}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-gray-400 mb-1">Date of Birth *</label>
                <input type="date" required value={form.date_of_birth}
                  onChange={(e) => setForm({ ...form, date_of_birth: e.target.value })}
                  className="w-full px-4 py-3 border border-surface-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/20" />
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-gray-400 mb-1">Dietary Preference</label>
                <select value={form.dietary_preference}
                  onChange={(e) => setForm({ ...form, dietary_preference: e.target.value })}
                  className="w-full px-4 py-3 border border-surface-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/20">
                  <option value="">No preference</option>
                  {DIETS.filter(d => d).map(d => <option key={d} value={d}>{d}</option>)}
                </select>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4">
              <div className="flex items-center gap-2 mb-2">
                <HeartPulse className="w-5 h-5 text-accent" />
                <h3 className="text-sm font-display font-bold uppercase tracking-tight">Health Profile</h3>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-gray-400 mb-1">Blood Group</label>
                  <select value={form.blood_group}
                    onChange={(e) => setForm({ ...form, blood_group: e.target.value })}
                    className="w-full px-4 py-3 border border-surface-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/20">
                    {BLOOD_GROUPS.map(bg => <option key={bg} value={bg}>{bg || 'Unknown'}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-gray-400 mb-1">Height (cm)</label>
                  <input type="number" value={form.height_cm}
                    onChange={(e) => setForm({ ...form, height_cm: e.target.value })}
                    className="w-full px-4 py-3 border border-surface-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/20"
                    placeholder="165" />
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-gray-400 mb-1">Weight (kg)</label>
                  <input type="number" value={form.weight_kg}
                    onChange={(e) => setForm({ ...form, weight_kg: e.target.value })}
                    className="w-full px-4 py-3 border border-surface-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/20"
                    placeholder="62" />
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
                  {form.existing_conditions.map(c => (
                    <span key={c} className="inline-flex items-center gap-1 px-3 py-1 bg-amber-50 text-amber-700 rounded-full text-xs font-medium">
                      {c}
                      <button type="button"
                        onClick={() => setForm({ ...form, existing_conditions: form.existing_conditions.filter(x => x !== c) })}
                        className="text-amber-400 hover:text-amber-600">×</button>
                    </span>
                  ))}
                </div>
                <div className="flex flex-wrap gap-2">
                  {CONDITIONS.filter(c => !form.existing_conditions.includes(c)).map(c => (
                    <button key={c} type="button" onClick={() => addCondition(c)}
                      className="px-3 py-1.5 text-xs font-medium text-gray-500 bg-surface-muted rounded-full hover:bg-amber-50 hover:text-amber-700 transition-colors">
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
                  {form.allergies.map(a => (
                    <span key={a} className="inline-flex items-center gap-1 px-3 py-1 bg-red-50 text-red-700 rounded-full text-xs font-medium">
                      {a}
                      <button type="button"
                        onClick={() => setForm({ ...form, allergies: form.allergies.filter(x => x !== a) })}
                        className="text-red-400 hover:text-red-600">×</button>
                    </span>
                  ))}
                </div>
                <div className="flex flex-wrap gap-2">
                  {ALLERGIES.filter(a => !form.allergies.includes(a)).map(a => (
                    <button key={a} type="button" onClick={() => addAllergy(a)}
                      className="px-3 py-1.5 text-xs font-medium text-gray-500 bg-surface-muted rounded-full hover:bg-red-50 hover:text-red-700 transition-colors">
                      + {a}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          <div className="flex gap-3 pt-2">
            {step === 2 && (
              <button type="button" onClick={() => setStep(1)}
                className="flex-1 px-6 py-3.5 text-sm font-bold text-gray-600 bg-surface-muted rounded-lg hover:bg-gray-200 transition-all">
                Back
              </button>
            )}
            <button type="submit" disabled={loading || !form.full_name || !form.date_of_birth}
              className={`flex-1 flex items-center justify-center gap-2 px-6 py-3.5 text-sm font-bold text-white bg-accent rounded-lg
                shadow-button hover:shadow-button-hover hover:-translate-y-0.5 transition-all disabled:opacity-50`}>
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : step === 1 ? 'Next: Health' : <><Plus className="w-4 h-4" /> Save Member</>}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}