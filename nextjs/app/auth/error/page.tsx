/**
 * Error Page for Authentication Issues
 */

"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertCircle, HeartPulse } from "lucide-react";
import Link from "next/link";

const errorMessages: Record<string, { title: string; description: string }> = {
  Configuration: {
    title: "Server Configuration Error",
    description: "There is a problem with the server configuration. Please contact your system administrator.",
  },
  AccessDenied: {
    title: "Access Denied",
    description: "You do not have permission to access this resource. Please contact your administrator if you believe this is an error.",
  },
  Verification: {
    title: "Verification Failed",
    description: "The verification link is invalid or has expired. Please request a new one.",
  },
  Default: {
    title: "Authentication Error",
    description: "An error occurred during authentication. Please try again or contact support if the problem persists.",
  },
};

function ErrorContent() {
  const searchParams = useSearchParams();
  const error = searchParams.get("error") || "Default";
  
  const errorInfo = errorMessages[error] || errorMessages.Default;

  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-gradient-to-br from-background via-background to-primary/5">
      <div className="w-full max-w-md space-y-6">
        {/* Logo/Branding */}
        <div className="text-center space-y-2">
          <div className="flex justify-center">
            <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center">
              <HeartPulse className="h-8 w-8 text-primary" />
            </div>
          </div>
          <h1 className="text-3xl font-bold">CareFlow Pulse</h1>
        </div>

        {/* Error Card */}
        <Card>
          <CardHeader>
            <CardTitle>{errorInfo.title}</CardTitle>
            <CardDescription>Authentication Issue</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{errorInfo.description}</AlertDescription>
            </Alert>

            <div className="space-y-2">
              <Button asChild className="w-full">
                <Link href="/auth/login">Return to Login</Link>
              </Button>
              
              <Button asChild variant="outline" className="w-full">
                <Link href="/auth/register">Request New Account</Link>
              </Button>
            </div>

            {error === "AccessDenied" && (
              <p className="text-sm text-muted-foreground text-center">
                If you believe you should have access, please contact your system administrator
                with error code: <code className="text-xs">{error}</code>
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default function AuthErrorPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">Loading...</div>
      </div>
    }>
      <ErrorContent />
    </Suspense>
  );
}
