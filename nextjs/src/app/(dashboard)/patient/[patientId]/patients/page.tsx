"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Users } from "lucide-react";
import { mockPatients } from "@/data/mockData";
import { useRouter } from "next/navigation";

export default function PatientList() {
  const router = useRouter();

  const getRiskBadgeClass = (risk: string) => {
    switch (risk) {
      case 'critical':
        return 'status-critical';
      case 'warning':
        return 'status-warning';
      default:
        return 'status-safe';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Users className="h-8 w-8 text-primary" />
        <div>
          <h1 className="text-3xl font-bold">Patient List</h1>
          <p className="text-muted-foreground mt-1">
            All patients under active monitoring
          </p>
        </div>
      </div>

      <div className="space-y-4">
        {mockPatients.map((patient) => (
          <Card key={patient.id}>
            <CardContent className="p-6">
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-center">
                <div className="lg:col-span-2">
                  <Badge className={`status-badge ${getRiskBadgeClass(patient.currentStatus)}`}>
                    {patient.currentStatus.toUpperCase()}
                  </Badge>
                </div>

                <div className="lg:col-span-3">
                  <div className="font-bold text-lg">{patient.name}</div>
                  <div className="text-sm text-muted-foreground">ID: {patient.id}</div>
                </div>

                <div className="lg:col-span-4">
                  <div className="text-sm font-medium text-muted-foreground">Diagnosis</div>
                  <div className="text-sm">{patient.diagnosis}</div>
                </div>

                <div className="lg:col-span-2">
                  <div className="text-sm font-medium text-muted-foreground">Discharged</div>
                  <div className="text-sm font-semibold">{patient.dischargeDate}</div>
                </div>

                <div className="lg:col-span-1 flex justify-end">
                  <Button
                    variant="outline"
                    onClick={() => router.push(`/patient/${patient.id}`)}
                  >
                    View
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
