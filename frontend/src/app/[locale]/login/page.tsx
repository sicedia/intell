"use client";

/**
 * Login page.
 *
 * Displays the login form and handles successful authentication redirect.
 */
import { useRouter, useSearchParams } from "next/navigation";
import { LoginForm } from "@/features/auth";

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const callbackUrl = searchParams.get("callbackUrl") || "/dashboard";

  const handleLoginSuccess = () => {
    // Redirect to callback URL or dashboard
    router.push(callbackUrl);
    router.refresh(); // Refresh to update server components
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <LoginForm onSuccess={handleLoginSuccess} />
    </div>
  );
}
