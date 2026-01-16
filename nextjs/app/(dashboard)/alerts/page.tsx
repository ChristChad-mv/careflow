import { AlertTriangle } from "lucide-react";
import { AlertsRealtime } from "@/components/alerts/AlertsRealtime";

export default function CriticalAlerts() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <AlertTriangle className="h-8 w-8 text-destructive" />
        <div>
          <h1 className="text-3xl font-bold">Critical Alerts</h1>
          <p className="text-muted-foreground mt-1">
            Patients requiring immediate attention • Updates in real-time
          </p>
        </div>
      </div>

      <AlertsRealtime />
    </div>
  );
}

