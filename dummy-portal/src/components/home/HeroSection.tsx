import SearchWidget from './SearchWidget'

export default function HeroSection() {
    return (
        <main className="relative pt-16 pb-32 px-4">
            {/* Background Gradient handles by index.tsx */}

            <div className="max-w-7xl mx-auto text-center relative flex flex-col items-center">
                {/* Top Section: Text */}
                <div className="w-full">
                    <h1 className="hero-title">Smart Flight Finder</h1>
                    <p className="hero-subtitle">
                        Discover a smarter way to fly — easy booking, reliable service, and
                        a journey designed around your comfort.
                    </p>
                </div>

                {/* Bottom Section: Airplane Image and Search Widget */}
                <div className="relative w-full -mt-24">
                    {/* Airplane Image */}
                    <div className="relative w-full -ml-8 z-20 pointer-events-none drop-shadow-2xl">
                        <img
                            src="/airplane.webp"
                            alt="Airplane"
                            className="w-full h-auto object-contain"
                            fetchPriority="high"
                            loading="eager"
                        />
                    </div>

                    {/* Search Widget */}
                    <SearchWidget />
                </div>
            </div>
        </main>
    )
}
