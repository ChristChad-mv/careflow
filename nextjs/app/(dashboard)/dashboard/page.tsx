'use client';

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertTriangle, Users, TrendingUp, Clock, Loader2 } from "lucide-react";
import { getDashboardStats, UserContext } from "@/lib/db";
import { RiskTrendChart } from "@/components/dashboard/RiskTrendChart";
import { HackathonDemoDialog } from "@/components/dashboard/HackathonDemoDialog";
import { useSession } from "next-auth/react";
import { useEffect, useState } from "react";
import { Rocket } from "lucide-react";
import { Button } from "@/components/ui/button";

interface DashboardStats {
  totalPatients: number;
  criticalAlerts: number;
  readmissionRate: number;
  statusCounts: { safe: number; warning: number; critical: number };
}

export default function Dashboard() {
  const { data: session, status } = useSession();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [demoOpen, setDemoOpen] = useState(false);

  useEffect(() => {
    async function loadStats() {
      if (status === 'authenticated' && session?.user) {
        try {
          // Prepare UserContext from session
          const userContext: UserContext = {
            hospitalId: (session.user as any).hospitalId,
            role: (session.user as any).role,
            email: session.user.email || undefined
          };

          const data = await getDashboardStats(userContext);
          setStats(data);
        } catch (error) {
          console.error("Failed to load dashboard stats", error);
        } finally {
          setLoading(false);
        }
      } else if (status === 'unauthenticated') {
        setLoading(false); // Or redirect
      }
    }

    loadStats();
  }, [session, status]);

  if (status === 'loading' || loading) {
    return (
      <div className="flex items-center justify-center h-screen w-full">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!stats) {
    return <div>Unable to load dashboard data. Please try refreshing.</div>;
  }

  const kpiCards = [
    {
      title: "Total Patients",
      value: stats.totalPatients,
      icon: Users,
      description: "Active monitoring",
      trend: "+12% from last month",
      color: "text-blue-500",
    },
    {
      title: "Critical Alerts",
      value: stats.criticalAlerts,
      icon: AlertTriangle,
      description: "Requires attention",
      trend: "+2 new today",
      color: "text-destructive",
    },
    {
      title: "Readmission Rate",
      value: "4.2%",
      icon: TrendingUp,
      description: "Last 30 days",
      trend: "-0.5% improvement",
      color: "text-success",
    },
    {
      title: "Avg Response Time",
      value: "12m",
      icon: Clock,
      description: "Nurse engagement",
      trend: "Within target",
      color: "text-primary",
    },
  ];

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-4xl font-bold tracking-tight">
            Welcome back, <span className="text-gradient">{session?.user?.name || 'Nurse'}</span>
          </h1>
          <p className="text-muted-foreground mt-2 text-lg">
            Here's what's happening in your ward today.
          </p>
        </div>
        <Button
          size="lg"
          onClick={() => setDemoOpen(true)}
          className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-bold shadow-lg transition-all animate-bounce"
        >
          <Rocket className="mr-2 h-5 w-5" />
          Hackathon Demo
        </Button>
      </div>

      <HackathonDemoDialog open={demoOpen} onOpenChange={setDemoOpen} />

      {/* KPI Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {kpiCards.map((card) => (
          <Card key={card.title} className="glass-card border-none">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {card.title}
              </CardTitle>
              <card.icon className={`h-4 w-4 ${card.color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{card.value}</div>
              <p className="text-xs text-muted-foreground mt-1">
                {card.description}
              </p>
              <div className={`text-xs mt-2 font-medium ${card.trend.includes('+') && card.title !== 'Critical Alerts' ? 'text-success' :
                card.trend.includes('-') && card.title === 'Readmission Rate' ? 'text-success' : 'text-muted-foreground'
                }`}>
                {card.trend}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 grid-cols-1 md:grid-cols-7">
        {/* Chart Section */}
        <div className="md:col-span-4">
          <RiskTrendChart />
        </div>

        {/* Patient Status Distribution */}
        <div className="md:col-span-3">
          <Card className="glass-card border-none h-full">
            <CardHeader>
              <CardTitle>Patient Status Distribution</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {Object.entries(stats.statusCounts).map(([status, count]) => {
                  const percentage = stats.totalPatients > 0
                    ? Math.round((count / stats.totalPatients) * 100)
                    : 0;

                  let colorClass = "bg-slate-500";
                  if (status === 'critical') colorClass = "bg-destructive";
                  if (status === 'warning') colorClass = "bg-warning";
                  if (status === 'safe') colorClass = "bg-success";

                  return (
                    <div key={status} className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="capitalize font-medium">{status}</span>
                        <span className="text-muted-foreground">{count} patients ({percentage}%)</span>
                      </div>
                      <div className="h-2 w-full bg-secondary rounded-full overflow-hidden">
                        <div
                          className={`h-full ${colorClass} transition-all duration-500 ease-out`}
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
