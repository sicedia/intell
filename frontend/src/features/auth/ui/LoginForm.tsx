"use client";

/**
 * Login form component.
 *
 * Microsoft OAuth2 login only.
 */
import { useSearchParams } from "next/navigation";
import { MicrosoftLoginButton } from "./MicrosoftLoginButton";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/shared/components/ui/card";

export function LoginForm() {
  const searchParams = useSearchParams();

  // Check for OAuth error in URL params (from Microsoft callback)
  const error = searchParams.get("error");
  const errorDescription = searchParams.get("error_description");
  const serverError = error
    ? errorDescription || `Authentication failed: ${error}`
    : null;

  return (
    <Card className="w-full max-w-md">
      <CardHeader className="space-y-1 text-center">
        <CardTitle className="text-2xl font-bold">Welcome</CardTitle>
        <CardDescription>
          Sign in to continue to your account
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
          By signing in, you agree to our terms of service and privacy policy.
        </p>
      </CardContent>
    </Card>
  );
}
