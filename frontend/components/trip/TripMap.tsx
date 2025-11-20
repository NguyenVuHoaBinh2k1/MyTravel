"use client";

import { TripActivity, TripAccommodation, TripRestaurant } from "@/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface TripMapProps {
  activities?: TripActivity[];
  accommodations?: TripAccommodation[];
  restaurants?: TripRestaurant[];
  destination: string;
}

interface MapMarker {
  id: string;
  name: string;
  type: "activity" | "accommodation" | "restaurant";
  latitude?: number;
  longitude?: number;
  address?: string;
}

export function TripMap({
  activities = [],
  accommodations = [],
  restaurants = [],
  destination,
}: TripMapProps) {
  // Collect all markers
  const markers: MapMarker[] = [
    ...activities.map((a) => ({
      id: a.id,
      name: a.name,
      type: "activity" as const,
      latitude: a.latitude,
      longitude: a.longitude,
      address: a.location,
    })),
    ...accommodations.map((a) => ({
      id: a.id,
      name: a.name,
      type: "accommodation" as const,
      latitude: a.latitude,
      longitude: a.longitude,
      address: a.address,
    })),
    ...restaurants.map((r) => ({
      id: r.id,
      name: r.name,
      type: "restaurant" as const,
      latitude: r.latitude,
      longitude: r.longitude,
      address: r.address,
    })),
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Ban do - {destination}</CardTitle>
      </CardHeader>
      <CardContent>
        {/* Map placeholder - can be replaced with real map component */}
        <div className="aspect-video bg-muted rounded-lg mb-4 flex items-center justify-center">
          <div className="text-center text-muted-foreground">
            <MapIcon className="h-12 w-12 mx-auto mb-2" />
            <p>Tich hop ban do Google Maps</p>
            <p className="text-xs mt-1">
              {markers.length} dia diem da duoc danh dau
            </p>
          </div>
        </div>

        {/* Locations list */}
        {markers.length > 0 ? (
          <div className="space-y-3 max-h-[300px] overflow-y-auto">
            {markers.map((marker) => (
              <div
                key={`${marker.type}-${marker.id}`}
                className="flex items-start gap-3 p-2 rounded hover:bg-muted"
              >
                <div className={`p-1.5 rounded ${getMarkerColor(marker.type)}`}>
                  {getMarkerIcon(marker.type)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-sm truncate">
                    {marker.name}
                  </div>
                  {marker.address && (
                    <div className="text-xs text-muted-foreground truncate">
                      {marker.address}
                    </div>
                  )}
                  {marker.latitude && marker.longitude && (
                    <div className="text-xs text-muted-foreground">
                      {marker.latitude.toFixed(4)}, {marker.longitude.toFixed(4)}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-center text-muted-foreground py-4">
            Chua co dia diem nao duoc them vao. Su dung tro ly AI de tim dia
            diem!
          </p>
        )}
      </CardContent>
    </Card>
  );
}

function getMarkerColor(type: string): string {
  const colors: Record<string, string> = {
    activity: "bg-blue-100 text-blue-600",
    accommodation: "bg-green-100 text-green-600",
    restaurant: "bg-orange-100 text-orange-600",
  };
  return colors[type] || "bg-gray-100 text-gray-600";
}

function getMarkerIcon(type: string) {
  switch (type) {
    case "activity":
      return <CameraIcon className="h-4 w-4" />;
    case "accommodation":
      return <BedIcon className="h-4 w-4" />;
    case "restaurant":
      return <UtensilsIcon className="h-4 w-4" />;
    default:
      return <MapPinIcon className="h-4 w-4" />;
  }
}

function MapIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"
      />
    </svg>
  );
}

function MapPinIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
      />
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
      />
    </svg>
  );
}

function CameraIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"
      />
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"
      />
    </svg>
  );
}

function BedIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
      />
    </svg>
  );
}

function UtensilsIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
      />
    </svg>
  );
}

export default TripMap;
