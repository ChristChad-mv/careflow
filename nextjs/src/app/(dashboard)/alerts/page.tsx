"use client";

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle, Clock } from "lucide-react";
import { mockAlerts } from "@/data/mockData";
import { useRouter } from "next/navigation";
import { formatDistanceToNow } from "date-fns";

export default function CriticalAlerts() {
  const router = useRouter();
  const [alerts] = useState(mockAlerts);

  const getRiskBadgeClass = (risk: string) => {
    switch (risk) {
      case 'critical':
        return 'status-critical animate-critical-pulse';
      case 'warning':
        return 'status-warning';
      default:
        return 'status-safe';
    }
  };

  const handleTakeOwnership = (patientId: string) => {
    router.push(`/patient/${patientId}`);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <AlertTriangle className="h-8 w-8 text-destructive" />
        <div>
          <h1 className="text-3xl font-bold">Critical Alerts</h1>
          <p className="text-muted-foreground mt-1">
            Patients requiring immediate attention
          </p>
        </div>
      </div>

      {alerts.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <div className="text-success text-lg font-semibold">
              No critical alerts at this time
            </div>
            <p className="text-muted-foreground mt-2">
              All patients are stable or in monitoring status
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {alerts.map((alert) => (
            <Card 
              key={alert.id}
              className={`border-2 ${
                alert.riskLevel === 'critical' 
                  ? 'border-destructive bg-destructive/5' 
                  : 'border-warning bg-warning/5'
              }`}
            >
              <CardContent className="p-6">
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-center">
                  {/* Risk Level */}
                  <div className="lg:col-span-2">
                    <Badge className={`status-badge ${getRiskBadgeClass(alert.riskLevel)} text-base px-4 py-2`}>
                      {alert.riskLevel.toUpperCase()}
                    </Badge>
                  </div>

                  {/* Patient Info */}
                  <div className="lg:col-span-2">
                    <div className="font-bold text-lg">{alert.patientName}</div>
                    <div className="text-sm text-muted-foreground">ID: {alert.patientId}</div>
                  </div>

                  {/* Time Since Alert */}
                  <div className="lg:col-span-2">
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <Clock className="h-4 w-4" />
                      <span className="text-sm font-medium">
                        {formatDistanceToNow(alert.timestamp, { addSuffix: true })}
                      </span>
                    </div>
                  </div>

                  {/* Critical Trigger */}
                  <div className="lg:col-span-4">
                    <div className="text-sm font-semibold text-foreground">
                      {alert.trigger}
                    </div>
                  </div>

                  {/* Action Button */}
                  <div className="lg:col-span-2 flex justify-end">
                    <Button
                      onClick={() => handleTakeOwnership(alert.patientId)}
                      className="bg-primary hover:bg-primary/90 text-primary-foreground font-semibold"
                    >
                      View Brief & Take Ownership
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
