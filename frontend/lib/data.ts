export interface Category {
  id: string
  name: string
  slug: string
  description: string
  image: string
  productCount: number
  avgSavings: string
}

export interface Stat {
  label: string
  value: string
  sublabel: string
}

export const categories: Category[] = [
  {
    id: 'grains',
    name: 'Grains & Staples',
    slug: 'grains-staples',
    description: 'Rice, wheat, pulses, and flour — bulk wholesale priced for a lifetime.',
    image: 'https://images.unsplash.com/photo-1586201375761-83865001e31c?w=800&q=80',
    productCount: 142,
    avgSavings: '42%',
  },
  {
    id: 'spices',
    name: 'Spices & Herbs',
    slug: 'spices-herbs',
    description: 'Turmeric, cumin, cardamom, and blended masalas sourced direct from growers.',
    image: 'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=800&q=80',
    productCount: 98,
    avgSavings: '35%',
  },
  {
    id: 'cleaning',
    name: 'Cleaning & Janitorial',
    slug: 'cleaning-janitorial',
    description: 'Industrial-grade cleaners, detergents, and supplies for homes and businesses.',
    image: 'https://images.unsplash.com/photo-1585421514284-efb74c2b69ba?w=800&q=80',
    productCount: 67,
    avgSavings: '28%',
  },
  {
    id: 'pantry',
    name: 'Corporate Pantry',
    slug: 'corporate-pantry',
    description: 'Premium coffee, tea, snacks, and instant meals for office pantries.',
    image: 'https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=800&q=80',
    productCount: 55,
    avgSavings: '31%',
  },
]

export const platformStats: Stat[] = [
  { label: 'Active Households', value: '12,400+', sublabel: 'across 28 cities' },
  { label: 'Avg Monthly Savings', value: '₹3,200', sublabel: 'per household' },
  { label: 'Corporate Partners', value: '140+', sublabel: 'employers onboard' },
]

export const navLinks = [
  { label: 'Categories', href: '#categories' },
  { label: 'How It Works', href: '#how-it-works' },
  { label: 'For Business', href: '#business' },
]
