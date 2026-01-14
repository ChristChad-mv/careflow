"use client";

import Link from "next/link";
import { ArrowLeft, Shield, Lock, Activity, Zap, Code2, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function Security() {
    return (
        <div className="min-h-screen bg-background selection:bg-primary/20 pt-24 pb-20">
            <div className="container mx-auto px-6 max-w-4xl">
                <Link href="/">
                    <Button variant="ghost" className="mb-8 hover:bg-white/5">
                        <ArrowLeft className="mr-2 h-4 w-4" /> Back to Home
                    </Button>
                </Link>

                <div className="space-y-4 mb-12">
                    <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight">Security Architecture</h1>
                    <p className="text-xl text-muted-foreground">A transparent look at how we secure the intelligent healthcare stack.</p>
                </div>

                <div className="prose prose-invert max-w-none space-y-16">

                    {/* Section: AI Security */}
                    <section className="space-y-6">
                        <h2 className="text-2xl font-bold flex items-center gap-3">
                            <Shield className="h-6 w-6 text-primary" />
                            AI Defense-in-Depth (Google Model Armor)
                        </h2>
                        <p className="text-muted-foreground leading-relaxed">
                            We deploy advanced specialized security filters directly into the AI inference pipeline, ensuring safe and appropriate interactions.
                        </p>

                        <div className="grid md:grid-cols-2 gap-4">
                            <div className="p-5 rounded-2xl bg-white/5 border border-white/10">
                                <h3 className="font-bold text-white mb-2 flex items-center gap-2"><Lock className="h-4 w-4 text-teal-400" /> Input Protection</h3>
                                <p className="text-sm text-muted-foreground">Blocks "Jailbreak" attempts, prompt injection attacks, and adversarial inputs designed to manipulate the clinical persona.</p>
                            </div>
                            <div className="p-5 rounded-2xl bg-white/5 border border-white/10">
                                <h3 className="font-bold text-white mb-2 flex items-center gap-2"><Activity className="h-4 w-4 text-blue-400" /> Output Sanitization</h3>
                                <p className="text-sm text-muted-foreground">Real-time DLP scanning prevents the model from leaking sensitive data (PHI) or hallucinating inappropriate content.</p>
                            </div>
                        </div>
                    </section>

                    {/* Section: Application Security */}
                    <section className="space-y-6">
                        <h2 className="text-2xl font-bold flex items-center gap-3">
                            <Code2 className="h-6 w-6 text-teal-400" />
                            Application Hardening
                        </h2>
                        <p className="text-muted-foreground">
                            Our frontend and backend follow rigorous security standards verified by regular automated audits.
                        </p>
                        <ul className="space-y-4">
                            <li className="flex gap-4 items-start">
                                <div className="h-6 w-6 rounded-full bg-success/10 flex items-center justify-center flex-shrink-0 mt-1"><Zap className="h-3 w-3 text-success" /></div>
                                <div>
                                    <strong className="text-white">Strict Rate Limiting: </strong>
                                    <span className="text-muted-foreground">Powered by Redis, we enforce granular limits (e.g., 20 req/min for APIs) to prevent DoS attacks and brute-force attempts.</span>
                                </div>
                            </li>
                            <li className="flex gap-4 items-start">
                                <div className="h-6 w-6 rounded-full bg-success/10 flex items-center justify-center flex-shrink-0 mt-1"><Zap className="h-3 w-3 text-success" /></div>
                                <div>
                                    <strong className="text-white">Content Security Policy (CSP): </strong>
                                    <span className="text-muted-foreground">We enforce strict content sources, disallowing unauthorized scripts, styles, or frames from executing in your browser.</span>
                                </div>
                            </li>
                            <li className="flex gap-4 items-start">
                                <div className="h-6 w-6 rounded-full bg-success/10 flex items-center justify-center flex-shrink-0 mt-1"><Zap className="h-3 w-3 text-success" /></div>
                                <div>
                                    <strong className="text-white">Input Validation: </strong>
                                    <span className="text-muted-foreground">Every API endpoint utilizes Zod schemas to strip malicious payloads and prevent mass-assignment vulnerabilities.</span>
                                </div>
                            </li>
                        </ul>
                    </section>

                    {/* Section: Vulnerability Reporting */}
                    <section className="p-8 rounded-3xl bg-primary/5 border border-primary/20 text-center space-y-4">
                        <AlertTriangle className="h-10 w-10 text-primary mx-auto opacity-80" />
                        <h2 className="text-2xl font-bold">Vulnerability Disclosure</h2>
                        <p className="text-muted-foreground max-w-2xl mx-auto">
                            We value the research community. If you believe you have found a security vulnerability in CareFlow, please report it to us immediately.
                        </p>
                        <Link href="mailto:security@careflow.com">
                            <Button variant="outline" className="mt-2 text-primary border-primary/20 hover:bg-primary/10">
                                Report a Vulnerability
                            </Button>
                        </Link>
                    </section>

                </div>
            </div>
        </div>
    );
}
