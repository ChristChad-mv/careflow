"use client";

import { Home, AlertTriangle, Users, Settings } from "lucide-react";
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

const navItems = [
  { title: "Dashboard", url: "/dashboard", icon: Home },
  { title: "Critical Alerts", url: "/alerts", icon: AlertTriangle, badge: 3 },
  { title: "Patient List", url: "/patients", icon: Users },
  { title: "Configuration", url: "/config", icon: Settings },
];

export function AppSidebar() {
  const { state } = useSidebar();
  const isCollapsed = state === "collapsed";

  return (
    <Sidebar className="border-r border-sidebar-border">
      <SidebarContent className="pt-6">
        <div className="px-6 mb-8">
          <h1 className={`font-bold text-sidebar-foreground transition-all ${isCollapsed ? 'text-lg' : 'text-xl'}`}>
            {isCollapsed ? 'CF' : 'CareFlow'}
          </h1>
          {!isCollapsed && (
            <p className="text-xs text-muted-foreground mt-1">Post-Hospitalization Monitor</p>
          )}
        </div>

        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {navItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild>
                    <NavLink
                      to={item.url}
                      end={item.url === "/"}
                      className="flex items-center gap-3 px-6 py-3 hover:bg-sidebar-accent transition-colors"
                      activeClassName="bg-sidebar-accent text-sidebar-primary font-semibold border-l-4 border-sidebar-primary"
                    >
                      <item.icon className="h-5 w-5 shrink-0" />
                      {!isCollapsed && (
                        <span className="flex-1">{item.title}</span>
                      )}
                      {!isCollapsed && item.badge !== undefined && (
                        <Badge 
                          variant="destructive" 
                          className="ml-auto animate-critical-pulse"
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
      </SidebarContent>
    </Sidebar>
  );
}
