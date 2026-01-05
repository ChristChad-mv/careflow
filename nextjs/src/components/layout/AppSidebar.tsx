"use client";

import { Home, AlertTriangle, Users, Settings, User } from "lucide-react";
import { NavLink } from "@/components/NavLink";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar";
import { Badge } from "@/components/ui/badge";
import { ThemeToggle } from "@/components/ThemeToggle";

const navItems = [
  { title: "Dashboard", url: "/dashboard", icon: Home },
  { title: "Critical Alerts", url: "/alerts", icon: AlertTriangle, badge: 3 },
  { title: "Patient List", url: "/patients", icon: Users },
  { title: "Profile", url: "/profile", icon: User },
  { title: "Configuration", url: "/config", icon: Settings },
];

export function AppSidebar({ alertCount = 0 }: { alertCount?: number }) {
  const { state } = useSidebar();
  const isCollapsed = state === "collapsed";

  const items = navItems.map(item => ({
    ...item,
    badge: item.url === "/alerts" ? alertCount : undefined
  }));

  return (
    <Sidebar className="border-r border-white/5 bg-sidebar/95 backdrop-blur-xl">
      <SidebarContent className="pt-6">
        <div className="px-6 mb-8">
          <h1 className={`font-bold text-sidebar-foreground transition-all ${isCollapsed ? 'text-lg' : 'text-2xl'}`}>
            <span className="text-gradient">{isCollapsed ? 'CF' : 'CareFlow'}</span>
          </h1>
          {!isCollapsed && (
            <p className="text-xs text-muted-foreground mt-1">Post-Hospitalization Monitor</p>
          )}
        </div>

        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {items.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild>
                    <NavLink
                      to={item.url}
                      end={item.url === "/"}
                      className="flex items-center gap-3 px-6 py-3 hover:bg-white/5 transition-all duration-200 group"
                      activeClassName="bg-primary/10 text-primary font-semibold border-l-4 border-primary"
                    >
                      <item.icon className="h-5 w-5 shrink-0 group-hover:text-primary transition-colors" />
                      {!isCollapsed && (
                        <span className="flex-1">{item.title}</span>
                      )}
                      {!isCollapsed && item.badge !== undefined && (
                        <Badge
                          variant="destructive"
                          className="ml-auto animate-critical-pulse shadow-lg shadow-destructive/20"
                        >
                          {item.badge}
                        </Badge>
                      )}
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>




        <SidebarGroup className="mt-auto">
          <SidebarGroupContent>
            <SidebarMenu>
              <SidebarMenuItem>
                <div className="flex items-center justify-between px-6 py-2">
                  {!isCollapsed && <span className="text-sm text-muted-foreground">Theme</span>}
                  <ThemeToggle />
                </div>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
}
