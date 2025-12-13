import { NextIntlClientProvider } from "next-intl";
import { getMessages } from "next-intl/server";
import { Sidebar } from "@/shared/components/layout/sidebar";
import { Inter } from "next/font/google";
import { ThemeProvider } from "@/shared/components/providers/theme-provider";
import { QueryProvider } from "@/shared/components/providers/query-provider";
import { Toaster } from "sonner";
import type { Metadata } from "next";
import { routing } from "@/i18n/routing";
import { notFound } from "next/navigation";
import { hasLocale } from "next-intl";
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
  params: { locale: string };
}) {
  const { locale } = params;
  
  if (!hasLocale(routing.locales, locale)) {
    notFound();
  }
  
  const messages = await getMessages();

  return (
    <html lang={locale} suppressHydrationWarning>
      <body className={inter.variable}>
        <NextIntlClientProvider messages={messages}>
          <ThemeProvider
            attribute="class"
            defaultTheme="system"
            enableSystem
            disableTransitionOnChange
          >
            <QueryProvider>
              <div className="flex h-screen overflow-hidden">
                <Sidebar />
                <main className="flex-1 overflow-y-auto lg:pl-64">{children}</main>
              </div>
              <Toaster />
            </QueryProvider>
          </ThemeProvider>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
