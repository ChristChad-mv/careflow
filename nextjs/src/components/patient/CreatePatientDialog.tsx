'use client';

import { useState } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { createPatientClient } from '@/lib/client-actions';
import { useSession } from 'next-auth/react';
import { toast } from 'sonner';
import { useRouter } from 'next/navigation';
import { UserContext } from '@/lib/db';
import { Loader2 } from 'lucide-react';

interface CreatePatientDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
}

export function CreatePatientDialog({ open, onOpenChange }: CreatePatientDialogProps) {
    const { data: session } = useSession();
    const router = useRouter();
    const [loading, setLoading] = useState(false);

    const [formData, setFormData] = useState({
        name: '',
        contactNumber: '',
        email: '',
        diagnosis: '',
        dateOfBirth: '',
        preferredLanguage: 'English'
    });

    const handleChange = (field: string, value: string) => {
        setFormData(prev => ({ ...prev, [field]: value }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!session?.user) {
            toast.error("Unauthorized");
            return;
        }

        if (!formData.name || !formData.contactNumber) {
            toast.error("Name and Contact Number are required");
            return;
        }

        setLoading(true);

        try {
            const userContext: UserContext = {
                hospitalId: (session.user as any).hospitalId,
                role: (session.user as any).role,
                email: session.user.email || undefined
            };

            await createPatientClient(formData, userContext);

            toast.success("Patient created successfully");
            onOpenChange(false);
            setFormData({
                name: '',
                contactNumber: '',
                email: '',
                diagnosis: '',
                dateOfBirth: '',
                preferredLanguage: 'English'
            });
            router.refresh();
        } catch (error) {
            console.error(error);
            toast.error("Failed to create patient");
        } finally {
            setLoading(false);
        }
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                    <DialogTitle>Add New Patient</DialogTitle>
                    <DialogDescription>
                        Enter the patient's basic information to onboard them.
                    </DialogDescription>
                </DialogHeader>

                <form onSubmit={handleSubmit} className="space-y-4 py-4">
                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label htmlFor="name">Full Name *</Label>
                            <Input
                                id="name"
                                placeholder="John Doe"
                                value={formData.name}
                                onChange={(e) => handleChange('name', e.target.value)}
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="dob">Date of Birth</Label>
                            <Input
                                id="dob"
                                type="date"
                                value={formData.dateOfBirth}
                                onChange={(e) => handleChange('dateOfBirth', e.target.value)}
                            />
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label htmlFor="phone">Phone Number *</Label>
                            <Input
                                id="phone"
                                placeholder="+1 555-000-0000"
                                value={formData.contactNumber}
                                onChange={(e) => handleChange('contactNumber', e.target.value)}
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="email">Email (Optional)</Label>
                            <Input
                                id="email"
                                type="email"
                                placeholder="john@example.com"
                                value={formData.email}
                                onChange={(e) => handleChange('email', e.target.value)}
                            />
                        </div>
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="diagnosis">Primary Diagnosis</Label>
                        <Input
                            id="diagnosis"
                            placeholder="e.g. Heart Failure, COPD"
                            value={formData.diagnosis}
                            onChange={(e) => handleChange('diagnosis', e.target.value)}
                        />
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="language">Preferred Language</Label>
                        <Select
                            value={formData.preferredLanguage}
                            onValueChange={(val) => handleChange('preferredLanguage', val)}
                        >
                            <SelectTrigger>
                                <SelectValue placeholder="Select Language" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="English">English</SelectItem>
                                <SelectItem value="Spanish">Spanish</SelectItem>
                                <SelectItem value="French">French</SelectItem>
                                <SelectItem value="German">German</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>

                    <DialogFooter className="pt-4">
                        <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={loading}>
                            Cancel
                        </Button>
                        <Button type="submit" disabled={loading}>
                            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            Create Patient
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
}
