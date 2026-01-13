"use client";

import { useTranslations } from "next-intl";
import { PageHeader } from "@/shared/ui/PageHeader";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Label } from "@/shared/components/ui/label";
import { Switch } from "@/shared/components/ui/switch";
import { Separator } from "@/shared/components/ui/separator";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { Settings, User, Mail } from "lucide-react";
import { useAuth } from "@/features/auth";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

export default function SettingsPage() {
  const { user, isLoading } = useAuth();
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const t = useTranslations('settings');

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <div className="space-y-6">
      <PageHeader
        title={t('title')}
        subtitle={t('description')}
      />

      <div className="grid gap-6 md:grid-cols-2">
        {/* Account Information */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <User className="h-5 w-5 text-muted-foreground" />
              <CardTitle>Account</CardTitle>
            </div>
            <CardDescription>Your account information from Microsoft</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {isLoading ? (
              <>
                <div className="space-y-2">
                  <Skeleton className="h-4 w-16" />
                  <Skeleton className="h-5 w-48" />
                </div>
                <div className="space-y-2">
                  <Skeleton className="h-4 w-16" />
                  <Skeleton className="h-5 w-32" />
                </div>
                <div className="space-y-2">
                  <Skeleton className="h-4 w-16" />
                  <Skeleton className="h-5 w-40" />
                </div>
              </>
            ) : user ? (
              <>
                <div className="space-y-1">
                  <Label className="text-xs text-muted-foreground">Email</Label>
                  <div className="flex items-center gap-2">
                    <Mail className="h-4 w-4 text-muted-foreground" />
                    <p className="text-sm font-medium">{user.email}</p>
                  </div>
                </div>
                <Separator />
                <div className="space-y-1">
                  <Label className="text-xs text-muted-foreground">Username</Label>
                  <p className="text-sm font-medium">{user.username}</p>
                </div>
                <Separator />
                <div className="space-y-1">
                  <Label className="text-xs text-muted-foreground">Name</Label>
                  <p className="text-sm font-medium">
                    {user.first_name && user.last_name
                      ? `${user.first_name} ${user.last_name}`
                      : user.first_name || user.username}
                  </p>
                </div>
              </>
            ) : (
              <p className="text-sm text-muted-foreground">
                Unable to load account information
              </p>
            )}
          </CardContent>
        </Card>

        {/* Preferences */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Settings className="h-5 w-5 text-muted-foreground" />
              <CardTitle>Preferences</CardTitle>
            </div>
            <CardDescription>Customize your experience</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="dark-mode">Dark Mode</Label>
                <p className="text-sm text-muted-foreground">
                  Switch between light and dark themes
                </p>
              </div>
              <Switch
                id="dark-mode"
                checked={mounted && theme === "dark"}
                onCheckedChange={(checked) => setTheme(checked ? "dark" : "light")}
                disabled={!mounted}
              />
            </div>
            <Separator />
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="auto-refresh">Auto Refresh</Label>
                <p className="text-sm text-muted-foreground">
                  Automatically refresh job status
                </p>
              </div>
              <Switch id="auto-refresh" defaultChecked />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
