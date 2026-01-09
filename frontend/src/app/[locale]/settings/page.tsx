import { PageHeader } from "@/shared/ui/PageHeader";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";
import { Switch } from "@/shared/components/ui/switch";
import { Separator } from "@/shared/components/ui/separator";
import { FormField } from "@/shared/ui/FormField";
import { Settings, User, Bell, Shield, Database } from "lucide-react";

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Settings"
        subtitle="Manage your account and application preferences"
      />

      <div className="grid gap-6 md:grid-cols-2">
        {/* Account Settings */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <User className="h-5 w-5 text-muted-foreground" />
              <CardTitle>Account</CardTitle>
            </div>
            <CardDescription>Update your account information</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <FormField label="Email" required>
              <Input type="email" placeholder="user@example.com" defaultValue="user@example.com" />
            </FormField>
            <FormField label="Display Name">
              <Input type="text" placeholder="Your name" defaultValue="User" />
            </FormField>
            <Button className="w-full">Save Changes</Button>
          </CardContent>
        </Card>

        {/* Preferences */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Bell className="h-5 w-5 text-muted-foreground" />
              <CardTitle>Preferences</CardTitle>
            </div>
            <CardDescription>Customize your experience</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="email-notifications">Email Notifications</Label>
                <p className="text-sm text-muted-foreground">
                  Receive email updates about your generations
                </p>
              </div>
              <Switch id="email-notifications" defaultChecked />
            </div>
            <Separator />
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="dark-mode">Dark Mode</Label>
                <p className="text-sm text-muted-foreground">
                  Switch between light and dark themes
                </p>
              </div>
              <Switch id="dark-mode" />
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

        {/* API & Integration */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Database className="h-5 w-5 text-muted-foreground" />
              <CardTitle>API & Integration</CardTitle>
            </div>
            <CardDescription>Manage API keys and integrations</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <FormField label="API Key" hint="Use this key to access the API">
              <div className="flex gap-2">
                <Input type="password" value="sk-••••••••••••••••" readOnly />
                <Button variant="outline" size="icon">
                  <Settings className="h-4 w-4" />
                </Button>
              </div>
            </FormField>
            <Button variant="outline" className="w-full">
              Regenerate API Key
            </Button>
          </CardContent>
        </Card>

        {/* Security */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Shield className="h-5 w-5 text-muted-foreground" />
              <CardTitle>Security</CardTitle>
            </div>
            <CardDescription>Manage your security settings</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <FormField label="Current Password">
              <Input type="password" />
            </FormField>
            <FormField label="New Password">
              <Input type="password" />
            </FormField>
            <FormField label="Confirm New Password">
              <Input type="password" />
            </FormField>
            <Button className="w-full">Update Password</Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
