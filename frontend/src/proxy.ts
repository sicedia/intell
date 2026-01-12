import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import createIntlMiddleware from "next-intl/middleware";
import { routing } from "./i18n/routing";

/**
 * Proxy handler for Next.js 16+
 *
 * Combines:
 * 1. Internationalization (next-intl)
 * 2. Route protection (session cookie check)
 *
 * Note: Cookie presence check is UX only, not security.
 * Real validation happens via /api/auth/me in layout/components.
 */

const intlMiddleware = createIntlMiddleware(routing);

// Routes that don't require authentication
const publicPaths = ["/login", "/register", "/forgot-password"];

// Paths to skip entirely (API, static, etc.)
const skipPaths = ["/api", "/_next", "/static", "/favicon.ico"];

function isPublicPath(pathname: string): boolean {
  // Remove locale prefix for checking
  const pathWithoutLocale = pathname.replace(/^\/[a-z]{2}(-[A-Z]{2})?/, "") || "/";
  return publicPaths.some((path) => pathWithoutLocale.startsWith(path));
}

function shouldSkip(pathname: string): boolean {
  return skipPaths.some((path) => pathname.startsWith(path));
}

/**
 * Next.js 16 proxy function (replaces middleware)
 */
export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Skip proxy for API routes, static files, etc.
  if (shouldSkip(pathname)) {
    return NextResponse.next();
  }

  // Check for session cookie (UX check, not security)
  const sessionCookie = request.cookies.get("sessionid");
  const hasSession = !!sessionCookie?.value;

  // Determine locale from path or default
  const localeMatch = pathname.match(/^\/([a-z]{2}(-[A-Z]{2})?)/);
  const locale = localeMatch?.[1] || routing.defaultLocale;

  // If not authenticated and trying to access protected route, redirect to login
  if (!hasSession && !isPublicPath(pathname) && pathname !== "/") {
    const loginUrl = new URL(`/${locale}/login`, request.url);
    loginUrl.searchParams.set("callbackUrl", pathname);
    return NextResponse.redirect(loginUrl);
  }

  // If authenticated and trying to access login, redirect to dashboard
  if (hasSession && isPublicPath(pathname)) {
    return NextResponse.redirect(new URL(`/${locale}/dashboard`, request.url));
  }

  // Apply internationalization middleware
  return intlMiddleware(request);
}

export const config = {
  // Match all paths except static files
  matcher: ["/((?!api|_next|_vercel|.*\\..*).*)"],
};
