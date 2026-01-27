'use client';

import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search, Plus, Loader2 } from "lucide-react";
import { PatientList } from "@/components/patient/PatientList";
import { getPatients, UserContext } from "@/lib/db";
import { Patient } from "@/types/patient";
import { useState, useEffect } from "react";
import { useSession } from "next-auth/react";
import { CreatePatientDialog } from "@/components/patient/CreatePatientDialog";

export default function PatientsPage() {
  const { data: session, status } = useSession();
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [riskFilter, setRiskFilter] = useState("all");
  const [isCreateOpen, setIsCreateOpen] = useState(false);

  useEffect(() => {
    async function loadPatients() {
      if (status === 'authenticated' && session?.user) {
        try {
          const userContext: UserContext = {
            hospitalId: (session.user as any).hospitalId,
            role: (session.user as any).role,
            email: session.user.email || undefined
          };
          const data = await getPatients(userContext);
          setPatients(data);
        } catch (error) {
          console.error("Error loading patients:", error);
        } finally {
          setLoading(false);
        }
      } else if (status === 'unauthenticated') {
        setLoading(false);
      }
    }
    loadPatients();
  }, [session, status]);

  if (status === 'loading' || loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  // Filter patients
  const filteredPatients = patients.filter(patient => {
    const matchesSearch = patient.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      patient.id.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesRisk = riskFilter === "all" || patient.currentStatus === riskFilter;
    return matchesSearch && matchesRisk;
  });

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-4xl font-bold tracking-tight">Patients</h1>
          <p className="text-muted-foreground mt-2 text-lg">
            Manage and monitor patient status
          </p>
        </div>
        <Button onClick={() => setIsCreateOpen(true)} className="bg-primary hover:bg-primary/90 text-white shadow-lg shadow-primary/20 transition-all duration-300 hover:scale-105 active:scale-95">
          <Plus className="mr-2 h-4 w-4" /> Add Patient
        </Button>
      </div>

      <CreatePatientDialog
        open={isCreateOpen}
        onOpenChange={setIsCreateOpen}
      />

      <Card className="glass-card border-none p-4">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search patients by name or ID..."
              className="pl-9 bg-secondary/50 border-0 focus-visible:ring-1 focus-visible:ring-primary/50 transition-all duration-300"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <div className="flex gap-2">
            <Button
              variant={riskFilter === "all" ? "default" : "outline"}
              onClick={() => setRiskFilter("all")}
              size="sm"
            >
              All
            </Button>
            <Button
              variant={riskFilter === "critical" ? "destructive" : "outline"}
              onClick={() => setRiskFilter("critical")}
              size="sm"
            >
              Critical
            </Button>
          </div>
        </div>
      </Card>

      <div className="grid gap-6">
        <PatientList patients={filteredPatients} />
      </div>
    </div>
  );
}
