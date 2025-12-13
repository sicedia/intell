import { getTranslations } from "next-intl/server";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/components/ui/card";

export default async function SettingsPage() {
  const t = await getTranslations("settings");

  return (
    <div className="container mx-auto p-6">
      <Card>
        <CardHeader>
          <CardTitle>{t("title")}</CardTitle>
          <CardDescription>{t("description")}</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            Settings features will be implemented here.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
