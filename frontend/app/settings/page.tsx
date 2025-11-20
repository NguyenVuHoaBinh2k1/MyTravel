"use client";

import { useState, useEffect } from "react";
import { useAuthStore } from "@/stores/authStore";
import { authApi } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export default function SettingsPage() {
  const user = useAuthStore((state) => state.user);
  const [loading, setLoading] = useState(false);
  const [saved, setSaved] = useState(false);

  const [formData, setFormData] = useState({
    full_name: "",
    email: "",
    phone: "",
    language: "vi" as "vi" | "en",
    currency: "VND",
  });

  useEffect(() => {
    if (user) {
      setFormData({
        full_name: user.full_name || "",
        email: user.email || "",
        phone: user.phone || "",
        language: user.preferences?.language || "vi",
        currency: user.preferences?.currency || "VND",
      });
    }
  }, [user]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setSaved(false);

    try {
      // Update user profile - this would need to be implemented in the API
      // await authApi.updateProfile(formData);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (error) {
      console.error("Failed to update settings:", error);
      alert("Khong the cap nhat cai dat");
    } finally {
      setLoading(false);
    }
  };

  if (!user) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-muted-foreground">Vui long dang nhap</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-6 max-w-4xl">
      <h1 className="text-3xl font-bold mb-6">Cai dat</h1>

      <div className="space-y-6">
        {/* Profile Settings */}
        <Card>
          <CardHeader>
            <CardTitle>Thong tin ca nhan</CardTitle>
            <CardDescription>
              Cap nhat thong tin tai khoan cua ban
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="text-sm font-medium">Ten day du</label>
                <Input
                  value={formData.full_name}
                  onChange={(e) =>
                    setFormData({ ...formData, full_name: e.target.value })
                  }
                  className="mt-1"
                />
              </div>

              <div>
                <label className="text-sm font-medium">Email</label>
                <Input
                  type="email"
                  value={formData.email}
                  onChange={(e) =>
                    setFormData({ ...formData, email: e.target.value })
                  }
                  className="mt-1"
                  disabled
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Email khong the thay doi
                </p>
              </div>

              <div>
                <label className="text-sm font-medium">So dien thoai</label>
                <Input
                  value={formData.phone}
                  onChange={(e) =>
                    setFormData({ ...formData, phone: e.target.value })
                  }
                  className="mt-1"
                  placeholder="0912345678"
                />
              </div>

              <div className="flex gap-4">
                <Button type="submit" disabled={loading}>
                  {loading ? "Dang luu..." : "Luu thay doi"}
                </Button>
                {saved && (
                  <span className="text-sm text-green-600 self-center">
                    Da luu!
                  </span>
                )}
              </div>
            </form>
          </CardContent>
        </Card>

        {/* Preferences */}
        <Card>
          <CardHeader>
            <CardTitle>Tuy chon</CardTitle>
            <CardDescription>
              Tuy chinh cach ung dung hien thi thong tin
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium">Ngon ngu</label>
              <select
                value={formData.language}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    language: e.target.value as "vi" | "en",
                  })
                }
                className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <option value="vi">Tieng Viet</option>
                <option value="en">English</option>
              </select>
            </div>

            <div>
              <label className="text-sm font-medium">Don vi tien te</label>
              <select
                value={formData.currency}
                onChange={(e) =>
                  setFormData({ ...formData, currency: e.target.value })
                }
                className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <option value="VND">VND (Vietnam Dong)</option>
                <option value="USD">USD (US Dollar)</option>
                <option value="EUR">EUR (Euro)</option>
              </select>
            </div>
          </CardContent>
        </Card>

        {/* Account Actions */}
        <Card>
          <CardHeader>
            <CardTitle>Tai khoan</CardTitle>
            <CardDescription>
              Quan ly tai khoan va du lieu cua ban
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <h3 className="text-sm font-medium mb-2">Xuat du lieu</h3>
              <p className="text-sm text-muted-foreground mb-3">
                Tai xuong tat ca du lieu chuyen di cua ban
              </p>
              <Button variant="outline" size="sm">
                Xuat du lieu
              </Button>
            </div>

            <div className="pt-4 border-t">
              <h3 className="text-sm font-medium mb-2 text-destructive">
                Vung nguy hiem
              </h3>
              <p className="text-sm text-muted-foreground mb-3">
                Xoa tai khoan se xoa vinh vien tat ca du lieu cua ban
              </p>
              <Button variant="destructive" size="sm">
                Xoa tai khoan
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
