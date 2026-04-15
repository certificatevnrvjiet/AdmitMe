import React from 'react'

export default function FeatureCard({ icon, title, description }) {
  const ref = React.useRef()
  const [visible, setVisible] = React.useState(false)

  React.useEffect(() => {
    const el = ref.current
    if (!el) return
    const obs = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setVisible(true)
            obs.unobserve(el)
          }
        })
      },
      { threshold: 0.15 }
    )
    obs.observe(el)
    return () => obs.disconnect()
  }, [])

  return (
    <div
      ref={ref}
      className={`bg-white rounded-2xl shadow-md p-6 flex flex-col gap-3 transition-all duration-500 transform ${
        visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'
      }`}
    >
      <div className="w-12 h-12 flex items-center justify-center rounded-lg bg-red-50 text-red-600">{icon}</div>
      <h4 className="text-lg font-semibold">{title}</h4>
      <p className="text-gray-600 text-sm">{description}</p>
    </div>
  )
}
