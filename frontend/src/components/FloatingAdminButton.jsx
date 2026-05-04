import React from 'react'
import { useNavigate } from 'react-router-dom'
import Button from './Button'
import { useAuth } from '../auth/AuthContext'

export default function FloatingAdminButton() {
  const navigate = useNavigate()
  const { isAuthenticated, role } = useAuth()
  const isStaffSession = isAuthenticated && role !== 'student'

  return (
    <div className="fixed top-4 right-4 z-50">
      <div className="bg-white rounded-2xl shadow-md p-3 flex items-center gap-3 max-w-xs sm:max-w-sm">
        <div>
          <div className="text-sm font-medium">{isStaffSession ? 'Admin Dashboard' : 'Admin'}</div>
          <div className="text-xs text-gray-500">{isStaffSession ? 'Signed in' : 'Staff access'}</div>
        </div>
        <div className="ml-auto">
          <Button onClick={() => navigate(isStaffSession ? '/dashboard' : '/admin-login')} variant="red">
            {isStaffSession ? 'Dashboard' : 'Login'}
          </Button>
        </div>
      </div>
    </div>
  )
}
