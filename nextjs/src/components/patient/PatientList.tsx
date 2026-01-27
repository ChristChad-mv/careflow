'use client';

import { Patient } from "@/types/patient";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Phone, ArrowRight, Activity } from "lucide-react";
import Link from "next/link";

interface PatientListProps {
    patients: Patient[];
}

export function PatientList({ patients }: PatientListProps) {
    if (patients.length === 0) {
        return (
            <div className="text-center py-12">
                <div className="bg-muted/30 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                    <Activity className="h-8 w-8 text-muted-foreground" />
                </div>
                <h3 className="text-lg font-medium">No patients found</h3>
                <p className="text-muted-foreground mt-2">Try adjusting your search or add a new patient.</p>
            </div>
        );
    }

    const getInitials = (name: string) => {
        return name
            .split(' ')
            .map(n => n[0])
            .join('')
            .toUpperCase()
            .slice(0, 2);
    };

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {patients.map((patient) => (
                <Card key={patient.id} className="hover:shadow-lg transition-all duration-300 border-l-4"
                    style={{
                        borderLeftColor: patient.currentStatus === 'critical' ? 'hsl(var(--destructive))' :
                            patient.currentStatus === 'warning' ? '#eab308' : '#22c55e'
                    }}>
                    <CardHeader className="flex flex-row items-center gap-4 pb-2">
                        <Avatar className="h-10 w-10">
                            <AvatarFallback>{getInitials(patient.name)}</AvatarFallback>
                        </Avatar>
                        <div className="flex-1 overflow-hidden">
                            <CardTitle className="text-lg truncate">{patient.name}</CardTitle>
                            <p className="text-xs text-muted-foreground truncate">ID: {patient.id}</p>
                        </div>
                        <Badge variant={patient.currentStatus === 'critical' ? 'destructive' : 'secondary'}>
                            {patient.currentStatus.toUpperCase()}
                        </Badge>
                    </CardHeader>
                    <CardContent className="pb-2">
                        <div className="text-sm text-muted-foreground mt-2 space-y-2">
                            <div className="flex items-center gap-2">
                                <Activity className="h-3 w-3" />
                                <span className="truncate">{patient.diagnosis || 'No Diagnosis'}</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <Phone className="h-3 w-3" />
                                <span>{patient.contactNumber}</span>
                            </div>
                        </div>
                    </CardContent>
                    <CardFooter className="pt-2">
                        <Link href={`/patient/${patient.id}`} className="w-full">
                            <Button variant="ghost" className="w-full justify-between group">
                                View Profile
                                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                            </Button>
                        </Link>
                    </CardFooter>
                </Card>
            ))}
        </div>
    );
}
