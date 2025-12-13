"use client";

import { Link, usePathname } from "@/i18n/routing";
import { useTranslations } from "next-intl";
import { useUIStore } from "@/shared/store/ui-store";
import { Button } from "@/shared/components/ui/button";
import { cn } from "@/shared/lib/utils";
import {
  LayoutDashboard,
  Sparkles,
  Image as ImageIcon,
  Palette,
  FileText,
  Settings,
  Menu,
  X,
} from "lucide-react";

const navigation = [
  { name: "dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "generate", href: "/generate", icon: Sparkles },
  { name: "images", href: "/images", icon: ImageIcon },
  { name: "themes", href: "/themes", icon: Palette },
  { name: "reports", href: "/reports", icon: FileText },
  { name: "settings", href: "/settings", icon: Settings },
];

export function Sidebar() {
  const t = useTranslations("common");
  const pathname = usePathname();
  const { sidebarOpen, toggleSidebar } = useUIStore();
  const localeSegment = pathname?.split("/")[1] ?? "";

  return (
    <>
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={toggleSidebar}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 w-64 bg-card border-r border-border transition-transform duration-300 lg:translate-x-0",
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex h-full flex-col">
          {/* Header */}
          <div className="flex h-16 items-center justify-between border-b border-border px-6">
            <h1 className="text-xl font-bold">{t("appName")}</h1>
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleSidebar}
              className="lg:hidden"
            >
              <X className="h-5 w-5" />
            </Button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 space-y-1 px-3 py-4">
            {navigation.map((item) => {
              const Icon = item.icon;
              const targetPath = `/${localeSegment}${item.href}`;
              const isActive =
                pathname === targetPath || pathname?.startsWith(`${targetPath}/`);
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                  )}
                  onClick={() => {
                    if (window.innerWidth < 1024) {
                      toggleSidebar();
                    }
                  }}
                >
                  <Icon className="h-5 w-5" />
                  {t(item.name)}
                </Link>
              );
            })}
          </nav>
        </div>
      </aside>

      {/* Mobile menu button */}
      <Button
        variant="ghost"
        size="icon"
        onClick={toggleSidebar}
        className="fixed top-4 left-4 z-30 lg:hidden"
      >
        <Menu className="h-5 w-5" />
      </Button>
    </>
  );
}
