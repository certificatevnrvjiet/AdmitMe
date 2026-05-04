import React from 'react'
import { useNavigate } from 'react-router-dom'
import Card from '../components/Card'
import Button from '../components/Button'
import FeatureCard from '../components/FeatureCard'

function useScrollScale() {
  const [scale, setScale] = React.useState(1)
  React.useEffect(() => {
    const onScroll = () => {
      const y = window.scrollY || window.pageYOffset
      const next = Math.max(0.9, 1 - y / 2000)
      setScale(Number(next.toFixed(3)))
    }
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])
  return scale
}

function HeroIcon() {
  return (
    <svg className="w-14 h-14 text-red-600" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M12 2L15 8H9L12 2Z" fill="currentColor" opacity="0.95" />
      <path d="M12 22C16.4183 22 20 18.4183 20 14H4C4 18.4183 7.58172 22 12 22Z" fill="currentColor" opacity="0.65" />
    </svg>
  )
}

export default function LandingPage() {
  const navigate = useNavigate()
  const scale = useScrollScale()
  const [heroVisible, setHeroVisible] = React.useState(false)

  React.useEffect(() => {
    const t = setTimeout(() => setHeroVisible(true), 80)
    return () => clearTimeout(t)
  }, [])

  const features = [
    {
      title: 'Student Applications',
      description: 'Submit and manage applications with an intuitive workflow.',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m2 0a2 2 0 012 2v6H6v-6a2 2 0 012-2h8zM12 3v9" />
        </svg>
      ),
    },
    {
      title: 'Document Upload & Verification',
      description: 'Upload supporting documents and verify authenticity quickly.',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 8h10M7 12h4m1 8h2a2 2 0 002-2v-5H6v5a2 2 0 002 2h2" />
        </svg>
      ),
    },
    {
      title: 'Real-Time Status Tracking',
      description: 'Track application status updates instantly as they happen.',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3M21 12A9 9 0 1112 3v0" />
        </svg>
      ),
    },
    {
      title: 'Notifications System',
      description: 'Automatic notifications for students and administrators.',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6 6 0 00-5-5.917V4a1 1 0 10-2 0v1.083A6 6 0 006 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h11z" />
        </svg>
      ),
    },
  ]

  return (
    <div
      className="min-h-[calc(100vh-65px)] text-gray-900 relative overflow-x-hidden"
      style={{
        backgroundImage: 'url(https://vnrvjiet.ac.in/assets/images/Numbers-Image.png)',
        backgroundSize: 'cover',
        backgroundPosition: 'center',
      }}
    >
      {/* subtle overlay like LoginPage */}
      <div className="absolute inset-0 pointer-events-none bg-gradient-to-br from-blue-50/60 to-indigo-100/60" />

      {/* HERO */}
      <section className="min-h-[75vh] flex items-center justify-center">
        <div className={`text-center px-6 transition-all duration-700 ${heroVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'}`}>
          {/* <HeroIcon /> */}
          <h1 className="font-extrabold text-gray-900 mt-6" style={{ transform: `scale(${scale})`, transition: 'transform 200ms ease-out', fontSize: 'clamp(48px, 8vw, 88px)' }}>
            AdmitMe
          </h1>
          <p className="text-gray-600 mt-4 text-lg max-w-2xl mx-auto">Simplify admissions — submit, verify, and track applications.</p>
        </div>
      </section>

      {/* ABOUT - white cards grid */}
      <section className="py-12 px-6">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-2xl font-semibold text-center mb-8">What is AdmitMe?</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            {features.map((f) => (
              <FeatureCard key={f.title} icon={f.icon} title={f.title} description={f.description} />
            ))}
          </div>
        </div>
      </section>

      {/* STUDENT PORTAL - primary focus */}
      <section className="py-12 px-6">
        <div className="max-w-4xl mx-auto flex justify-center">
          <Card variant="transparent" className="w-full rounded-2xl shadow-lg p-10 transform hover:scale-105 transition-all duration-300">
            <div className="flex flex-col items-center text-center gap-6">
              <h3 className="text-3xl font-semibold">Student Portal</h3>
              <p className="text-gray-600 max-w-xl">Submit your application, upload documents, and track your admission status in real time.</p>
                <div>
                <Button onClick={() => navigate('/student-login')} variant="red">Student Login</Button>
                </div>
            </div>
          </Card>
        </div>
      </section>
    </div>
  )
}
