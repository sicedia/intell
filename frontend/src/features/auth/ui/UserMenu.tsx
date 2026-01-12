"use client";

/**
 * User Menu Component.
 *
 * Displays the authenticated user's avatar and a dropdown menu
 * with user info and actions (logout, etc.).
 */
import { useRouter } from "next/navigation";
import { LogOut, Settings, ChevronDown } from "lucide-react";
import { useAuth } from "../hooks/useAuth";
import {
  Avatar,
  AvatarFallback,
  AvatarImage,
} from "@/shared/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/shared/components/ui/dropdown-menu";
import { Button } from "@/shared/components/ui/button";
import { Skeleton } from "@/shared/components/ui/skeleton";

interface UserMenuProps {
  /** Show user name next to avatar */
  showName?: boolean;
  /** Additional CSS classes */
  className?: string;
}

export function UserMenu({ showName = false, className }: UserMenuProps) {
  const router = useRouter();
  const { user, isAuthenticated, isLoading, logout, isLoggingOut } = useAuth();

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center gap-2">
        <Skeleton className="h-8 w-8 rounded-full" />
        {showName && <Skeleton className="h-4 w-20" />}
      </div>
    );
  }

  // Not authenticated - don't render anything
  if (!isAuthenticated || !user) {
    return null;
  }

  // Get user initials for avatar fallback
  const getInitials = (): string => {
    if (user.first_name && user.last_name) {
      return `${user.first_name[0]}${user.last_name[0]}`.toUpperCase();
    }
    if (user.first_name) {
      return user.first_name.substring(0, 2).toUpperCase();
    }
    if (user.username) {
      return user.username.substring(0, 2).toUpperCase();
    }
    return "U";
  };

  // Get display name
  const getDisplayName = (): string => {
    if (user.first_name && user.last_name) {
      return `${user.first_name} ${user.last_name}`;
    }
    if (user.first_name) {
      return user.first_name;
    }
    return user.username;
  };

  const handleLogout = async () => {
    try {
      await logout();
      router.push("/login");
    } catch (error) {
      // Error handling is done in the hook
      console.error("Logout failed:", error);
    }
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          className={`relative h-auto p-1.5 hover:bg-accent ${className ?? ""}`}
        >
          <div className="flex items-center gap-2">
            <Avatar className="h-8 w-8">
              <AvatarImage
                src={undefined} // Could be user.avatar_url if available
                alt={getDisplayName()}
              />
              <AvatarFallback className="bg-primary text-primary-foreground text-xs font-medium">
                {getInitials()}
              </AvatarFallback>
            </Avatar>
            {showName && (
              <span className="text-sm font-medium hidden sm:inline-block max-w-[120px] truncate">
                {getDisplayName()}
              </span>
            )}
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          </div>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-56" align="end" forceMount>
        <DropdownMenuLabel className="font-normal">
          <div className="flex flex-col space-y-1">
            <p className="text-sm font-medium leading-none">{getDisplayName()}</p>
            <p className="text-xs leading-none text-muted-foreground">
              {user.email}
            </p>
          </div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuGroup>
          <DropdownMenuItem
            onClick={() => router.push("/settings")}
            className="cursor-pointer"
          >
            <Settings className="mr-2 h-4 w-4" />
            <span>Settings</span>
          </DropdownMenuItem>
        </DropdownMenuGroup>
        <DropdownMenuSeparator />
        <DropdownMenuItem
          onClick={handleLogout}
          disabled={isLoggingOut}
          className="text-destructive focus:text-destructive cursor-pointer"
        >
          <LogOut className="mr-2 h-4 w-4" />
          <span>{isLoggingOut ? "Signing out..." : "Sign out"}</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
