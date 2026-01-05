"use client";

import { useParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Phone, Calendar, Pill, AlertTriangle, Clock, Bot, User } from "lucide-react";
import { mockPatients, mockInteractions, mockAlerts } from "@/data/mockData";
import { format } from "date-fns";
import { validatePatientId } from "@/lib/validators";
import { useMemo } from "react";

export default function PatientDetail() {
  const params = useParams();
  
  // Validate patient ID using useMemo to avoid re-validation on every render
  const { patientId, error } = useMemo(() => {
    try {
      const rawId = params.patientId as string;
      const validatedId = validatePatientId(rawId);
      return { patientId: validatedId, error: null };
    } catch (err) {
      return { 
        patientId: null, 
        error: err instanceof Error ? err.message : 'Invalid patient ID' 
      };
    }
  }, [params.patientId]);

  // Show error if validation failed
  if (error) {
    return (
      <div className="p-6">
        <Card>
          <CardContent className="py-12 text-center">
            <AlertTriangle className="h-12 w-12 text-destructive mx-auto mb-4" />
            <p className="text-lg font-semibold text-destructive mb-2">Invalid Patient ID</p>
            <p className="text-muted-foreground">{error}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Show loading while validating
  if (!patientId) {
    return (
      <div className="p-6">
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-lg">Loading...</p>
          </CardContent>
        </Card>
      </div>
    );
  }
  
  const patient = mockPatients.find(p => p.id === patientId);
  const interactions = mockInteractions[patientId] || [];
  const patientAlerts = mockAlerts.filter(a => a.patientId === patientId);
  const currentAlert = patientAlerts[0];

  if (!patient) {
    return (
      <div className="p-6">
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-lg">Patient not found</p>
          </CardContent>
        </Card>
      </div>
    );
  }

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

  return (
    <div className="space-y-6">
      {/* Patient Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold">{patient.name}</h1>
          <p className="text-muted-foreground mt-1">Patient ID: {patient.id}</p>
        </div>
        <Badge className={`status-badge ${getRiskBadgeClass(patient.currentStatus)} text-lg px-4 py-2`}>
          {patient.currentStatus.toUpperCase()}
        </Badge>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Patient Summary */}
        <div className="space-y-6">
          {/* Basic Info */}
          <Card>
            <CardHeader>
              <CardTitle>Patient Summary</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-start gap-3">
                <Calendar className="h-5 w-5 text-muted-foreground mt-0.5" />
                <div>
                  <div className="text-sm font-medium text-muted-foreground">Discharge Date</div>
                  <div className="font-semibold">{patient.dischargeDate}</div>
                </div>
              </div>

              <Separator />

              <div>
                <div className="text-sm font-medium text-muted-foreground mb-2">Diagnosis</div>
                <div className="font-semibold">{patient.diagnosis}</div>
              </div>

              <Separator />

              <div className="flex items-center gap-3">
                <Phone className="h-5 w-5 text-muted-foreground" />
                <div className="flex-1">
                  <div className="text-sm font-medium text-muted-foreground">Contact</div>
                  <div className="font-semibold">{patient.contactNumber}</div>
                </div>
                <Button variant="default" size="sm">
                  Call Patient
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Medication Plan */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Pill className="h-5 w-5" />
                Medication Plan
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {patient.medicationPlan.map((med, idx) => (
                <div key={idx} className="bg-secondary p-3 rounded-lg">
                  <div className="font-semibold">{med.name}</div>
                  <div className="text-sm text-muted-foreground mt-1">
                    {med.dosage} • {med.frequency}
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

        {/* Right Column: AI Brief and Timeline */}
        <div className="space-y-6">
          {/* AI Critical Brief */}
          {currentAlert && currentAlert.brief && (
            <Card className="border-2 border-destructive">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-destructive">
                  <AlertTriangle className="h-5 w-5" />
                  AI-Generated Critical Brief
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="bg-destructive/10 p-4 rounded-lg space-y-3">
                  <div>
                    <div className="text-sm font-semibold text-muted-foreground">AI Summary</div>
                    <p className="mt-2 text-foreground leading-relaxed">{currentAlert.brief}</p>
                  </div>
                  
                  <Separator />
                  
                  <div>
                    <div className="text-sm font-semibold text-muted-foreground">Recommended Action</div>
                    <p className="mt-2 text-foreground font-medium">
                      Immediate phone contact required. Consider emergency dispatch if patient condition deteriorates.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Interaction Timeline */}
          <Card>
            <CardHeader>
              <CardTitle>Interaction Log</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {interactions.map((interaction) => (
                  <div
                    key={interaction.id}
                    className={`p-4 rounded-lg ${
                      interaction.sender === 'ai'
                        ? 'bg-primary/10 border-l-4 border-primary'
                        : interaction.sender === 'patient'
                        ? 'bg-secondary border-l-4 border-accent'
                        : 'bg-muted border-l-4 border-muted-foreground'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-2">
                      {interaction.sender === 'ai' && <Bot className="h-4 w-4 text-primary" />}
                      {interaction.sender === 'patient' && <User className="h-4 w-4 text-accent" />}
                      {interaction.sender === 'system' && <Clock className="h-4 w-4 text-muted-foreground" />}
                      
                      <span className="text-xs font-semibold uppercase">
                        {interaction.sender}
                      </span>
                      <span className="text-xs text-muted-foreground ml-auto">
                        {format(interaction.timestamp, 'MMM d, HH:mm')}
                      </span>
                    </div>
                    <p className={`text-sm ${interaction.type === 'event' ? 'font-semibold italic' : ''}`}>
                      {interaction.content}
                    </p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
