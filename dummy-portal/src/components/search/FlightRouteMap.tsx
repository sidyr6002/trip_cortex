import { useEffect } from 'react';
import { MapContainer, TileLayer, CircleMarker, Polyline, Tooltip, useMap } from 'react-leaflet';
import type { LatLngBoundsExpression } from 'leaflet';
import greatCircle from '@turf/great-circle';
import { point } from '@turf/helpers';
import 'leaflet/dist/leaflet.css';

interface FlightRouteMapProps {
  airports: Array<{
    code: string;
    cityName: string;
    lat: number;
    lng: number;
  }>;
}

const ROUTE_STYLE = { color: '#3957d7', weight: 2, opacity: 0.6, dashArray: '8 6' };
const DEPARTURE_STYLE = { fillColor: '#3957d7', color: '#ffffff', weight: 2, opacity: 1, fillOpacity: 1 };
const ARRIVAL_STYLE = { fillColor: '#ffffff', color: '#3957d7', weight: 2, opacity: 1, fillOpacity: 1 };
const LAYOVER_STYLE = { fillColor: '#ffffff', color: '#3957d7', weight: 2, opacity: 1, fillOpacity: 0.8 };

function FitBoundsHelper({ bounds }: { bounds: LatLngBoundsExpression }) {
  const map = useMap();
  useEffect(() => {
    map.fitBounds(bounds, { padding: [50, 50] });
  }, [map, bounds]);
  return null;
}

export function FlightRouteMap({ airports }: FlightRouteMapProps) {
  if (airports.length === 0) return null;

  const bounds: LatLngBoundsExpression = airports.map(a => [a.lat, a.lng] as [number, number]);
  const center: [number, number] = [airports[0].lat, airports[0].lng];

  const routeSegments = [];
  for (let i = 0; i < airports.length - 1; i++) {
    const start = point([airports[i].lng, airports[i].lat]);
    const end = point([airports[i + 1].lng, airports[i + 1].lat]);
    const line = greatCircle(start, end, { npoints: 50 });
    const leafletCoords = line.geometry.coordinates.map(c => [c[1], c[0]] as [number, number]);
    routeSegments.push(leafletCoords);
  }

  return (
    <MapContainer
      center={center}
      zoom={4}
      scrollWheelZoom={false}
      zoomControl={true}
      attributionControl={false}
      className="w-full h-full rounded-2xl border border-divider-light"
      style={{ minHeight: '256px' }}
    >
      <TileLayer
        url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
      />
      <FitBoundsHelper bounds={bounds} />

      {routeSegments.map((segment, idx) => (
        <Polyline key={`route-${idx}`} positions={segment} pathOptions={ROUTE_STYLE} />
      ))}

      {airports.map((airport, idx) => {
        const isDeparture = idx === 0;
        const isArrival = idx === airports.length - 1;
        const isLayover = !isDeparture && !isArrival;

        return (
          <CircleMarker
            key={airport.code}
            center={[airport.lat, airport.lng]}
            radius={isLayover ? 5 : 7}
            pathOptions={isDeparture ? DEPARTURE_STYLE : isArrival ? ARRIVAL_STYLE : LAYOVER_STYLE}
          >
            <Tooltip permanent direction="top" offset={[0, -10]} className="text-xs font-semibold">
              {airport.cityName}
            </Tooltip>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
}
