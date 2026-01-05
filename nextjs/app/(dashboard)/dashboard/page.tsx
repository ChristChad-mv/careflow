import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertTriangle, Users, TrendingUp, Clock } from "lucide-react";
import { getDashboardStats } from "@/lib/db";
import { RiskTrendChart } from "@/components/dashboard/RiskTrendChart";

export default async function Dashboard() {
  const stats = await getDashboardStats();

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
      <div>
        <h1 className="text-4xl font-bold tracking-tight">
          Welcome back, <span className="text-gradient">Nurse Sarah</span>
        </h1>
        <p className="text-muted-foreground mt-2 text-lg">
          Here's what's happening in your ward today.
        </p>
      </div>

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

      <div className="grid gap-6 md:grid-cols-7">
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
