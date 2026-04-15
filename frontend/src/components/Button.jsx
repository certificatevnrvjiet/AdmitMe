import React from 'react'

export default function Button({ children, onClick, variant = 'primary', className = '' }) {
  const base = 'inline-flex items-center justify-center px-4 py-2 rounded-md font-medium transition-transform'
  const variants = {
    primary: 'bg-gradient-to-r from-indigo-600 to-blue-500 text-white shadow-md hover:scale-105',
    subtle: 'bg-white/60 text-gray-800 border border-gray-200 hover:scale-105',
    red: 'bg-red-600 text-white shadow-md hover:bg-red-700 hover:scale-105',
  }
  return (
    <button onClick={onClick} className={`${base} ${variants[variant] || variants.primary} ${className}`}>
      {children}
    </button>
  )
}
