'use client';

import { getAlert, getPatient, UserContext } from "@/lib/db";
import { formatDistanceToNow } from "date-fns";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { ManageAlertDialog } from "@/components/alerts/ManageAlertDialog";
import { ArrowLeft, User, FileText, Activity, AlertTriangle, Pill, Bot, Loader2 } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ModernAudioPlayer } from "@/components/alerts/ModernAudioPlayer";
import { useSession } from "next-auth/react";
import { useEffect, useState } from "react";
import { Alert, Patient } from "@/types/patient";

export default function AlertDetailPage() {
    const params = useParams();
    const id = params.id as string;
    const { data: session, status } = useSession();

    const [alert, setAlert] = useState<Alert | null>(null);
    const [patient, setPatient] = useState<Patient | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function loadData() {
            if (status === 'authenticated' && session?.user && id) {
                try {
                    const userContext: UserContext = {
                        hospitalId: (session.user as any).hospitalId,
                        role: (session.user as any).role,
                        email: session.user.email || undefined
                    };

                    const alertData = await getAlert(id, userContext);
                    setAlert(alertData);

                    if (alertData && alertData.patientId) {
                        const patientData = await getPatient(alertData.patientId, userContext);
                        setPatient(patientData);
                    }
                } catch (error) {
                    console.error("Error loading alert data:", error);
                } finally {
                    setLoading(false);
                }
            } else if (status === 'unauthenticated') {
                setLoading(false);
            }
        }
        loadData();
    }, [session, status, id]);


    if (status === 'loading' || loading) {
        return (
            <div className="flex items-center justify-center h-screen">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    if (!alert) return <div className="p-8 text-center">Alert not found.</div>;

    const getPriorityColor = (priority: string) => {
        switch (priority) {
            case 'critical': return 'text-red-500 bg-red-50 border-red-200';
            case 'warning': return 'text-yellow-500 bg-yellow-50 border-yellow-200';
            default: return 'text-green-500 bg-green-50 border-green-200';
        }
    };

    return (
        <div className="space-y-6 max-w-7xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-700">
            {/* Header */}
            <div className="flex items-center gap-4">
                <Link href="/alerts">
                    <Button variant="ghost" size="icon">
                        <ArrowLeft className="h-5 w-5" />
                    </Button>
                </Link>
                <div>
                    <h1 className="text-2xl font-bold flex items-center gap-3">
                        Alert Resolution
                        <Badge variant="outline" className={getPriorityColor(alert.priority)}>
                            {(alert.priority || 'UNKNOWN').toUpperCase()}
                        </Badge>
                    </h1>
                    <p className="text-muted-foreground">
                        ID: {alert.id} • Created {alert.createdAt ? formatDistanceToNow(new Date(alert.createdAt), { addSuffix: true }) : 'N/A'}
                    </p>
                </div>
                <div className="ml-auto">
                    <ManageAlertDialog alert={alert} />
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                {/* Left Column: Patient Context */}
                <div className="lg:col-span-1 space-y-6">
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <User className="h-5 w-5 text-primary" />
                                Patient Profile
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div>
                                <div className="text-lg font-bold">{alert.patientName}</div>
                                <div className="text-sm text-muted-foreground">ID: {alert.patientId}</div>
                            </div>
                            {patient && (
                                <>
                                    <div className="pt-2 border-t">
                                        <span className="text-sm font-semibold block mb-1">Diagnosis</span>
                                        <span className="text-sm">{patient.diagnosis}</span>
                                    </div>
                                    <div className="pt-2 border-t">
                                        <span className="text-sm font-semibold block mb-1">Contact</span>
                                        <span className="text-sm">{patient.contactNumber}</span>
                                    </div>
                                    <div className="pt-4">
                                        <Link href={`/patient/${patient.id}`}>
                                            <Button variant="outline" className="w-full">View Full Profile</Button>
                                        </Link>
                                    </div>
                                </>
                            )}
                        </CardContent>
                    </Card>

                    {patient && patient.medicationPlan && (
                        <Card>
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2">
                                    <Pill className="h-5 w-5 text-blue-500" />
                                    Active Medications
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <ul className="space-y-3">
                                    {patient.medicationPlan.map((med, idx) => (
                                        <li key={idx} className="text-sm flex justify-between items-start">
                                            <span className="font-medium">{med.name}</span>
                                            <span className="text-muted-foreground text-xs">{med.frequency}</span>
                                        </li>
                                    ))}
                                </ul>
                            </CardContent>
                        </Card>
                    )}
                </div>

                {/* Right Column: Alert Details & Action */}
                <div className="lg:col-span-2 space-y-6">
                    {/* The Alert Trigger */}
                    <Card className="border-l-4 border-l-destructive shadow-sm">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2 text-destructive">
                                <AlertTriangle className="h-5 w-5" />
                                Trigger Event
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <p className="text-lg font-medium">{alert.trigger}</p>
                        </CardContent>
                    </Card>

                    {/* AI Brief / Analysis */}
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Activity className="h-5 w-5 text-primary" />
                                AI Analysis
                            </CardTitle>
                            <CardDescription>Automated insights based on patient history and interaction.</CardDescription>
                        </CardHeader>
                        <CardContent className="prose prose-sm max-w-none bg-muted/30 p-4 rounded-md">
                            {alert.brief ? (
                                <p>{alert.brief}</p>
                            ) : (
                                <p className="text-muted-foreground italic">No detailed AI brief available for this alert.</p>
                            )}
                        </CardContent>
                    </Card>

                    {/* Status & Resolution Info */}
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <FileText className="h-5 w-5 text-primary" />
                                Resolution Status
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <span className="text-sm text-muted-foreground block">Current Status</span>
                                    <Badge variant={alert.status === 'resolved' ? 'secondary' : 'default'} className="mt-1">
                                        {(alert.status || 'ACTIVE').toUpperCase()}
                                    </Badge>
                                </div>
                                <div>
                                    <span className="text-sm text-muted-foreground block">Priority</span>
                                    <span className="font-medium capitalize">{alert.priority}</span>
                                </div>
                            </div>

                            <div className="pt-6 flex justify-end">
                                <ManageAlertDialog alert={alert} />
                            </div>
                        </CardContent>
                    </Card>

                    {/* Audio Recording (Replaces Interaction Context) */}
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Bot className="h-5 w-5 text-primary" />
                                Audio Context
                            </CardTitle>
                            <CardDescription>
                                Original call recording used for this analysis.
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            {alert.callSid ? (
                                <ModernAudioPlayer src={`/api/audio/${alert.callSid}`} />
                            ) : (
                                <div className="text-muted-foreground italic text-sm">
                                    No output audio available for this alert.
                                </div>
                            )}
                        </CardContent>
                    </Card>

                </div>
            </div>
        </div>
    );
}
