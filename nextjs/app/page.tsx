"use client";

import Link from "next/link";
import Image from "next/image";
import {
  ArrowRight,
  ShieldCheck,
  Activity,
  PhoneCall,
  BrainCircuit,
  Lock,
  Database,
  HeartPulse,
  ChevronRight,
  Users,
  Clock,
  CheckCircle2,
  Sparkles,
  ClipboardCheck,
  Zap,
  LayoutDashboard
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ThemeToggle } from "@/components/ThemeToggle";

export default function Home() {
  return (
    <div className="min-h-screen bg-background selection:bg-primary/20">
      {/* Navigation */}
      <nav className="fixed top-0 w-full z-50 border-b border-white/5 bg-background/60 backdrop-blur-xl">
        <div className="container mx-auto px-6 h-20 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="relative h-10 w-10 bg-primary rounded-xl flex items-center justify-center shadow-lg shadow-primary/20">
              <HeartPulse className="h-6 w-6 text-white" />
            </div>
            <span className="text-2xl font-bold tracking-tight text-gradient">CareFlow</span>
          </div>

          <div className="hidden md:flex items-center gap-8 text-sm font-medium text-muted-foreground">
            <Link href="#how-it-works" className="hover:text-primary transition-colors">How it Works</Link>
            <Link href="#solutions" className="hover:text-primary transition-colors">Solutions</Link>
            <Link href="#security" className="hover:text-primary transition-colors">Security</Link>
          </div>

          <div className="flex items-center gap-4">
            <ThemeToggle />
            <Link href="/dashboard">
              <Button className="hidden md:flex rounded-full px-6 bg-primary hover:bg-primary/90 shadow-lg shadow-primary/20">
                Experience CareFlow <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-32 pb-20 md:pt-48 md:pb-32 overflow-hidden">
        <div className="absolute top-0 right-0 -z-10 w-[500px] h-[500px] bg-primary/10 rounded-full blur-[120px] translate-x-1/2 -translate-y-1/2" />
        <div className="absolute bottom-0 left-0 -z-10 w-[500px] h-[500px] bg-teal-500/10 rounded-full blur-[120px] -translate-x-1/2 translate-y-1/2" />

        <div className="container mx-auto px-6">
          <div className="max-w-4xl mx-auto text-center space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-1000">
            <Badge variant="outline" className="px-4 py-1.5 rounded-full border-primary/20 bg-primary/5 text-primary">
              <Sparkles className="h-3.5 w-3.5 mr-2" />
              Revolutionizing Post-Discharge Patient Safety
            </Badge>

            <h1 className="text-3xl md:text-7xl font-extrabold tracking-tight leading-[1.1]">
              The Intelligent Pulse of <br />
              <span className="text-gradient">Post-Hospital Care</span>
            </h1>

            <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed px-4">
              Automated clinical follow-up that thinks, speaks, and acts like your best nurse coordinator. Reduce readmissions through AI-driven proactive monitoring.
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4 px-4">
              <Link href="/dashboard">
                <Button size="lg" className="min-w-[200px] rounded-full px-8 h-14 text-lg font-semibold bg-primary hover:bg-primary/90 shadow-xl shadow-primary/20">
                  Explore the Platform <ChevronRight className="ml-2 h-5 w-5" />
                </Button>
              </Link>
              <Button size="lg" variant="outline" className="min-w-[200px] rounded-full px-8 h-14 text-lg font-semibold glass border-white/10 hover:bg-white/5 transition-all">
                Request a Clinical BAA
              </Button>
            </div>

            <div className="pt-8 flex items-center justify-center gap-8 opacity-60 grayscale hover:grayscale-0 transition-all duration-500 overflow-x-auto pb-4 px-4 scrollbar-hide">
              {/* Simulating "Trusted By" or "Built With" */}
              <div className="flex items-center gap-2 flex-shrink-0">
                <ShieldCheck className="h-5 w-5" />
                <span className="text-xs font-bold uppercase tracking-widest">HIPAA Compliant</span>
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                <BrainCircuit className="h-5 w-5" />
                <span className="text-xs font-bold uppercase tracking-widest">Gemini 3 Med-Logic</span>
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                <Activity className="h-5 w-5" />
                <span className="text-xs font-bold uppercase tracking-widest">Real-time Tracing</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* AI in Action - The "Magic" Section */}
      <section className="py-24 bg-secondary/20 relative">
        <div className="container mx-auto px-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
            <div className="space-y-8">
              <Badge className="bg-primary/10 text-primary border-primary/20">AI in Action</Badge>
              <h2 className="text-3xl md:text-4xl font-bold tracking-tight">The 24/7 Safety Net for Your Patients</h2>
              <p className="text-lg text-muted-foreground leading-relaxed">
                CareFlow extends your clinical reach beyond the hospital walls, acting as an automated extension of your nursing team.
              </p>

              <div className="space-y-6">
                <div className="flex flex-col sm:flex-row gap-4 p-4 rounded-2xl bg-white/5 border border-white/10 hover:bg-white/10 transition-colors group">
                  <div className="h-12 w-12 rounded-xl bg-blue-500/20 text-blue-400 flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform">
                    <PhoneCall className="h-6 w-6" />
                  </div>
                  <div>
                    <h4 className="font-bold">Automated Clinical Outreach</h4>
                    <p className="text-sm text-muted-foreground">Our system proactively calls patients to check on their recovery, asking the right questions just like a nurse would—ensuring no patient is left monitoring themselves.</p>
                  </div>
                </div>
                <div className="flex flex-col sm:flex-row gap-4 p-4 rounded-2xl bg-white/5 border border-white/10 hover:bg-white/10 transition-colors group">
                  <div className="h-12 w-12 rounded-xl bg-primary/20 text-primary flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform">
                    <ShieldCheck className="h-6 w-6" />
                  </div>
                  <div>
                    <h4 className="font-bold">Instant Risk Detection</h4>
                    <p className="text-sm text-muted-foreground">We instantly analyze patient responses for deterioration signs. If a risk is detected, your team is alerted immediately. If not, the patient rests easy. Peace of mind, automated.</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="relative">
              {/* Simulated Conversation Mockup */}
              <div className="glass rounded-3xl border border-white/10 shadow-2xl p-6 md:p-10 space-y-6 max-w-lg mx-auto transform hover:rotate-1 transition-transform duration-500">
                <div className="flex items-center gap-4 border-b border-white/5 pb-4">
                  <div className="h-3 w-3 rounded-full bg-red-500 animate-pulse" />
                  <p className="text-xs font-bold uppercase tracking-widest opacity-60">Live Call Interaction</p>
                </div>

                <div className="space-y-4">
                  <div className="flex gap-3 items-start">
                    <div className="h-8 w-8 rounded-full bg-blue-500/20 flex items-center justify-center flex-shrink-0 mt-1">
                      <PhoneCall className="h-4 w-4 text-blue-400" />
                    </div>
                    <div className="flex-1 p-3 rounded-2xl rounded-tl-none bg-blue-500/10 border border-blue-500/20">
                      <p className="text-sm italic">"Hello Mr. Thompson, I'm checking in on your recovery. How have you been feeling since your discharge?"</p>
                    </div>
                  </div>

                  <div className="flex gap-3 justify-end items-start text-right">
                    <div className="flex-1 p-3 rounded-2xl rounded-tr-none bg-white/5 border border-white/10">
                      <p className="text-sm">"I was okay this morning, but I'm feeling a bit short of breath now that I'm up and moving."</p>
                    </div>
                    <div className="h-8 w-8 rounded-full bg-white/10 flex items-center justify-center flex-shrink-0 mt-1">
                      <Users className="h-4 w-4 text-white/40" />
                    </div>
                  </div>

                  <div className="flex gap-3 items-start">
                    <div className="h-8 w-8 rounded-full bg-primary/20 flex items-center justify-center flex-shrink-0 mt-1">
                      <Sparkles className="h-4 w-4 text-primary" />
                    </div>
                    <div className="flex-1 p-3 rounded-2xl rounded-tl-none bg-primary/10 border border-primary/20">
                      <p className="text-sm font-medium">Processing clinical risk... Detection: Potential Pulmonary Complication. Action: High-Severity Triage.</p>
                    </div>
                  </div>
                </div>

                <div className="pt-4 mt-6 border-t border-white/5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-muted-foreground">Google Model Armor</span>
                    <span className="text-success flex items-center gap-1 font-bold">
                      <ShieldCheck className="h-3 w-3" /> PHI SECURED
                    </span>
                  </div>
                </div>
              </div>

              {/* Floating Stats Badge */}
              <div className="absolute -bottom-6 -right-6 glass rounded-2xl p-4 border border-white/10 shadow-xl hidden md:block animate-bounce-subtle">
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-full bg-success/20 flex items-center justify-center">
                    <Clock className="h-5 w-5 text-success" />
                  </div>
                  <div>
                    <p className="text-xs font-bold">Response Time</p>
                    <p className="text-lg font-extrabold text-success">~450ms</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* How it Works - The Journey */}
      <section id="how-it-works" className="py-24">
        <div className="container mx-auto px-6">
          <div className="text-center max-w-3xl mx-auto mb-20 space-y-4">
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight">The 360° Continuity Loop</h2>
            <p className="text-lg text-muted-foreground">From discharge to full recovery, CareFlow covers every critical touchpoint.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 md:gap-4 relative">
            {/* Connecting Line (Desktop) */}
            <div className="hidden md:block absolute top-[60px] left-0 w-full h-[2px] bg-gradient-to-r from-transparent via-primary/30 to-transparent -z-10" />

            {[
              {
                step: "01",
                icon: ClipboardCheck,
                title: "Discharge Sync",
                desc: "Patient recovery plan is synced from EHR/Firestore directly into CareFlow Pulse."
              },
              {
                step: "02",
                icon: Zap,
                title: "Proactive Engagement",
                desc: "Caller Agent initiates natural voice follow-ups at clinically relevant intervals."
              },
              {
                step: "03",
                icon: BrainCircuit,
                title: "Intelligent Triage",
                desc: "Pulse Agent analyzes symptoms and adherence to calculate real-time risk scores."
              },
              {
                step: "04",
                icon: LayoutDashboard,
                title: "Nurse Intervention",
                desc: "Critical alerts are instantly triaged to nursing staff for immediate clinical action."
              }
            ].map((item, i) => (
              <div key={i} className="relative group text-center px-4">
                <div className="h-16 w-16 mx-auto rounded-full glass border border-white/10 bg-background flex items-center justify-center mb-6 group-hover:border-primary group-hover:scale-110 transition-all duration-300">
                  <item.icon className="h-8 w-8 text-primary" />
                </div>
                <div className="bg-primary/10 text-primary text-[10px] font-bold w-12 mx-auto rounded-full py-0.5 mb-4 group-hover:bg-primary group-hover:text-white transition-colors uppercase tracking-widest">
                  Step {item.step}
                </div>
                <h4 className="font-bold text-lg mb-2">{item.title}</h4>
                <p className="text-sm text-muted-foreground leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Trust & Security Section */}
      <section id="security" className="py-24 bg-gradient-to-b from-transparent to-secondary/30 relative">
        <div className="container mx-auto px-4 md:px-10">
          <div className="glass rounded-[40px] p-8 md:p-16 border border-white/10 shadow-2xl relative overflow-hidden">
            {/* Abstract Security Graphic */}
            <div className="absolute top-0 right-0 h-full w-1/3 opacity-5 pointer-events-none">
              <ShieldCheck className="w-full h-full scale-110 rotate-12" />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center relative z-10">
              <div className="space-y-8">
                <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-teal-500/10 text-teal-400 border border-teal-500/20 text-xs font-bold uppercase tracking-widest">
                  <Lock className="h-3 w-3" /> HIPAA Compliant Infrastructure
                </div>
                <h2 className="text-3xl md:text-5xl font-bold tracking-tight leading-tight">Patient Safety is <br /><span className="text-gradient">Our Baseline.</span></h2>
                <p className="text-lg text-muted-foreground leading-relaxed">
                  We've built CareFlow on Google Cloud's most advanced security framework. Our dual-agent architecture ensures zero-trust handling of every byte of patient data.
                </p>

                <ul className="space-y-4">
                  {[
                    { title: "Google Model Armor", desc: "Real-time PII/PHI redaction and response filtering." },
                    { title: "E2E Encryption", desc: "Data is encrypted at rest and in transit via HTTPS/TLS 1.3." },
                    { title: "Clinical Sovereignty", desc: "We never train public models on your private hospital data." }
                  ].map((item, i) => (
                    <li key={i} className="flex gap-4">
                      <CheckCircle2 className="h-6 w-6 text-primary flex-shrink-0" />
                      <div>
                        <p className="font-bold">{item.title}</p>
                        <p className="text-sm text-muted-foreground">{item.desc}</p>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-4 pt-0 sm:pt-12">
                  <Card className="glass border-none shadow-none p-6 text-center">
                    <Activity className="h-8 w-8 text-primary mx-auto mb-4" />
                    <p className="text-2xl font-bold">100%</p>
                    <p className="text-[10px] text-muted-foreground uppercase font-bold tracking-widest">Traceable Actions</p>
                  </Card>
                  <Card className="glass border-none shadow-none p-6 text-center">
                    <Database className="h-8 w-8 text-teal-400 mx-auto mb-4" />
                    <p className="text-2xl font-bold">Firestore</p>
                    <p className="text-[10px] text-muted-foreground uppercase font-bold tracking-widest">Secure Sync</p>
                  </Card>
                </div>
                <div className="space-y-4">
                  <Card className="glass border-none shadow-none p-6 text-center bg-primary/10">
                    <ShieldCheck className="h-8 w-8 text-primary mx-auto mb-4" />
                    <p className="text-2xl font-bold">SOC2</p>
                    <p className="text-[10px] text-muted-foreground uppercase font-bold tracking-widest">Type II Compliant</p>
                  </Card>
                  <Card className="glass border-none shadow-none p-6 text-center">
                    <Users className="h-8 w-8 text-blue-400 mx-auto mb-4" />
                    <p className="text-2xl font-bold">99.9%</p>
                    <p className="text-[10px] text-muted-foreground uppercase font-bold tracking-widest">System Honesty</p>
                  </Card>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24">
        <div className="container mx-auto px-6">
          <div className="glass rounded-[40px] p-8 md:p-20 text-center relative overflow-hidden bg-gradient-to-br from-primary/20 to-teal-500/20">
            <div className="relative z-10 max-w-2xl mx-auto space-y-8">
              <h2 className="text-3xl md:text-6xl font-extrabold tracking-tight">Evolve your patient <br /> outcomes today.</h2>
              <p className="text-lg text-muted-foreground leading-relaxed">
                Experience the future of healthcare monitoring. Secure, intelligent, and built for startup-speed innovation in MedTech.
              </p>
              <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                <Link href="/dashboard" className="w-full sm:w-auto">
                  <Button size="lg" className="w-full sm:w-auto rounded-full px-12 h-16 text-xl font-bold bg-primary hover:bg-primary/90 shadow-2xl shadow-primary/30">
                    Get Started Free
                  </Button>
                </Link>
                <Button size="lg" variant="ghost" className="w-full sm:w-auto rounded-full px-12 h-16 text-xl font-bold hover:bg-white/5">
                  Download Spec Sheet
                </Button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 border-t border-white/5">
        <div className="container mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-8">
          <div className="flex items-center gap-3">
            <HeartPulse className="h-6 w-6 text-primary" />
            <span className="text-xl font-bold tracking-tight">CareFlow</span>
          </div>
          <div className="flex flex-col md:flex-row items-center gap-4 md:gap-12 text-sm text-muted-foreground font-medium text-center md:text-left">
            <Link href="/privacy-policy" className="hover:text-primary transition-colors">Privacy Policy</Link>
            <Link href="/hipaa-compliance" className="hover:text-primary transition-colors">HIPAA Compliance BAA</Link>
            <Link href="/security" className="hover:text-primary transition-colors">Security Docs</Link>
          </div>
          <div className="flex items-center gap-4">
            <Image src="/logo.png" alt="Google Cloud Partner" width={100} height={40} className="opacity-40 grayscale" />
          </div>
        </div>
        <div className="container mx-auto px-6 mt-12 text-center text-[10px] text-muted-foreground/30 tracking-[0.3em] uppercase font-bold">
          © 2026 CareFlow Medical Systems. Empowered by Gemini 3 Logic Engines.
        </div>
      </footer>
    </div>
  );
}
