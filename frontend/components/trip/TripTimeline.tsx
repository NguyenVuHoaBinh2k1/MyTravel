"use client";

import { TripActivity } from "@/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface TripTimelineProps {
  activities: TripActivity[];
  startDate: string;
}

export function TripTimeline({ activities, startDate }: TripTimelineProps) {
  // Group activities by day
  const activitiesByDay = activities.reduce((acc, activity) => {
    const day = activity.day_number;
    if (!acc[day]) {
      acc[day] = [];
    }
    acc[day].push(activity);
    return acc;
  }, {} as Record<number, TripActivity[]>);

  // Sort days
  const days = Object.keys(activitiesByDay)
    .map(Number)
    .sort((a, b) => a - b);

  if (activities.length === 0) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <p className="text-muted-foreground">
            Chua co lich trinh. Su dung tro ly AI de lap lich trinh!
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {days.map((day) => (
        <Card key={day}>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">
              Ngay {day} - {getDayDate(startDate, day)}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="relative">
              {/* Timeline line */}
              <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-border" />

              {/* Activities */}
              <div className="space-y-4">
                {activitiesByDay[day]
                  .sort((a, b) => a.start_time.localeCompare(b.start_time))
                  .map((activity, index) => (
                    <div key={activity.id} className="relative pl-10">
                      {/* Timeline dot */}
                      <div
                        className={`absolute left-2.5 top-1.5 w-3 h-3 rounded-full border-2 ${
                          activity.status === "completed"
                            ? "bg-primary border-primary"
                            : "bg-background border-primary"
                        }`}
                      />

                      {/* Activity content */}
                      <div className="bg-muted rounded-lg p-3">
                        <div className="flex justify-between items-start">
                          <div>
                            <div className="font-medium">{activity.name}</div>
                            <div className="text-sm text-muted-foreground">
                              {activity.location}
                            </div>
                          </div>
                          <div className="text-sm text-muted-foreground">
                            {activity.start_time} - {activity.end_time}
                          </div>
                        </div>

                        {activity.description && (
                          <p className="text-sm mt-2">{activity.description}</p>
                        )}

                        <div className="flex gap-4 mt-2 text-xs text-muted-foreground">
                          {activity.duration_minutes && (
                            <span>{activity.duration_minutes} phut</span>
                          )}
                          {activity.price && (
                            <span>
                              {formatCurrency(activity.price)} {activity.currency}
                            </span>
                          )}
                          {activity.rating && (
                            <span>{activity.rating}/5</span>
                          )}
                        </div>

                        <div className="mt-2">
                          <span
                            className={`text-xs px-2 py-0.5 rounded ${getCategoryColor(
                              activity.category
                            )}`}
                          >
                            {getCategoryLabel(activity.category)}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function getDayDate(startDate: string, dayNumber: number): string {
  const date = new Date(startDate);
  date.setDate(date.getDate() + dayNumber - 1);
  return date.toLocaleDateString("vi-VN", {
    weekday: "long",
    day: "2-digit",
    month: "2-digit",
  });
}

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat("vi-VN").format(amount);
}

function getCategoryLabel(category: string): string {
  const labels: Record<string, string> = {
    sightseeing: "Tham quan",
    food: "An uong",
    transport: "Di chuyen",
    accommodation: "Nhi ngoi",
    activity: "Hoat dong",
    shopping: "Mua sam",
  };
  return labels[category] || category;
}

function getCategoryColor(category: string): string {
  const colors: Record<string, string> = {
    sightseeing: "bg-blue-100 text-blue-800",
    food: "bg-orange-100 text-orange-800",
    transport: "bg-purple-100 text-purple-800",
    accommodation: "bg-green-100 text-green-800",
    activity: "bg-pink-100 text-pink-800",
    shopping: "bg-yellow-100 text-yellow-800",
  };
  return colors[category] || "bg-gray-100 text-gray-800";
}

export default TripTimeline;
