import { getAlert, getPatient, getInteractions } from "@/lib/db";
import { formatDistanceToNow, format } from "date-fns";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { ManageAlertDialog } from "@/components/alerts/ManageAlertDialog";
import { ArrowLeft, User, FileText, Activity, AlertTriangle, Pill, Clock, Bot } from "lucide-react";
import Link from "next/link";
import { notFound } from "next/navigation";

export default async function AlertDetailPage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = await params;
    const alert = await getAlert(id);
    if (!alert) return notFound();

    const [patient, interactions] = await Promise.all([
        getPatient(alert.patientId),
        getInteractions(alert.patientId)
    ]);

    const getPriorityColor = (priority: string) => {
        switch (priority) {
            case 'critical': return 'text-red-500 bg-red-50 border-red-200';
            case 'warning': return 'text-yellow-500 bg-yellow-50 border-yellow-200';
            default: return 'text-green-500 bg-green-50 border-green-200';
        }
    };

    return (
        <div className="space-y-6 max-w-7xl mx-auto">
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
                        ID: {alert.id} • Created {formatDistanceToNow(alert.createdAt, { addSuffix: true })}
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
                            {alert.resolutionNote && (
                                <div className="mt-4 pt-4 border-t">
                                    <span className="text-sm font-semibold block mb-2">Resolution Notes</span>
                                    <div className="bg-yellow-50 p-3 rounded-md text-sm border border-yellow-100 dark:bg-yellow-900/10 dark:border-yellow-900/50">
                                        {alert.resolutionNote}
                                    </div>
                                </div>
                            )}

                            <div className="pt-6 flex justify-end">
                                <ManageAlertDialog alert={alert} />
                            </div>
                        </CardContent>
                    </Card>

                    {/* Interaction Timeline */}
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Clock className="h-5 w-5 text-muted-foreground" />
                                Correct Context: Interaction History
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4 max-h-[400px] overflow-y-auto">
                                {interactions.map((interaction) => (
                                    <div
                                        key={interaction.id}
                                        className={`p-4 rounded-lg ${interaction.sender === 'ai'
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
                                {interactions.length === 0 && (
                                    <div className="text-center text-muted-foreground py-4">
                                        No interactions recorded yet.
                                    </div>
                                )}
                            </div>
                        </CardContent>
                    </Card>

                </div>
            </div>
        </div>
    );
}
