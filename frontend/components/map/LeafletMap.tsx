"use client";

import { useEffect, useState } from "react";
import { MapContainer, TileLayer, Marker, Popup, useMap } from "react-leaflet";
import type { LatLngExpression } from "leaflet";
import "leaflet/dist/leaflet.css";
import { Icon } from "leaflet";

// Fix for default marker icons in Next.js
const createIcon = (color: string) => {
  if (typeof window === "undefined") return undefined;

  return new Icon({
    iconUrl: `https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-${color}.png`,
    shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41],
  });
};

const icons = {
  activity: createIcon("blue"),
  accommodation: createIcon("green"),
  restaurant: createIcon("orange"),
  default: createIcon("grey"),
};

export interface MapMarker {
  id: string;
  name: string;
  type: "activity" | "accommodation" | "restaurant" | "other";
  latitude: number;
  longitude: number;
  address?: string;
  description?: string;
}

interface LeafletMapProps {
  markers: MapMarker[];
  center?: LatLngExpression;
  zoom?: number;
  height?: string;
}

function MapBoundsUpdater({ markers }: { markers: MapMarker[] }) {
  const map = useMap();

  useEffect(() => {
    if (markers.length > 0) {
      const bounds = markers
        .filter((m) => m.latitude && m.longitude)
        .map((m) => [m.latitude, m.longitude] as LatLngExpression);

      if (bounds.length > 0) {
        map.fitBounds(bounds, { padding: [50, 50], maxZoom: 15 });
      }
    }
  }, [markers, map]);

  return null;
}

export function LeafletMap({
  markers,
  center = [16.0544, 108.2022], // Center of Vietnam
  zoom = 6,
  height = "500px",
}: LeafletMapProps) {
  const [isMounted, setIsMounted] = useState(false);

  // Only render map on client side
  useEffect(() => {
    setIsMounted(true);
  }, []);

  if (!isMounted) {
    return (
      <div
        style={{ height }}
        className="flex items-center justify-center bg-muted rounded-lg"
      >
        <p className="text-muted-foreground">Dang tai ban do...</p>
      </div>
    );
  }

  return (
    <MapContainer
      center={center}
      zoom={zoom}
      style={{ height, width: "100%", borderRadius: "0.5rem" }}
      className="z-0"
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      {markers
        .filter((marker) => marker.latitude && marker.longitude)
        .map((marker) => (
          <Marker
            key={marker.id}
            position={[marker.latitude, marker.longitude]}
            icon={icons[marker.type] || icons.default}
          >
            <Popup>
              <div className="p-1">
                <h3 className="font-semibold">{marker.name}</h3>
                {marker.address && (
                  <p className="text-sm text-muted-foreground">{marker.address}</p>
                )}
                {marker.description && (
                  <p className="text-sm mt-1">{marker.description}</p>
                )}
                <div className="text-xs mt-2 text-muted-foreground">
                  {marker.latitude.toFixed(4)}, {marker.longitude.toFixed(4)}
                </div>
              </div>
            </Popup>
          </Marker>
        ))}

      <MapBoundsUpdater markers={markers} />
    </MapContainer>
  );
}

export default LeafletMap;
