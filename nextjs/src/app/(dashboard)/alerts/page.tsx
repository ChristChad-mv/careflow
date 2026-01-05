import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle, Clock } from "lucide-react";
import { getAlerts } from "@/lib/db";
import Link from "next/link";
import { formatDistanceToNow } from "date-fns";


export default async function CriticalAlerts() {
  const allAlerts = await getAlerts();
  const alerts = allAlerts.sort((a, b) => {
    const priorityOrder = { critical: 0, warning: 1, safe: 2 };
    // @ts-ignore - Handle potential undefined priorities gracefully
    return (priorityOrder[a.priority] ?? 2) - (priorityOrder[b.priority] ?? 2);
  });

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical':
        return 'text-red-500 bg-red-50 border-red-200';
      case 'warning':
        return 'text-yellow-500 bg-yellow-50 border-yellow-200';
      default:
        return 'text-green-500 bg-green-50 border-green-200';
    }
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
              className={`border-2 ${alert.priority === 'critical'
                ? 'border-destructive bg-destructive/5'
                : 'border-warning bg-warning/5'
                }`}
            >
              <CardContent className="p-6">
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-center">
                  {/* Risk Level */}
                  <div className="lg:col-span-2">
                    <Badge variant="outline" className={getPriorityColor(alert.priority)}>
                      {(alert.priority || 'UNKNOWN').toUpperCase()}
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
                        {formatDistanceToNow(alert.createdAt, { addSuffix: true })}
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
                  <div className="lg:col-span-2 flex justify-end gap-2">
                    <Link href={`/alerts/${alert.id}`}>
                      <Button className="bg-primary hover:bg-primary/90 text-primary-foreground font-semibold">
                        View & Manage
                      </Button>
                    </Link>
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
