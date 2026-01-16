"use client";

/**
 * Login form component.
 *
 * Microsoft OAuth2 login only.
 */
import { useSearchParams } from "next/navigation";
import { useTranslations } from "next-intl";
import { MicrosoftLoginButton } from "./MicrosoftLoginButton";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/shared/components/ui/card";

interface LoginFormProps {
  onSuccess?: () => void;
}

export function LoginForm({ onSuccess }: LoginFormProps = {}) {
  const searchParams = useSearchParams();
  const t = useTranslations('auth');

  // Check for OAuth error in URL params (from Microsoft callback)
  const error = searchParams.get("error");
  const errorDescription = searchParams.get("error_description");
  const serverError = error
    ? errorDescription || `${t('authenticationFailed')}: ${error}`
    : null;

  return (
    <Card className="w-full max-w-md">
      <CardHeader className="space-y-1 text-center">
        <CardTitle className="text-2xl font-bold">{t('welcome')}</CardTitle>
        <CardDescription>
          {t('signIn')}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {serverError && (
          <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive text-center">
            {serverError}
          </div>
        )}

        <MicrosoftLoginButton className="w-full" />

        <p className="text-xs text-center text-muted-foreground">
          {t('termsOfService')}
        </p>
      </CardContent>
    </Card>
  );
}
