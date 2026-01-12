"use client";

/**
 * Microsoft Sign-In Button Component.
 *
 * Initiates the Microsoft OAuth2 flow by redirecting to the backend endpoint.
 * The backend handles the redirect URL configuration via MICROSOFT_LOGIN_REDIRECT_URL.
 */
import { useState } from "react";
import { Button } from "@/shared/components/ui/button";
import { env } from "@/shared/lib/env";

interface MicrosoftLoginButtonProps {
  /** Additional CSS classes */
  className?: string;
  /** Disabled state */
  disabled?: boolean;
}

export function MicrosoftLoginButton({
  className,
  disabled = false,
}: MicrosoftLoginButtonProps) {
  const [isLoading, setIsLoading] = useState(false);

  const handleMicrosoftLogin = () => {
    setIsLoading(true);

    // Build the Microsoft login URL - backend handles redirect configuration
    const baseUrl = env.NEXT_PUBLIC_API_BASE_URL.replace(/\/api\/?$/, "");
    const loginUrl = `${baseUrl}/api/auth/microsoft/login/`;

    // Redirect to backend Microsoft login endpoint
    window.location.href = loginUrl;
  };

  return (
    <Button
      type="button"
      variant="outline"
      onClick={handleMicrosoftLogin}
      disabled={disabled || isLoading}
      className={className}
    >
      {isLoading ? (
        "Redirecting..."
      ) : (
        <>
          <MicrosoftIcon className="mr-2 h-4 w-4" />
          Sign in with Microsoft
        </>
      )}
    </Button>
  );
}

/**
 * Microsoft logo icon
 */
function MicrosoftIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 21 21"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <rect x="1" y="1" width="9" height="9" fill="#F25022" />
      <rect x="11" y="1" width="9" height="9" fill="#7FBA00" />
      <rect x="1" y="11" width="9" height="9" fill="#00A4EF" />
      <rect x="11" y="11" width="9" height="9" fill="#FFB900" />
    </svg>
  );
}
