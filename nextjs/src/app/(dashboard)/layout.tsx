

import { ReactNode } from "react";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/layout/AppSidebar";
import { SignOutButton } from "@/components/auth/signOutButton";

import { getAlerts } from "@/lib/db";

export default async function AppLayout({ children }: { children: ReactNode }) {
  const alerts = await getAlerts();
  const criticalCount = alerts.filter(a => a.riskLevel === 'critical').length;

  return (
    <SidebarProvider>
      <div className="min-h-screen flex w-full bg-background">
        <AppSidebar alertCount={criticalCount} />
        <main className="flex-1">
          <header className="h-16 border-b border-border flex items-center px-6 bg-card">
            <SidebarTrigger className="mr-4" />
            <div className="flex-1" />
            <div className="flex items-center gap-4">
              <span className="text-sm text-muted-foreground hidden md:inline-block">
                Nurse Coordinator Portal
              </span>
              <SignOutButton />
            </div>
          </header>
          <div className="p-6">
            {children}
          </div>
        </main>
      </div>
    </SidebarProvider>
  );
}
