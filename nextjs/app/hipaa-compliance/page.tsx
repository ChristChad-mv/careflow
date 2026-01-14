"use client";

import Link from "next/link";
import { ArrowLeft, FileCheck, Server, Shield, Network } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function HIPAACompliance() {
    return (
        <div className="min-h-screen bg-background selection:bg-primary/20 pt-24 pb-20">
            <div className="container mx-auto px-6 max-w-4xl">
                <Link href="/">
                    <Button variant="ghost" className="mb-8 hover:bg-white/5">
                        <ArrowLeft className="mr-2 h-4 w-4" /> Back to Home
                    </Button>
                </Link>

                <div className="space-y-4 mb-12">
                    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-500/10 text-teal-400 border border-teal-500/20 text-xs font-bold uppercase tracking-widest">
                        <Shield className="h-3 w-3" /> Technical Compliance Guide
                    </div>
                    <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight">HIPAA Compliance</h1>
                    <p className="text-xl text-muted-foreground">How CareFlow Architecture Meets Technical Safeguards.</p>
                </div>

                <div className="prose prose-invert max-w-none space-y-12">

                    <div className="p-6 border border-white/10 rounded-2xl bg-white/5">
                        <p className="italic text-muted-foreground">
                            <strong>Note:</strong> CareFlow operates as a "Business Associate" under HIPAA. We execute a comprehensive Business Associate Agreement (BAA) with all healthcare provider partners ensuring legal protection and accountability.
                        </p>
                    </div>

                    <section className="space-y-6">
                        <h2 className="text-2xl font-bold flex items-center gap-3">
                            <Server className="h-6 w-6 text-primary" />
                            Access Control & Isolation
                        </h2>
                        <div className="grid gap-6">
                            <div className="space-y-2">
                                <h3 className="font-bold text-lg text-white">Row-Level Security (RLS)</h3>
                                <p className="text-muted-foreground">
                                    CareFlow implements strict multi-tenancy at the database kernel level (Firestore Security Rules). A clinician from Hospital A can <em>never</em> technically query data from Hospital B. This is enforced by cryptographic token verification on every read/write operation.
                                </p>
                            </div>
                            <div className="space-y-2">
                                <h3 className="font-bold text-lg text-white">Zero-Trust Identity</h3>
                                <p className="text-muted-foreground">
                                    We allow no anonymous access. All sessions are authenticated via industry-standard Identity Providers (IdP) with mandatory MFA support for clinical staff accounts.
                                </p>
                            </div>
                        </div>
                    </section>

                    <section className="space-y-6">
                        <h2 className="text-2xl font-bold flex items-center gap-3">
                            <FileCheck className="h-6 w-6 text-teal-400" />
                            Audit Integrity
                        </h2>
                        <p className="text-muted-foreground">
                            HIPAA requires knowing <em>who</em> accessed <em>what</em> and <em>when</em>.
                        </p>
                        <ul className="space-y-4">
                            <li className="p-4 rounded-xl bg-white/5 border border-white/5">
                                <strong className="block text-white mb-1">Immutable Audit Logs</strong>
                                <span className="text-sm text-muted-foreground">Every mutation (create, update, delete) to a patient record generates a simplified, write-only audit entry stored in a separate, locked collection tailored for compliance review.</span>
                            </li>
                            <li className="p-4 rounded-xl bg-white/5 border border-white/5">
                                <strong className="block text-white mb-1">Access Traceability</strong>
                                <span className="text-sm text-muted-foreground">System logs capture the identity of the actor (human or AI agent) for every API request, ensuring a complete chain of custody for PHI.</span>
                            </li>
                        </ul>
                    </section>

                    <section className="space-y-6">
                        <h2 className="text-2xl font-bold flex items-center gap-3">
                            <Network className="h-6 w-6 text-blue-400" />
                            Transmission Security
                        </h2>
                        <p className="text-muted-foreground">
                            Data in transit is protected by high-standard encryption protocols.
                        </p>
                        <ul className="list-disc list-inside space-y-2 text-muted-foreground pl-2">
                            <li><strong>Encryption:</strong> All traffic is encrypted via TLS 1.3 (Transport Layer Security).</li>
                            <li><strong>HSTS:</strong> HTTP Strict Transport Security is enforced, preventing any downgrade attacks to unencrypted HTTP.</li>
                            <li><strong>At Rest:</strong> All data stored in our cloud infrastructure is encrypted at rest using AES-256 standards.</li>
                        </ul>
                    </section>

                    <div className="pt-12 border-t border-white/10 flex flex-col items-center text-center gap-6">
                        <p className="text-lg font-medium text-white">Ready to review our BAA?</p>
                        <Link href="mailto:compliance@careflow.com">
                            <Button size="lg" className="rounded-full px-8 bg-white text-black hover:bg-white/90">
                                Request Full BAA Packet
                            </Button>
                        </Link>
                    </div>
                </div>
            </div>
        </div>
    );
}
