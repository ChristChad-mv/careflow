/**
 * Global Error Boundary
 * 
 * Catches React errors and prevents application crashes from exposing
 * sensitive information in production.
 */

'use client';

import { useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { AlertTriangle } from 'lucide-react';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log error to monitoring service in production
    if (process.env.NODE_ENV === 'production') {
      // TODO: Send to error monitoring service (e.g., Sentry)
      console.error('Application error:', error.digest);
    } else {
      // Show full error in development
      console.error('Application error:', error);
    }
  }, [error]);

  return (
    <html>
      <body>
        <div className="min-h-screen flex items-center justify-center p-6 bg-background">
          <Card className="max-w-md w-full">
            <CardHeader>
              <div className="flex items-center gap-3">
                <AlertTriangle className="h-6 w-6 text-destructive" />
                <CardTitle>Something went wrong</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-muted-foreground">
                We apologize for the inconvenience. An unexpected error has occurred.
              </p>
              
              {process.env.NODE_ENV === 'development' && (
                <div className="bg-muted p-3 rounded-md text-sm font-mono">
                  {error.message}
                </div>
              )}
              
              <div className="flex gap-2">
                <Button onClick={reset} className="flex-1">
                  Try Again
                </Button>
                <Button
                  variant="outline"
                  onClick={() => window.location.href = '/dashboard'}
                  className="flex-1"
                >
                  Return Home
                </Button>
              </div>
              
              {error.digest && (
                <p className="text-xs text-muted-foreground text-center">
                  Error ID: {error.digest}
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      </body>
    </html>
  );
}
