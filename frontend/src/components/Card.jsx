import React from 'react'

export default function Card({ children, className = '', variant = 'default' }) {
  const base = 'rounded-2xl p-6 transition-transform transform shadow-lg'
  const variants = {
    default: 'backdrop-blur-sm bg-white/80 dark:bg-gray-800/60',
    // more visible white transparent look (not grey)
    transparent: 'backdrop-blur-md bg-white/60 dark:bg-white/20 border border-white/10',
    subtle: 'bg-white/60 dark:bg-gray-800/60 opacity-90',
  }

  const v = variants[variant] || variants.default
  return <div className={`${base} ${v} ${className}`}>{children}</div>
}
