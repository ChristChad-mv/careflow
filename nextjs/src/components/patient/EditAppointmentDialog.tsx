'use client';

import { useState } from 'react';
import { Button } from "@/components/ui/button";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { Patient } from '@/types/patient';
import { updatePatientClient } from '@/lib/client-actions';
import { Pencil } from 'lucide-react';
import { toast } from 'sonner';
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { UserContext } from '@/lib/db';

interface EditAppointmentDialogProps {
    patient: Patient;
}

export function EditAppointmentDialog({ patient }: EditAppointmentDialogProps) {
    const [open, setOpen] = useState(false);
    const [loading, setLoading] = useState(false);

    const { data: session } = useSession();
    const router = useRouter();

    // Initial state from patient or empty defaults
    const [appointment, setAppointment] = useState({
        date: patient.nextAppointment?.date || '',
        type: patient.nextAppointment?.type || '',
        location: patient.nextAppointment?.location || ''
    });

    const handleSave = async () => {
        if (!session?.user) {
            toast.error("Unauthorized");
            return;
        }
        setLoading(true);
        try {
            const userContext: UserContext = {
                hospitalId: (session.user as any).hospitalId,
                role: (session.user as any).role,
                email: session.user.email || undefined
            };

            // If fields are empty, we might want to clear the appointment
            // For now, we update whatever is there
            await updatePatientClient(patient.id, { nextAppointment: appointment }, userContext);
            toast.success("Appointment updated");
            setOpen(false);
            router.refresh();
        } catch (error) {
            console.error(error);
            toast.error("Failed to update appointment");
        } finally {
            setLoading(false);
        }
    };

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
                <Button variant="ghost" size="icon" className="h-8 w-8">
                    <Pencil className="h-4 w-4" />
                </Button>
            </DialogTrigger>
            <DialogContent>
                <DialogHeader>
                    <DialogTitle>Update Next Appointment</DialogTitle>
                    <DialogDescription>
                        Schedule the next check-in or consultation.
                    </DialogDescription>
                </DialogHeader>

                <div className="grid gap-4 py-4">
                    <div className="grid gap-2">
                        <Label htmlFor="date">Date</Label>
                        <Input
                            id="date"
                            type="datetime-local"
                            value={appointment.date}
                            onChange={(e) => setAppointment({ ...appointment, date: e.target.value })}
                        />
                    </div>
                    <div className="grid gap-2">
                        <Label htmlFor="type">Type</Label>
                        <Select
                            value={appointment.type}
                            onValueChange={(val) => setAppointment({ ...appointment, type: val })}
                        >
                            <SelectTrigger>
                                <SelectValue placeholder="Select type" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="General Check-up">General Check-up</SelectItem>
                                <SelectItem value="Specialist Consultation">Specialist Consultation</SelectItem>
                                <SelectItem value="Lab Work">Lab Work</SelectItem>
                                <SelectItem value="Follow-up">Follow-up</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                    <div className="grid gap-2">
                        <Label htmlFor="location">Location</Label>
                        <Select
                            value={appointment.location}
                            onValueChange={(val) => setAppointment({ ...appointment, location: val })}
                        >
                            <SelectTrigger>
                                <SelectValue placeholder="Select location" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="City General Hospital">City General Hospital</SelectItem>
                                <SelectItem value="Heart Rate Clinic">Heart Rate Clinic</SelectItem>
                                <SelectItem value="Home Visit">Home Visit</SelectItem>
                                <SelectItem value="Telehealth">Telehealth</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                </div>

                <DialogFooter>
                    <Button variant="outline" onClick={() => setOpen(false)} disabled={loading}>
                        Cancel
                    </Button>
                    <Button onClick={handleSave} disabled={loading}>
                        {loading ? 'Saving...' : 'Update Appointment'}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
