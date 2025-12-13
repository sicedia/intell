import { getTranslations } from "next-intl/server";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/components/ui/card";

export default async function DashboardPage() {
  const t = await getTranslations("dashboard");

  return (
    <div className="container mx-auto p-6">
      <Card>
        <CardHeader>
          <CardTitle>{t("title")}</CardTitle>
          <CardDescription>{t("welcome")}</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            Dashboard content will be implemented here.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
