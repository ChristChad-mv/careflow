"use client";

import { useAlerts } from "@/hooks/useAlerts";
import { useSession } from "next-auth/react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertTriangle, Clock, Rocket } from "lucide-react";
import Link from "next/link";
import { formatDistanceToNow } from "date-fns";

/**
 * Real-time alerts list component.
 * Uses Firestore onSnapshot via useAlerts hook for live updates.
 */
export function AlertsRealtime() {
    const { data: session } = useSession();
    const hospitalId = (session?.user as any)?.hospitalId || "HOSP001";

    // Pass dynamic hospitalId, only fetch if we have a session (or fallback)
    const { alerts, loading, error } = useAlerts(hospitalId);

    // Sort by priority: critical > warning > others
    const sortedAlerts = [...alerts].sort((a, b) => {
        const priorityOrder: Record<string, number> = { critical: 0, warning: 1, safe: 2 };
        return (priorityOrder[a.priority] ?? 2) - (priorityOrder[b.priority] ?? 2);
    });

    const getPriorityColor = (priority: string) => {
        switch (priority) {
            case "critical":
                return "text-red-500 bg-red-50 border-red-200 dark:bg-red-950 dark:border-red-800";
            case "warning":
                return "text-yellow-500 bg-yellow-50 border-yellow-200 dark:bg-yellow-950 dark:border-yellow-800";
            default:
                return "text-green-500 bg-green-50 border-green-200 dark:bg-green-950 dark:border-green-800";
        }
    };

    if (loading) {
        return (
            <div className="space-y-4">
                {[1, 2, 3].map((i) => (
                    <Card key={i}>
                        <CardContent className="p-6">
                            <div className="flex items-center gap-4">
                                <Skeleton className="h-6 w-20" />
                                <Skeleton className="h-6 w-40" />
                                <Skeleton className="h-6 w-32 ml-auto" />
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>
        );
    }

    if (error) {
        return (
            <Card className="border-destructive">
                <CardContent className="py-8 text-center">
                    <AlertTriangle className="h-8 w-8 text-destructive mx-auto mb-2" />
                    <div className="text-destructive font-medium">
                        Failed to load alerts
                    </div>
                    <p className="text-muted-foreground text-sm mt-1">
                        {error.message}
                    </p>
                </CardContent>
            </Card>
        );
    }
    if (sortedAlerts.length === 0) {
        return (
            <Card className="border-dashed border-2 bg-muted/20">
                <CardContent className="py-16 text-center space-y-6">
                    <div className="mx-auto w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center text-primary animate-pulse">
                        <Rocket className="h-8 w-8" />
                    </div>
                    <div>
                        <div className="text-xl font-bold">
                            Welcome to the Hackathon Demo
                        </div>
                        <p className="text-muted-foreground mt-2 max-w-md mx-auto">
                            No critical alerts yet. To start the interactive demo, go back to the Dashboard and click <strong>"Hackathon Demo"</strong> to register as a patient.
                        </p>
                    </div>
                    <Link href="/dashboard">
                        <Button variant="default" className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-bold shadow-lg">
                            Go to Dashboard & Start Demo
                        </Button>
                    </Link>
                </CardContent>
            </Card>
        );
    }

    return (
        <div className="space-y-4">
            {sortedAlerts.map((alert) => (
                <Card
                    key={alert.id}
                    className={`border-2 transition-all animate-in fade-in slide-in-from-top-2 duration-300 ${alert.priority === "critical"
                        ? "border-destructive bg-destructive/5"
                        : alert.priority === "warning"
                            ? "border-warning bg-warning/5"
                            : ""
                        }`}
                >
                    <CardContent className="p-6">
                        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-center">
                            {/* Priority Badge */}
                            <div className="lg:col-span-2">
                                <Badge
                                    variant="outline"
                                    className={getPriorityColor(alert.priority)}
                                >
                                    {(alert.priority || "unknown").toUpperCase()}
                                </Badge>
                            </div>

                            {/* Patient Info */}
                            <div className="lg:col-span-2">
                                <div className="font-bold text-lg">{alert.patientName}</div>
                                <div className="text-sm text-muted-foreground">
                                    ID: {alert.patientId}
                                </div>
                            </div>

                            {/* Time */}
                            <div className="lg:col-span-2">
                                <div className="flex items-center gap-2 text-muted-foreground">
                                    <Clock className="h-4 w-4" />
                                    <span className="text-sm font-medium">
                                        {formatDistanceToNow(new Date(alert.createdAt), { addSuffix: true })}
                                    </span>
                                </div>
                            </div>

                            {/* Trigger */}
                            <div className="lg:col-span-4">
                                <div className="text-sm font-semibold text-foreground">
                                    {alert.trigger}
                                </div>
                            </div>

                            {/* Action */}
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
    );
}
