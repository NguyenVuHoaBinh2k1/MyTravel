"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { tripsApi } from "@/lib/api";
import { Trip } from "@/types";
import { ChatInterface } from "@/components/chat";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function TripDashboard() {
  const params = useParams();
  const tripId = params.id as string;

  const [trip, setTrip] = useState<Trip | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"chat" | "itinerary" | "map" | "budget">("chat");

  useEffect(() => {
    const loadTrip = async () => {
      try {
        setLoading(true);
        const tripData = await tripsApi.getTrip(tripId);
        setTrip(tripData);
      } catch (err) {
        setError("Khong the tai thong tin chuyen di");
        console.error("Failed to load trip:", err);
      } finally {
        setLoading(false);
      }
    };

    if (tripId) {
      loadTrip();
    }
  }, [tripId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto" />
          <p className="mt-4 text-muted-foreground">Dang tai...</p>
        </div>
      </div>
    );
  }

  if (error || !trip) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-destructive">{error || "Khong tim thay chuyen di"}</p>
          <Button className="mt-4" onClick={() => window.history.back()}>
            Quay lai
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-6">
      {/* Trip Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold">{trip.title}</h1>
        <div className="flex items-center gap-4 mt-2 text-muted-foreground">
          <span>{trip.destination}</span>
          <span>|</span>
          <span>
            {formatDate(trip.start_date)} - {formatDate(trip.end_date)}
          </span>
          <span>|</span>
          <span>{trip.travelers_count} nguoi</span>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex gap-2 mb-6 border-b">
        <TabButton
          active={activeTab === "chat"}
          onClick={() => setActiveTab("chat")}
        >
          Tro ly AI
        </TabButton>
        <TabButton
          active={activeTab === "itinerary"}
          onClick={() => setActiveTab("itinerary")}
        >
          Lich trinh
        </TabButton>
        <TabButton
          active={activeTab === "map"}
          onClick={() => setActiveTab("map")}
        >
          Ban do
        </TabButton>
        <TabButton
          active={activeTab === "budget"}
          onClick={() => setActiveTab("budget")}
        >
          Ngan sach
        </TabButton>
      </div>

      {/* Tab Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2">
          {activeTab === "chat" && (
            <div className="h-[600px]">
              <ChatInterface
                tripId={parseInt(tripId)}
                title={`Tro ly - ${trip.destination}`}
              />
            </div>
          )}

          {activeTab === "itinerary" && (
            <Card>
              <CardHeader>
                <CardTitle>Lich trinh</CardTitle>
              </CardHeader>
              <CardContent>
                {trip.activities && trip.activities.length > 0 ? (
                  <div className="space-y-4">
                    {trip.activities.map((activity) => (
                      <div
                        key={activity.id}
                        className="p-4 border rounded-lg"
                      >
                        <div className="font-medium">{activity.name}</div>
                        <div className="text-sm text-muted-foreground">
                          {activity.location}
                        </div>
                        <div className="text-sm">
                          Ngay {activity.day_number}: {activity.start_time} -{" "}
                          {activity.end_time}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-muted-foreground text-center py-8">
                    Chua co lich trinh. Su dung tro ly AI de lap lich trinh!
                  </p>
                )}
              </CardContent>
            </Card>
          )}

          {activeTab === "map" && (
            <Card>
              <CardHeader>
                <CardTitle>Ban do</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="aspect-video bg-muted rounded-lg flex items-center justify-center">
                  <p className="text-muted-foreground">
                    Ban do se duoc hien thi o day
                  </p>
                </div>
              </CardContent>
            </Card>
          )}

          {activeTab === "budget" && (
            <Card>
              <CardHeader>
                <CardTitle>Ngan sach</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center p-4 bg-muted rounded-lg">
                    <span className="font-medium">Tong ngan sach</span>
                    <span className="text-xl font-bold">
                      {formatCurrency(trip.budget)} {trip.currency}
                    </span>
                  </div>

                  {trip.expenses && trip.expenses.length > 0 ? (
                    <div className="space-y-2">
                      {trip.expenses.map((expense) => (
                        <div
                          key={expense.id}
                          className="flex justify-between p-3 border rounded"
                        >
                          <div>
                            <div className="font-medium">
                              {expense.description}
                            </div>
                            <div className="text-sm text-muted-foreground">
                              {expense.category}
                            </div>
                          </div>
                          <div className="font-medium">
                            {formatCurrency(expense.amount)} {expense.currency}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-muted-foreground text-center py-4">
                      Chua co chi phi nao duoc ghi nhan
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Quick Stats */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Thong tin chuyen di</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <StatItem label="Trang thai" value={getStatusLabel(trip.status)} />
              <StatItem
                label="So ngay"
                value={`${calculateDays(trip.start_date, trip.end_date)} ngay`}
              />
              <StatItem
                label="Ngan sach"
                value={`${formatCurrency(trip.budget)} ${trip.currency}`}
              />
              <StatItem
                label="So nguoi"
                value={`${trip.travelers_count} nguoi`}
              />
            </CardContent>
          </Card>

          {/* Accommodations */}
          {trip.accommodations && trip.accommodations.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Cho o</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {trip.accommodations.map((acc) => (
                    <div key={acc.id} className="text-sm">
                      <div className="font-medium">{acc.name}</div>
                      <div className="text-muted-foreground">{acc.address}</div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Restaurants */}
          {trip.restaurants && trip.restaurants.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Nha hang</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {trip.restaurants.map((rest) => (
                    <div key={rest.id} className="text-sm">
                      <div className="font-medium">{rest.name}</div>
                      <div className="text-muted-foreground">
                        {rest.cuisine_type}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`px-4 py-2 text-sm font-medium transition-colors ${
        active
          ? "text-primary border-b-2 border-primary"
          : "text-muted-foreground hover:text-foreground"
      }`}
    >
      {children}
    </button>
  );
}

function StatItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between text-sm">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  );
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat("vi-VN").format(amount);
}

function calculateDays(start: string, end: string): number {
  const startDate = new Date(start);
  const endDate = new Date(end);
  const diffTime = Math.abs(endDate.getTime() - startDate.getTime());
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
}

function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    planning: "Dang len ke hoach",
    booked: "Da dat",
    ongoing: "Dang di",
    completed: "Hoan thanh",
    cancelled: "Da huy",
  };
  return labels[status] || status;
}
