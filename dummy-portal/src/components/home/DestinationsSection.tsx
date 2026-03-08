import DestinationCard from './DestinationCard';

const destinations = [
    {
        image: 'https://images.unsplash.com/photo-1584660470766-20ac1a28c7fe?auto=format&fit=crop&q=80&w=800',
        alt: 'Tokyo',
        city: 'Tokyo',
        dates: '24 Dec 2025 - 07 Jan 2026',
        priceLabel: 'Economy From',
        price: 'USD $450',
    },
    {
        image: 'https://images.unsplash.com/photo-1541336032412-2048a678540d?auto=format&fit=crop&q=80&w=800',
        alt: 'New York',
        city: 'New York',
        dates: '24 Dec 2025 - 07 Jan 2026',
        priceLabel: 'Economy From',
        price: 'USD $249',
    },
    {
        image: 'https://images.unsplash.com/photo-1518684079-3c830dcef090?auto=format&fit=crop&q=80&w=800',
        alt: 'Dubai',
        city: 'Dubai',
        dates: '24 Dec 2025 - 07 Jan 2026',
        priceLabel: 'Economy From',
        price: 'USD $310',
    },
];

export default function DestinationsSection() {
    return (
        <section className="pb-20 px-4 max-w-6xl mx-auto">
            <div className="text-center mb-12">
                <h2 className="text-5xl font-bold text-content mb-4">Explore Top Destinations</h2>
                <p className="text-content-light">Get Exclusive Flight Deals To Your Favorite Cities.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {destinations.map((dest) => (
                    <DestinationCard key={dest.city} {...dest} />
                ))}
            </div>
        </section>
    );
}
