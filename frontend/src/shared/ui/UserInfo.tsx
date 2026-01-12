"use client";

import React from "react";
import { User } from "lucide-react";
import { cn } from "@/shared/lib/utils";

interface UserInfoProps {
  username?: string | null;
  email?: string | null;
  userId?: number | null;
  className?: string;
  variant?: "default" | "compact" | "minimal";
  showIcon?: boolean;
}

/**
 * Component to display user information (username/email)
 * Reusable across cards and detail views
 */
export function UserInfo({
  username,
  email,
  userId,
  className,
  variant = "default",
  showIcon = false,
}: UserInfoProps) {
  const displayName = username || email || "No disponible";
  const displayText = email && username ? `${username} (${email})` : displayName;

  if (variant === "minimal") {
    return (
      <span className={cn("text-xs text-muted-foreground", className)}>
        {displayName}
      </span>
    );
  }

  if (variant === "compact") {
    return (
      <div className={cn("flex items-center gap-1.5 text-xs text-muted-foreground", className)}>
        {showIcon && <User className="h-3 w-3" />}
        <span className="truncate" title={displayText}>
          {displayName}
        </span>
      </div>
    );
  }

  // Default variant
  return (
    <div className={cn("flex items-center gap-2 text-xs text-muted-foreground", className)}>
      {showIcon && <User className="h-3.5 w-3.5" />}
      <div className="flex flex-col min-w-0">
        {username && (
          <span className="font-medium text-foreground truncate" title={username}>
            {username}
          </span>
        )}
        {email && (
          <span className="truncate" title={email}>
            {email}
          </span>
        )}
        {!username && !email && (
          <span className="truncate text-muted-foreground italic">No disponible</span>
        )}
      </div>
    </div>
  );
}
