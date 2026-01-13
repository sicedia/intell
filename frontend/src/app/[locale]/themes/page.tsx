"use client";

import { useTranslations } from "next-intl";
import { PageHeader } from "@/shared/ui/PageHeader";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Button } from "@/shared/components/ui/button";
import { RadioGroup, RadioGroupItem } from "@/shared/components/ui/radio-group";
import { Label } from "@/shared/components/ui/label";
import { useTheme } from "next-themes";
import { Palette, Moon, Sun, Monitor } from "lucide-react";
import { useEffect, useState } from "react";

export default function ThemesPage() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const t = useTranslations('themes');

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return null;
  }

  const themes = [
    { value: "light", label: "Light", icon: Sun, description: "Clean and bright theme" },
    { value: "dark", label: "Dark", icon: Moon, description: "Easy on the eyes" },
    { value: "system", label: "System", icon: Monitor, description: "Match your OS setting" },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title={t('title')}
        subtitle={t('description')}
      />

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {/* Theme Selection */}
        <Card className="md:col-span-2 lg:col-span-3">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Palette className="h-5 w-5 text-muted-foreground" />
              <CardTitle>Theme Preference</CardTitle>
            </div>
            <CardDescription>Choose how Intell.AI looks to you</CardDescription>
          </CardHeader>
          <CardContent>
            <RadioGroup value={theme} onValueChange={setTheme} className="grid gap-4 md:grid-cols-3">
              {themes.map((themeOption) => {
                const Icon = themeOption.icon;
                return (
                  <div key={themeOption.value}>
                    <RadioGroupItem
                      value={themeOption.value}
                      id={themeOption.value}
                      className="peer sr-only"
                    />
                    <Label
                      htmlFor={themeOption.value}
                      className="flex flex-col items-center justify-between rounded-md border-2 border-muted bg-popover p-4 hover:bg-accent hover:text-accent-foreground peer-data-[state=checked]:border-primary [&:has([data-state=checked])]:border-primary cursor-pointer"
                    >
                      <Icon className="mb-3 h-6 w-6" />
                      <div className="text-center">
                        <div className="font-medium">{themeOption.label}</div>
                        <div className="text-xs text-muted-foreground mt-1">
                          {themeOption.description}
                        </div>
                      </div>
                    </Label>
                  </div>
                );
              })}
            </RadioGroup>
          </CardContent>
        </Card>

        {/* Color Customization (Placeholder) */}
        <Card>
          <CardHeader>
            <CardTitle>Color Palette</CardTitle>
            <CardDescription>Customize accent colors (Coming Soon)</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex gap-2">
              <div className="h-12 w-12 rounded-md bg-primary cursor-pointer hover:scale-110 transition-transform" />
              <div className="h-12 w-12 rounded-md bg-secondary cursor-pointer hover:scale-110 transition-transform" />
              <div className="h-12 w-12 rounded-md bg-accent cursor-pointer hover:scale-110 transition-transform" />
              <div className="h-12 w-12 rounded-md bg-muted cursor-pointer hover:scale-110 transition-transform" />
            </div>
            <p className="text-sm text-muted-foreground mt-4">
              Color customization will be available in a future update.
            </p>
          </CardContent>
        </Card>

        {/* Font Size (Placeholder) */}
        <Card>
          <CardHeader>
            <CardTitle>Typography</CardTitle>
            <CardDescription>Adjust text size (Coming Soon)</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="text-sm">Small</div>
              <div className="text-base">Medium</div>
              <div className="text-lg">Large</div>
            </div>
            <p className="text-sm text-muted-foreground mt-4">
              Font size customization coming soon.
            </p>
          </CardContent>
        </Card>

        {/* Preview */}
        <Card>
          <CardHeader>
            <CardTitle>Preview</CardTitle>
            <CardDescription>See how your theme looks</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 p-4 rounded-lg border bg-card">
              <div className="h-4 bg-primary rounded w-3/4" />
              <div className="h-4 bg-muted rounded w-1/2" />
              <div className="flex gap-2 mt-4">
                <Button size="sm">Primary</Button>
                <Button size="sm" variant="outline">
                  Secondary
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
