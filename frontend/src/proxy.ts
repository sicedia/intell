import type { NextRequest } from "next/server";
import createMiddleware from "next-intl/middleware";
import { routing } from "./i18n/routing";

/**
 * Proxy handler for internationalization routing.
 * 
 * Migrated from middleware.ts to proxy.ts following Next.js 16 conventions.
 * @see https://nextjs.org/docs/messages/middleware-to-proxy
 * 
 * Note: next-intl still uses createMiddleware internally, but we export
 * the function as 'proxy' to comply with Next.js 16's new naming convention.
 */
const intlMiddleware = createMiddleware(routing);

export function proxy(request: NextRequest) {
    return intlMiddleware(request);
}

export const config = {
    matcher: ["/((?!api|_next|_vercel|.*\\..*).*)"],
};
