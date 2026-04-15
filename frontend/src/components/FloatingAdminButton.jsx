import React from 'react'
import { useNavigate } from 'react-router-dom'
import Button from './Button'

export default function FloatingAdminButton() {
  const navigate = useNavigate()

  return (
    <div className="fixed top-4 right-4 z-50">
      <div className="bg-white rounded-2xl shadow-md p-3 flex items-center gap-3 max-w-xs sm:max-w-sm">
        <div>
          <div className="text-sm font-medium">Admin</div>
          <div className="text-xs text-gray-500">Staff access</div>
        </div>
        <div className="ml-auto">
          <Button onClick={() => navigate('/admin-login')} variant="red">Login</Button>
        </div>
      </div>
    </div>
  )
}
