'use client';

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Phone, Calendar, Pill, User, MapPin, Stethoscope, Mail, AlertTriangle, Loader2, Rocket, Trash2, Activity as ActivityIcon } from "lucide-react";
import { getPatient, UserContext } from "@/lib/db";
import { deletePatientClient } from "@/lib/client-actions";
import { format } from "date-fns";
import { EditMedicationDialog } from "@/components/patient/EditMedicationDialog";
import { EditAppointmentDialog } from "@/components/patient/EditAppointmentDialog";
import { useSession } from "next-auth/react";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Patient } from "@/types/patient";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

export default function PatientProfile() {
  const params = useParams();
  const router = useRouter();
  const patientId = params.patientId as string;
  const { data: session, status } = useSession();
  const [patient, setPatient] = useState<Patient | null>(null);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    async function loadPatient() {
      if (status === 'authenticated' && session?.user && patientId) {
        try {
          const userContext: UserContext = {
            hospitalId: (session.user as any).hospitalId,
            role: (session.user as any).role,
            email: session.user.email || undefined
          };
          const data = await getPatient(patientId, userContext);
          setPatient(data);
        } catch (error) {
          console.error("Error loading patient:", error);
        } finally {
          setLoading(false);
        }
      } else if (status === 'unauthenticated') {
        setLoading(false);
      }
    }
    loadPatient();
  }, [session, status, patientId]);

  if (status === 'loading' || loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!patient) return <div className="p-8 text-center text-muted-foreground">Patient not found or unauthorized.</div>;

  // Helper for safe date formatting
  const formatDate = (date: Date | string | undefined) => {
    if (!date) return 'N/A';
    try {
      return format(new Date(date), 'PPP');
    } catch (e) {
      return String(date);
    }
  };

  const handleCallDemo = async () => {
    if (!patientId) return;

    setTriggering(true);
    try {
      const response = await fetch('/api/demo/trigger', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ patientId, scheduleHour: 8 })
      });

      if (!response.ok) {
        throw new Error('Failed to trigger demo call');
      }

      toast.success("🚀 Agent Triggered!", {
        description: "You should receive a call shortly. Simulate symptoms and check Alerts for the follow-up.",
        duration: 8000,
      });

    } catch (error) {
      console.error(error);
      toast.error("Failed to trigger agent");
    } finally {
      setTriggering(false);
    }
  };

  const handleDeletePatient = async () => {

    setDeleting(true);
    try {
      const userContext: UserContext = {
        hospitalId: (session?.user as any).hospitalId,
        role: (session?.user as any).role,
        email: session?.user?.email || undefined
      };

      const result = await deletePatientClient(patientId, userContext);
      if (result.success) {
        toast.success("Patient record deleted successfully");
        router.push('/patients');
      }
    } catch (error) {
      console.error(error);
      toast.error("Failed to delete patient record");
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-700">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            {patient.name}
          </h1>
          <p className="text-muted-foreground">Patient ID: {patient.id}</p>
        </div>
        <div className="flex items-center gap-3">
          <Badge className={
            patient.currentStatus === 'critical' ? 'bg-destructive' :
              patient.currentStatus === 'warning' ? 'bg-yellow-500' : 'bg-green-500'
          }>
            {patient.currentStatus.toUpperCase()}
          </Badge>
          <Button
            onClick={handleCallDemo}
            disabled={triggering || deleting}
            className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-bold shadow-lg h-10 px-6 rounded-full"
          >
            {triggering ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Rocket className="mr-2 h-4 w-4" />}
            Call Now (Demo)
          </Button>
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button
                variant="outline"
                disabled={deleting || triggering}
                className="border-destructive/30 hover:bg-destructive/10 text-destructive font-semibold h-10 px-4 rounded-full"
              >
                {deleting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Trash2 className="mr-2 h-4 w-4" />}
                Delete Record
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
                <AlertDialogDescription>
                  This action cannot be undone. This will permanently delete the patient record,
                  all associated alerts, and interaction history from the clinical database.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction onClick={handleDeletePatient} className="bg-destructive hover:bg-destructive/90 text-white">
                  Confirm Deletion
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

        {/* Column 1: Demographics & Contact */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="h-5 w-5 text-primary" />
                Patient Details
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <span className="text-sm font-medium text-muted-foreground">Date of Birth / Age</span>
                <div className="font-medium">{formatDate(patient.dateOfBirth)}</div>
              </div>

              <div>
                <span className="text-sm font-medium text-muted-foreground">Contact Information</span>
                <div className="flex items-center gap-2 mt-2">
                  <Phone className="h-4 w-4 text-muted-foreground" />
                  <span>{patient.contactNumber}</span>
                </div>
                {patient.email && (
                  <div className="flex items-center gap-2 mt-1">
                    <Mail className="h-4 w-4 text-muted-foreground" />
                    <span>{patient.email}</span>
                  </div>
                )}
                <div className="mt-2 text-xs bg-secondary text-secondary-foreground px-2 py-1 rounded inline-block uppercase">
                  Preferred Language: {patient.preferredLanguage}
                </div>
                <div className="mt-2 ml-2 text-xs bg-secondary text-secondary-foreground px-2 py-1 rounded inline-block uppercase">
                  Preferred Contact: {patient.contact?.preferredMethod || 'phone'}
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Stethoscope className="h-5 w-5 text-blue-500" />
                Care Team
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {patient.assignedNurse ? (
                <div>
                  <span className="text-sm font-medium text-muted-foreground block mb-1">Assigned Nurse</span>
                  <div className="font-semibold">{patient.assignedNurse.name}</div>
                  <div className="text-sm">{patient.assignedNurse.phone}</div>
                  <div className="text-sm text-muted-foreground">{patient.assignedNurse.email}</div>
                </div>
              ) : (
                <div className="text-muted-foreground">No nurse assigned.</div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Column 2: Clinical Status & Discharge */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <ActivityIcon className="h-5 w-5 text-green-600" />
                Discharge Plan
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <span className="text-sm font-medium text-muted-foreground">Primary Diagnosis</span>
                <div className="font-bold text-lg">{patient.diagnosis}</div>
              </div>
              <div>
                <span className="text-sm font-medium text-muted-foreground">Discharge Date</span>
                <div className="font-medium">{patient.dischargeDate}</div>
              </div>
              <Separator />
              <div>
                <span className="text-sm font-medium text-muted-foreground">Discharging Physician</span>
                <div className="font-medium">{patient.dischargePlan?.dischargingPhysician || 'N/A'}</div>
                <div className="text-xs text-muted-foreground">{patient.dischargePlan?.hospitalId}</div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-l-4 border-l-yellow-400">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-yellow-500" />
                Risk Factors (Watchlist)
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <span className="text-sm font-semibold text-destructive block mb-1">Critical Symptoms</span>
                <ul className="list-disc pl-5 text-sm">
                  {patient.dischargePlan?.criticalSymptoms?.map((s: string, i: number) => (
                    <li key={i}>{s}</li>
                  )) || <li>None listed</li>}
                </ul>
              </div>
              <div>
                <span className="text-sm font-semibold text-yellow-600 block mb-1">Warning Symptoms</span>
                <ul className="list-disc pl-5 text-sm">
                  {patient.dischargePlan?.warningSymptoms?.map((s: string, i: number) => (
                    <li key={i}>{s}</li>
                  )) || <li>None listed</li>}
                </ul>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Column 3: Medications & Appointments */}
        <div className="space-y-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Calendar className="h-5 w-5 text-purple-500" />
                Next Appointment
              </CardTitle>
              <EditAppointmentDialog patient={patient} />
            </CardHeader>
            <CardContent>
              {patient.nextAppointment?.date ? (
                <div className="bg-purple-50 dark:bg-purple-950/20 p-4 rounded-lg">
                  <div className="font-bold text-lg text-purple-700 dark:text-purple-300">
                    {formatDate(patient.nextAppointment.date)}
                  </div>
                  <div className="font-medium mt-1">{patient.nextAppointment.type}</div>
                  <div className="flex items-center gap-2 mt-2 text-sm text-muted-foreground">
                    <MapPin className="h-4 w-4" />
                    {patient.nextAppointment.location}
                  </div>
                </div>
              ) : (
                <div className="text-muted-foreground italic">No upcoming appointments scheduled.</div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Pill className="h-5 w-5 text-blue-500" />
                Medication Schedule
              </CardTitle>
              <EditMedicationDialog patient={patient} />
            </CardHeader>
            <CardContent>
              <ul className="space-y-4">
                {patient.medicationPlan?.map((med, idx) => (
                  <li key={idx} className="border-b pb-3 last:border-0 last:pb-0">
                    <div className="flex justify-between items-start">
                      <div className="font-semibold">{med.name}</div>
                      <Badge variant="outline">{med.dosage}</Badge>
                    </div>
                    <div className="text-sm mt-1">{med.frequency}</div>
                    {med.instructions && (
                      <div className="text-xs text-muted-foreground mt-1 italic">
                        "{med.instructions}"
                      </div>
                    )}
                  </li>
                ))}
                {(!patient.medicationPlan || patient.medicationPlan.length === 0) && (
                  <li className="text-muted-foreground text-sm italic">
                    No medications listed. Click edit to add.
                  </li>
                )}
              </ul>
            </CardContent>
          </Card>
        </div>

      </div>
    </div>
  );
}
