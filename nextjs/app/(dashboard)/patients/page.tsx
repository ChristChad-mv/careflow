import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Users } from "lucide-react";
import { getPatients } from "@/lib/db";
import Link from "next/link";

export default async function PatientList() {
  const patients = await getPatients();

  // Sort patients: Critical > Warning > Safe > Others
  const riskOrder: Record<string, number> = { 'critical': 0, 'warning': 1, 'safe': 2 };

  patients.sort((a, b) => {
    const riskA = riskOrder[a.currentStatus] ?? 99;
    const riskB = riskOrder[b.currentStatus] ?? 99;
    return riskA - riskB;
  });

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
        {patients.map((patient) => (
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
                  <Link href={`/patient/${patient.id}`}>
                    <Button variant="outline">
                      View
                    </Button>
                  </Link>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}

        {patients.length === 0 && (
          <div className="text-center py-10 text-muted-foreground">
            No patients found.
          </div>
        )}
      </div>
    </div>
  );
}
