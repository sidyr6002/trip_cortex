import { createFileRoute } from '@tanstack/react-router'
import Navbar from '../components/home/Navbar'
import HeroSection from '../components/home/HeroSection'
import DestinationsSection from '../components/home/DestinationsSection'

export const Route = createFileRoute('/')({ component: App })

function App() {
  return (
    <div className="min-h-screen bg-linear-to-b from-primary-100 via-primary-50 to-white font-sans text-content overflow-x-hidden">
      <Navbar />
      <HeroSection />
      <DestinationsSection />
    </div>
  )
}
