import React from 'react'
import { Link } from 'react-router-dom'

export default function AdminLogin() {
  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-lg p-8">
        <h2 className="text-2xl font-semibold">Admin Login (Placeholder)</h2>
        <p className="text-gray-600 mt-4">Admin authentication UI will be implemented here.</p>
        <div className="mt-6">
          <Link to="/" className="text-indigo-600 underline">Back to Home</Link>
        </div>
      </div>
    </div>
  )
}
