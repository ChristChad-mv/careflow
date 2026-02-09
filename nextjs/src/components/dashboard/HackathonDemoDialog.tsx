'use client';

import { useState } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { createPatientClient } from '@/lib/client-actions';
import { useSession } from 'next-auth/react';
import { toast } from 'sonner';
import { useRouter } from 'next/navigation';
import { UserContext } from '@/lib/db';
import { Loader2, Heart, Activity, Thermometer, Pill, AlertCircle, ClipboardList } from 'lucide-react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';

interface HackathonDemoDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
}

const SCENARIOS = [
    {
        id: 'cardiac',
        label: 'Heart Failure (Medication Management)',
        icon: Heart,
        data: {
            diagnosis: 'Congestive Heart Failure (NYHA Class III)',
            medicationPlan: [
                { name: 'Lisinopril', dosage: '10mg', frequency: 'Daily', instructions: 'Take in the morning, check blood pressure' },
                { name: 'Furosemide', dosage: '40mg', frequency: 'Daily', instructions: 'Take before 4pm to avoid nocturia' },
                { name: 'Metoprolol', dosage: '25mg', frequency: 'Twice daily', instructions: 'Pulse must be >60 before taking' },
                { name: 'Spironolactone', dosage: '25mg', frequency: 'Daily', instructions: 'Potassium-sparing diuretic' }
            ],
            criticalSymptoms: [
                'Sudden weight gain (>3lbs/day)',
                'Shortness of breath while resting',
                'New onset of confusion or dizziness',
                'Pink frothy sputum'
            ],
            warningSymptoms: [
                'Dry hacking cough',
                'Increased swelling in ankles/feet',
                'Difficulty sleeping flat (needs extra pillows)',
                'Persistent fatigue'
            ],
            dischargeInstructions: "Daily weights are mandatory. Limit sodium intake to <2g/day. Fluid restriction of 1.5L-2L per day."
        }
    },
    {
        id: 'respiratory',
        label: 'Pneumonia (Respiratory Distress)',
        icon: Activity,
        data: {
            diagnosis: 'Bacterial Pneumonia (Post-Acute Phase)',
            medicationPlan: [
                { name: 'Amoxicillin/Clavulanate', dosage: '875mg', frequency: 'Twice daily', instructions: 'Finish entire 10-day course' },
                { name: 'Albuterol Inhaler', dosage: '2 puffs', frequency: 'Every 4-6 hours PRN', instructions: 'For wheezing or shortness of breath' },
                { name: 'Guaifenesin', dosage: '600mg', frequency: 'Every 12 hours', instructions: 'Drink plenty of water to thin mucus' }
            ],
            criticalSymptoms: [
                'Severe chest pain when breathing',
                'Turning blue/grey around lips/nails',
                'Confusion or inability to wake up',
                'Tachypnea (>25 breaths per minute)'
            ],
            warningSymptoms: [
                'Returning high fever (>102°F)',
                'Yellow, green, or bloody mucus',
                'Increased chest tightness',
                'Inability to finish sentences without gasping'
            ],
            dischargeInstructions: "Rest in an upright position. Use incentive spirometer 10 times every hour while awake. Avoid smoke and irritants."
        }
    },
    {
        id: 'post-op',
        label: 'Post-CABG Recovery (Infection Risk)',
        icon: Thermometer,
        data: {
            diagnosis: 'Status Post Coronary Artery Bypass Graft (CABG x3)',
            medicationPlan: [
                { name: 'Aspirin', dosage: '81mg', frequency: 'Daily', instructions: 'Anti-platelet therapy' },
                { name: 'Clopidogrel', dosage: '75mg', frequency: 'Daily', instructions: 'Maintain stent patency' },
                { name: 'Atorvastatin', dosage: '40mg', frequency: 'Daily', instructions: 'Statin therapy' },
                { name: 'Oxycodone', dosage: '5mg', frequency: 'Every 6 hours PRN', instructions: 'For severe incision pain' }
            ],
            criticalSymptoms: [
                'Chest clicking or feeling bone "rubbing"',
                'Pus or bright red blood from incision',
                'Heart rate >120 or irregular rhythm',
                'Severe calf pain or swelling'
            ],
            warningSymptoms: [
                'Incision site becoming hot or very red',
                'Chills or night sweats',
                'Fever over 101°F',
                'Increasing shortness of breath'
            ],
            dischargeInstructions: "Do not lift anything heavier than 5lbs. No driving until cleared by surgeon. Wash incision with mild soap only."
        }
    }
];

