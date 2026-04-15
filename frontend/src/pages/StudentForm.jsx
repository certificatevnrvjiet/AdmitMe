import React from 'react'
import { Link } from 'react-router-dom'

export default function StudentForm() {
  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="w-full max-w-2xl bg-white rounded-2xl shadow-lg p-8">
        <h2 className="text-2xl font-semibold">Student Application (Placeholder)</h2>
        <p className="text-gray-600 mt-4">This page will contain the application form for students.</p>
        <div className="mt-6">
          <Link to="/" className="text-indigo-600 underline">Back to Home</Link>
        </div>
      </div>
    </div>
  )
}
