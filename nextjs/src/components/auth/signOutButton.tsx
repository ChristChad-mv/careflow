"use client";

import { Button } from "@/components/ui/button";
import { LogOut } from "lucide-react";
import { signOut } from "next-auth/react";
import { auth } from "@/lib/firebase";
import { signOut as firebaseSignOut } from "firebase/auth";

export function SignOutButton() {
    const handleLogout = async () => {
        try {
            // Sign out from Firebase
            await firebaseSignOut(auth);

            // Sign out from NextAuth and redirect to login
            await signOut({ callbackUrl: "/auth/login" });
        } catch (error) {
            console.error("Error signing out:", error);
        }
    };

    return (
        <Button
            variant="ghost"
            size="sm"
            onClick={handleLogout}
            className="text-muted-foreground hover:text-destructive"
        >
            <LogOut className="h-4 w-4 mr-2" />
            Sign Out
        </Button>
    );
}
