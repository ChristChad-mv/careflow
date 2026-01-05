"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertTriangle, Users, TrendingDown, Activity } from "lucide-react";
import { mockPatients, mockAlerts } from "@/data/mockData";
import Link from "next/link";

export default function Dashboard() {
  const totalPatients = mockPatients.length;
  const criticalAlerts = mockAlerts.filter(a => a.riskLevel === 'critical').length;
  const readmissionRate = 12.3; // Mock data

  const statusCounts = {
    safe: mockPatients.filter(p => p.currentStatus === 'safe').length,
    warning: mockPatients.filter(p => p.currentStatus === 'warning').length,
    critical: mockPatients.filter(p => p.currentStatus === 'critical').length,
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">System Dashboard</h1>
        <p className="text-muted-foreground mt-1">Real-time patient monitoring and system health</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Active Patients
            </CardTitle>
            <Users className="h-5 w-5 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{totalPatients}</div>
            <p className="text-xs text-muted-foreground mt-2">
              Under active monitoring
            </p>
          </CardContent>
        </Card>

        <Card className="border-2 border-destructive">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-destructive">
              Critical Alerts
            </CardTitle>
            <AlertTriangle className="h-5 w-5 text-destructive" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-destructive">{criticalAlerts}</div>
            <Link href="/alerts" className="text-xs text-primary hover:underline mt-2 inline-block">
              View all critical cases →
            </Link>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              30-Day Readmission Rate
            </CardTitle>
            <TrendingDown className="h-5 w-5 text-success" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{readmissionRate}%</div>
            <p className="text-xs text-success mt-2">
              ↓ 2.1% from last month
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Patient Status Distribution */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Patient Status Distribution
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-card border-2 border-success/30 rounded-lg p-4">
              <div className="text-2xl font-bold text-success">{statusCounts.safe}</div>
              <div className="text-sm text-muted-foreground mt-1">Safe Status</div>
              <div className="text-xs text-muted-foreground mt-2">
                {((statusCounts.safe / totalPatients) * 100).toFixed(0)}% of total
              </div>
            </div>
            
            <div className="bg-card border-2 border-warning/30 rounded-lg p-4">
              <div className="text-2xl font-bold text-warning">{statusCounts.warning}</div>
              <div className="text-sm text-muted-foreground mt-1">Warning Status</div>
              <div className="text-xs text-muted-foreground mt-2">
                {((statusCounts.warning / totalPatients) * 100).toFixed(0)}% of total
              </div>
            </div>
            
            <div className="bg-card border-2 border-destructive/30 rounded-lg p-4 animate-critical-pulse">
              <div className="text-2xl font-bold text-destructive">{statusCounts.critical}</div>
              <div className="text-sm text-muted-foreground mt-1">Critical Status</div>
              <div className="text-xs text-muted-foreground mt-2">
                {((statusCounts.critical / totalPatients) * 100).toFixed(0)}% of total
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Resource Map (Simulated) */}
      <Card>
        <CardHeader>
          <CardTitle>Community Resource Availability</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex justify-between items-center p-3 bg-secondary rounded-lg">
              <div>
                <div className="font-medium">Sector 1 - Downtown</div>
                <div className="text-sm text-muted-foreground">3 available nurses</div>
              </div>
              <div className="text-success font-semibold">Available</div>
            </div>
            <div className="flex justify-between items-center p-3 bg-secondary rounded-lg">
              <div>
                <div className="font-medium">Sector 2 - East Side</div>
                <div className="text-sm text-muted-foreground">2 available nurses</div>
              </div>
              <div className="text-success font-semibold">Available</div>
            </div>
            <div className="flex justify-between items-center p-3 bg-secondary rounded-lg">
              <div>
                <div className="font-medium">Sector 3 - North District</div>
                <div className="text-sm text-muted-foreground">1 available nurse</div>
              </div>
              <div className="text-warning font-semibold">Limited</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
