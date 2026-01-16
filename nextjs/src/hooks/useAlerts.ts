"use client";

import { useEffect, useState } from "react";
import {
    collection,
    query,
    where,
    orderBy,
    onSnapshot,
    Timestamp,
} from "firebase/firestore";
import { db } from "@/lib/firebase";
import { Alert, RiskLevel } from "@/types/patient";

/**
 * Real-time Firestore hook for alerts.
 * Subscribes to alerts collection and updates automatically when changes occur.
 * 
 * @param hospitalId - Optional hospital ID to filter alerts (defaults to HOSP001)
 * @returns { alerts, loading, error, criticalCount }
 */
export function useAlerts(hospitalId: string = "HOSP001") {
    const [alerts, setAlerts] = useState<Alert[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<Error | null>(null);

    useEffect(() => {
        // Build query - simple query to avoid composite index requirement
        // Filter by hospitalId only, then filter status client-side
        const alertsRef = collection(db, "alerts");
        const q = query(
            alertsRef,
            where("hospitalId", "==", hospitalId),
            orderBy("createdAt", "desc")
        );

        // Subscribe to real-time updates
        const unsubscribe = onSnapshot(
            q,
            (snapshot) => {
                const allAlerts: Alert[] = snapshot.docs.map((doc) => {
                    const data = doc.data();
                    return {
                        id: doc.id,
                        patientId: data.patientId || "",
                        patientName: data.patientName || "Unknown",
                        hospitalId: data.hospitalId || "",
                        priority: (data.priority as RiskLevel) || "safe",
                        status: data.status || "active",
                        trigger: data.trigger || "",
                        aiBrief: data.aiBrief || "",
                        callSid: data.callSid,
                        resolutionNote: data.resolutionNote,
                        createdAt: data.createdAt instanceof Timestamp
                            ? data.createdAt.toDate()
                            : new Date(data.createdAt || Date.now()),
                        updatedAt: data.updatedAt instanceof Timestamp
                            ? data.updatedAt.toDate()
                            : undefined,
                    };
                });

                // Client-side filter for active/in_progress status
                const activeAlerts = allAlerts.filter(
                    a => a.status === "active" || a.status === "in_progress"
                );

                setAlerts(activeAlerts);
                setLoading(false);
                setError(null);
            },
            (err) => {
                console.error("Firestore onSnapshot error:", err);
                setError(err);
                setLoading(false);
            }
        );

        // Cleanup subscription on unmount
        return () => unsubscribe();
    }, [hospitalId]);

    // Compute critical count (critical + warning)
    const criticalCount = alerts.filter(
        (a) => a.priority === "critical" || a.priority === "warning"
    ).length;

    return { alerts, loading, error, criticalCount };
}