export function HackathonDemoDialog({ open, onOpenChange }: HackathonDemoDialogProps) {
    const { data: session } = useSession();
    const router = useRouter();
    const [loading, setLoading] = useState(false);
    const [name, setName] = useState('');
    const [phone, setPhone] = useState('');
    const [scenarioId, setScenarioId] = useState(SCENARIOS[0].id);

    const selectedScenario = SCENARIOS.find(s => s.id === scenarioId) || SCENARIOS[0];

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!session?.user) {
            toast.error("Please login first");
            return;
        }

        if (!name || !phone) {
            toast.error("Name and Phone are required for the demo call");
            return;
        }

        setLoading(true);

        try {
            const userContext: UserContext = {
                hospitalId: (session.user as any).hospitalId,
                role: (session.user as any).role,
                email: session.user.email || undefined
            };

            // Calculate Next Appointment: Current Day + 3
            const nextAppointmentDate = new Date();
            nextAppointmentDate.setDate(nextAppointmentDate.getDate() + 3);

            const patientData = {
                name,
                email: session.user.email || 'demo-patient@careflow.com',
                contactNumber: phone,
                contact: {
                    phone: phone,
                    preferredMethod: 'phone'
                },
                preferredLanguage: 'en',
                riskLevel: 'green',
                status: 'active',
                hospitalId: (session.user as any).hospitalId || 'HOSP001',
                dateOfBirth: '1990-06-25',
                dischargeDate: new Date(),
                lastAssessedAt: new Date(),
                dischargingPhysician: 'Dr. A. Carter',
                assignedNurse: {
                    name: 'Sarah Johnson, RN',
                    email: 'judge-hackathon@careflow.demo',
                    phone: '+15559876543'
                },
                diagnosis: selectedScenario.data.diagnosis,
                criticalSymptoms: selectedScenario.data.criticalSymptoms,
                warningSymptoms: selectedScenario.data.warningSymptoms,
                medicationPlan: selectedScenario.data.medicationPlan.map(m => ({
                    name: m.name,
                    dosage: m.dosage,
                    frequency: m.frequency,
                    instructions: m.instructions,
                    scheduleHour: 8,
                    startDate: new Date()
                })),
                nextAppointment: {
                    date: nextAppointmentDate.toISOString(),
                    type: 'Follow-up',
                    location: 'Main Medical Center'
                },
                // Maintaining the flat structure for direct Agent access as seen in debug
                currentStatus: 'safe',
                scheduleHour: 8,
                dischargePlan: {
                    diagnosis: selectedScenario.data.diagnosis,
                    medications: selectedScenario.data.medicationPlan,
                    criticalSymptoms: selectedScenario.data.criticalSymptoms,
                    warningSymptoms: selectedScenario.data.warningSymptoms,
                    dischargeInstructions: selectedScenario.data.dischargeInstructions,
                    nextAppointmentDate: nextAppointmentDate.toISOString()
                }
            };

            const result = await createPatientClient(patientData, userContext);

            if (result.success) {
                toast.success("Demo Case Initialized!");
                onOpenChange(false);
                // Correct redirect path to /patient/[id]
                router.push(`/patient/${result.id}`);
            }
        } catch (error) {
            console.error(error);
            toast.error("Failed to initialize demo case");
        } finally {
            setLoading(false);
        }
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="w-[95vw] sm:max-w-[800px] h-[95vh] md:h-[90vh] bg-background border border-border shadow-2xl p-0 overflow-hidden flex flex-col">
                <div className="p-4 md:p-8 bg-gradient-to-r from-blue-600/20 to-indigo-600/20 dark:from-blue-600/10 dark:to-indigo-600/10 border-b border-primary/10 shrink-0">
                    <DialogHeader>
                        <DialogTitle className="text-2xl md:text-4xl font-bold flex flex-wrap items-center gap-3">
                            <span className="bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600 dark:from-primary dark:to-teal-400">
                                Hackathon Demo Mode
                            </span>
                            <Badge variant="outline" className="text-primary border-primary animate-pulse py-1">LIVE INTERACTIVE</Badge>
                        </DialogTitle>
                        <DialogDescription className="text-lg text-muted-foreground font-medium flex flex-col gap-3">
                            <span>Adopt a clinical patient profile and receive a simulated follow-up call.</span>
                            <div className="flex items-start gap-2 text-xs font-semibold bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 px-3 py-2 rounded-lg border border-blue-100 dark:border-blue-800/50 w-full sm:w-fit">
                                <span className="mt-0.5">🔒</span>
                                <span>DATAPOLICY: Your demo data is temporary and isolated. You have full control to delete all records instantly after the call.</span>
                            </div>
                        </DialogDescription>
                    </DialogHeader>
                </div>

                <form onSubmit={handleSubmit} className="flex-1 min-h-0 flex flex-col">
                    <ScrollArea className="flex-1 w-full">
                        <div className="px-4 md:px-10 py-6 md:py-8 space-y-6 md:space-y-10">
                            {/* Identity Section */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div className="space-y-2">
                                    <Label htmlFor="demo-name" className="text-sm font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                                        <ClipboardList className="h-4 w-4" /> 1. Your Identity
                                    </Label>
                                    <Input
                                        id="demo-name"
                                        placeholder="Full Name"
                                        value={name}
                                        onChange={(e) => setName(e.target.value)}
                                        className="h-12 bg-background border-primary/30 focus:border-primary text-lg shadow-sm"
                                        required
                                    />
                                </div>
                                <div className="space-y-2">
                                    <div className="flex justify-between items-center">
                                        <Label htmlFor="demo-phone" className="text-sm font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                                            <Activity className="h-4 w-4" /> 2. Phone Number
                                        </Label>
                                        {phone && (
                                            <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded-full ${/^\+[1-9]\d{1,14}$/.test(phone) ? 'bg-green-500/20 text-green-500' : 'bg-amber-500/20 text-amber-500'}`}>
                                                {/^\+[1-9]\d{1,14}$/.test(phone) ? 'VALID FORMAT' : 'INVALID FORMAT'}
                                            </span>
                                        )}
                                    </div>
                                    <Input
                                        id="demo-phone"
                                        type="tel"
                                        placeholder="e.g. +1... (US), +33... (FR), +34... (ES)"
                                        value={phone}
                                        onChange={(e) => setPhone(e.target.value.replace(/\s/g, ''))}
                                        className={`h-12 bg-background border-primary/30 focus:border-primary text-lg shadow-sm ${phone && !/^\+[1-9]\d{1,14}$/.test(phone) ? 'border-amber-500/50' : ''}`}
                                        required
                                    />
                                    <div className="space-y-1">
                                        <p className="text-[10px] text-primary/80 font-bold uppercase tracking-tight">MUST INCLUDE "+" AND COUNTRY CODE</p>
                                        <p className="text-[10px] text-muted-foreground">The AI will call this number directly for the recovery scenario.</p>
                                    </div>
                                </div>
                            </div>

                            {/* Scenario Selection */}
                            <div className="space-y-4">
                                <Label className="text-sm font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                                    <AlertCircle className="h-4 w-4" /> 3. Select Medical Scenario
                                </Label>
                                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                                    {SCENARIOS.map((s) => (
                                        <div
                                            key={s.id}
                                            onClick={() => setScenarioId(s.id)}
                                            className={`p-4 rounded-xl border-2 transition-all cursor-pointer flex flex-col items-center text-center gap-2 ${scenarioId === s.id
                                                ? "border-primary bg-primary/10 shadow-md ring-2 ring-primary/20"
                                                : "border-border bg-muted/40 hover:border-primary/40 hover:bg-muted/60"
                                                }`}
                                        >
                                            <s.icon className={`h-8 w-8 ${scenarioId === s.id ? "text-primary" : "text-muted-foreground opacity-70"}`} />
                                            <span className={`text-xs font-bold leading-tight ${scenarioId === s.id ? "text-primary" : "text-muted-foreground"}`}>
                                                {s.label}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Giant Medical Preview */}
                            <div className="bg-muted/50 dark:bg-muted/30 rounded-2xl p-6 border border-border shadow-inner space-y-6">
                                <div className="flex items-center justify-between border-b border-border pb-4">
                                    <h3 className="font-bold text-xl flex items-center gap-2 text-foreground">
                                        <selectedScenario.icon className="h-5 w-5 text-primary" />
                                        Medical Record Preview
                                    </h3>
                                    <Badge className="bg-success text-success-foreground border-none">STABLE</Badge>
                                </div>

                                <div className="space-y-6">
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-6">
                                        <div className="space-y-3">
                                            <h4 className="flex items-center gap-2 text-sm font-bold text-primary">
                                                <Pill className="h-4 w-4" /> Medication Plan
                                            </h4>
                                            <div className="space-y-3">
                                                {selectedScenario.data.medicationPlan.map((m, idx) => (
                                                    <div key={idx} className="text-xs bg-background/40 p-2 rounded shadow-sm">
                                                        <div className="font-bold">{m.name} - {m.dosage}</div>
                                                        <div className="text-muted-foreground">{m.frequency}</div>
                                                        <div className="italic mt-1 text-[10px] opacity-80">{m.instructions}</div>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>

                                        <div className="space-y-3">
                                            <h4 className="flex items-center gap-2 text-sm font-bold text-red-500">
                                                <AlertCircle className="h-4 w-4" /> Critical Symptoms
                                            </h4>
                                            <ul className="space-y-1.5 list-disc list-inside text-xs text-muted-foreground">
                                                {selectedScenario.data.criticalSymptoms.map((s, idx) => (
                                                    <li key={idx}>{s}</li>
                                                ))}
                                            </ul>
                                            <h4 className="flex items-center gap-2 text-sm font-bold text-yellow-600 mt-4">
                                                <Thermometer className="h-4 w-4" /> Warning Signs
                                            </h4>
                                            <ul className="space-y-1.5 list-disc list-inside text-xs text-muted-foreground">
                                                {selectedScenario.data.warningSymptoms.map((s, idx) => (
                                                    <li key={idx}>{s}</li>
                                                ))}
                                            </ul>
                                        </div>
                                    </div>

                                    <div className="pt-4 border-t border-border">
                                        <h4 className="text-xs font-bold text-muted-foreground mb-1 uppercase tracking-widest">Discharge Diagnosis</h4>
                                        <p className="text-sm font-medium">{selectedScenario.data.diagnosis}</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </ScrollArea>

                    <div className="p-4 md:p-8 border-t border-border bg-background/50 shrink-0">
                        <Button
                            type="submit"
                            disabled={loading || !name || !phone}
                            className="w-full h-14 md:h-16 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white text-base md:text-lg font-bold rounded-xl md:rounded-2xl transition-all shadow-xl hover:shadow-primary/30"
                        >
                            {loading ? (
                                <Loader2 className="mr-2 h-6 w-6 animate-spin" />
                            ) : (
                                "ACTIVATE CASE & START DEMO"
                            )}
                        </Button>
                    </div>
                </form>
            </DialogContent>
        </Dialog>
    );
}
