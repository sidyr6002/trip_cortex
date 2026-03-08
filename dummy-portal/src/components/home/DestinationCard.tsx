interface DestinationCardProps {
    image: string;
    alt: string;
    city: string;
    dates: string;
    priceLabel: string;
    price: string;
}

export default function DestinationCard({ image, alt, city, dates, priceLabel, price }: DestinationCardProps) {
    return (
        <div className="group destination-card">
            <img
                src={image}
                alt={alt}
                className="destination-img"
            />
            <div className="destination-overlay" />
            <div className="destination-content">
                <div>
                    <h3 className="text-3xl font-bold text-white mb-2">{city}</h3>
                    <p className="text-content-on-dark text-sm font-medium">{dates}</p>
                </div>
                <div className="text-right">
                    <p className="text-content-on-dark text-xs font-medium mb-1">{priceLabel}</p>
                    <p className="text-2xl font-bold text-white">{price}</p>
                </div>
            </div>
        </div>
    );
}
