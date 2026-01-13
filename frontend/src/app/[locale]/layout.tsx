import { NextIntlClientProvider } from "next-intl";
import { getMessages } from "next-intl/server";
import { Inter } from "next/font/google";
import { ThemeProvider } from "@/shared/components/providers/theme-provider";
import { QueryProvider } from "@/shared/components/providers/query-provider";
import { ConnectionBanner } from "@/shared/components/ui/connection-banner";
import { AuthProvider } from "@/features/auth";
import { Toaster } from "sonner";
import type { Metadata } from "next";
import { routing } from "@/i18n/routing";
import { hasLocale } from "next-intl";
import { AppShell } from "@/shared/components/layout/AppShell";
import "../globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "Intell.AI",
  description: "AI-powered platform",
};

export function generateStaticParams() {
  return routing.locales.map((locale) => ({ locale }));
}

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;

  // Ensure locale is valid, fallback to default
  const validLocale = hasLocale(routing.locales, locale) ? locale : routing.defaultLocale;

  // Load messages with error handling
  let messages;
  try {
    messages = await getMessages();
  } catch (error) {
    console.error('Failed to load messages:', error);
    // Fallback to empty messages object to prevent crash
    messages = {};
  }

  return (
    <html lang={validLocale} suppressHydrationWarning>
      <body className={inter.variable}>
        <NextIntlClientProvider messages={messages}>
          <ThemeProvider
            attribute="class"
            defaultTheme="system"
            enableSystem
            disableTransitionOnChange
          >
            <QueryProvider>
              <AuthProvider>
                <ConnectionBanner />
                <AppShell>
                  {children}
                </AppShell>
                <Toaster />
              </AuthProvider>
            </QueryProvider>
          </ThemeProvider>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
