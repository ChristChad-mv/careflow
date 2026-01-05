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
import { Patient, Medication } from '@/types/patient';
import { updatePatient } from '@/lib/actions';
import { Pencil, Plus, Trash2 } from 'lucide-react';
import { toast } from 'sonner';

interface EditMedicationDialogProps {
    patient: Patient;
}

export function EditMedicationDialog({ patient }: EditMedicationDialogProps) {
    const [open, setOpen] = useState(false);
    const [medications, setMedications] = useState<Medication[]>(patient.medicationPlan || []);
    const [loading, setLoading] = useState(false);

    // New medication state
    const [newMed, setNewMed] = useState<Medication>({
        name: '',
        dosage: '',
        frequency: '',
        instructions: ''
    });

    const handleAddMedication = () => {
        if (!newMed.name || !newMed.dosage) {
            toast.error("Name and Dosage are required");
            return;
        }
        setMedications([...medications, newMed]);
        setNewMed({ name: '', dosage: '', frequency: '', instructions: '' });
    };

    const handleRemoveMedication = (index: number) => {
        const updated = medications.filter((_, i) => i !== index);
        setMedications(updated);
    };

    const handleSave = async () => {
        setLoading(true);
        try {
            await updatePatient(patient.id, { medicationPlan: medications });
            toast.success("Medication plan updated");
            setOpen(false);
        } catch (error) {
            console.error(error);
            toast.error("Failed to update medication plan");
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
            <DialogContent className="max-w-2xl">
                <DialogHeader>
                    <DialogTitle>Edit Medication Plan</DialogTitle>
                    <DialogDescription>
                        Update the active medication schedule for {patient.name}.
                    </DialogDescription>
                </DialogHeader>

                <div className="space-y-6 my-4">
                    {/* List of current meds */}
                    <div className="space-y-3">
                        {medications.map((med, index) => (
                            <div key={index} className="flex items-start justify-between bg-secondary/50 p-3 rounded-md border">
                                <div>
                                    <div className="font-semibold">{med.name}</div>
                                    <div className="text-sm text-muted-foreground">
                                        {med.dosage} • {med.frequency}
                                        {med.instructions && <div className="italic mt-1">"{med.instructions}"</div>}
                                    </div>
                                </div>
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    className="text-destructive hover:text-destructive hover:bg-destructive/10"
                                    onClick={() => handleRemoveMedication(index)}
                                >
                                    <Trash2 className="h-4 w-4" />
                                </Button>
                            </div>
                        ))}
                        {medications.length === 0 && (
                            <div className="text-center text-muted-foreground p-4 bg-secondary/20 rounded-md border border-dashed">
                                No active medications. Add one below.
                            </div>
                        )}
                    </div>

                    {/* Add new med form */}
                    <div className="border-t pt-4">
                        <Label>Add New Medication</Label>
                        <div className="grid grid-cols-2 gap-4 mt-2">
                            <Input
                                placeholder="Name (e.g. Lisinopril)"
                                value={newMed.name}
                                onChange={(e) => setNewMed({ ...newMed, name: e.target.value })}
                            />
                            <Input
                                placeholder="Dosage (e.g. 10mg)"
                                value={newMed.dosage}
                                onChange={(e) => setNewMed({ ...newMed, dosage: e.target.value })}
                            />
                            <Input
                                placeholder="Frequency (e.g. Twice Daily)"
                                value={newMed.frequency}
                                onChange={(e) => setNewMed({ ...newMed, frequency: e.target.value })}
                            />
                            <Input
                                placeholder="Instructions (Optional)"
                                value={newMed.instructions || ''}
                                onChange={(e) => setNewMed({ ...newMed, instructions: e.target.value })}
                            />
                        </div>
                        <Button onClick={handleAddMedication} variant="secondary" className="w-full mt-3 gap-2">
                            <Plus className="h-4 w-4" /> Add to List
                        </Button>
                    </div>
                </div>

                <DialogFooter>
                    <Button variant="outline" onClick={() => setOpen(false)} disabled={loading}>
                        Cancel
                    </Button>
                    <Button onClick={handleSave} disabled={loading}>
                        {loading ? 'Saving...' : 'Save Changes'}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
