"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { signOutAction } from "@/lib/actions";
import { updateUserProfileClient } from "@/lib/client-actions";
import { useToast } from "@/hooks/use-toast";
import { User as UserIcon, Building, Shield, Loader2 } from "lucide-react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { UserContext } from "@/lib/db";

interface UserData {
    id?: string | null;
    name?: string | null;
    email?: string | null;
    role?: string | null;
    hospitalId?: string | null;
}

export function ProfileForm({ user }: { user: UserData }) {
    const [isLoading, setIsLoading] = useState(false);
    const { toast } = useToast();
    const { data: session } = useSession();
    const router = useRouter();

    const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();

        if (!session?.user?.id) {
            toast({
                title: "Error",
                description: "You are not authenticated.",
                variant: "destructive",
            });
            return;
        }

        setIsLoading(true);
        const formData = new FormData(e.currentTarget);
        const name = formData.get("name") as string;
        const hospitalId = formData.get("hospitalId") as string;

        try {
            const userContext: UserContext = {
                hospitalId: (session.user as any).hospitalId,
                role: (session.user as any).role,
                email: session.user.email || undefined
            };

            await updateUserProfileClient(session.user.id, { name, hospitalId }, userContext);

            toast({
                title: "Profile Updated",
                description: "Your profile information has been saved.",
            });
            router.refresh();
        } catch (error: any) {
            toast({
                title: "Error",
                description: error.message || "Failed to update profile.",
                variant: "destructive",
            });
        } finally {
            setIsLoading(false);
        }
    };

    const handleSignOut = async () => {
        await signOutAction();
    };

    return (
        <div className="space-y-6">
            <form onSubmit={handleSubmit}>
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <UserIcon className="h-5 w-5" />
                            Personal Information
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="flex items-center gap-4 p-4 bg-secondary/50 rounded-lg mb-6">
                            <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center">
                                <span className="text-2xl font-bold text-primary">
                                    {user.name?.charAt(0) || "U"}
                                </span>
                            </div>
                            <div>
                                <h3 className="font-semibold text-lg">{user.name}</h3>
                                <p className="text-sm text-muted-foreground">{user.role || "User"}</p>
                            </div>
                        </div>

                        <div className="grid gap-4 md:grid-cols-2">
                            <div className="space-y-2">
                                <Label htmlFor="name">Full Name</Label>
                                <Input
                                    id="name"
                                    name="name"
                                    defaultValue={user.name || ""}
                                    placeholder="Enter your full name"
                                    required
                                />
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="email">Email Address</Label>
                                <Input
                                    id="email"
                                    defaultValue={user.email || ""}
                                    disabled
                                    className="bg-muted"
                                />
                                <p className="text-xs text-muted-foreground">Email cannot be changed</p>
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="hospitalId">Hospital ID</Label>
                                <div className="relative">
                                    <Building className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                                    <Input
                                        id="hospitalId"
                                        defaultValue={user.hospitalId || ""}
                                        disabled
                                        className="pl-9 bg-muted"
                                        placeholder="HOSP..."
                                    />
                                </div>
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="role">Role</Label>
                                <div className="relative">
                                    <Shield className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                                    <Input
                                        id="role"
                                        defaultValue={user.role || ""}
                                        disabled
                                        className="pl-9 bg-muted capitalize"
                                    />
                                </div>
                            </div>
                        </div>
                    </CardContent>
                    <CardFooter className="flex justify-between">
                        <Button type="button" variant="destructive" onClick={handleSignOut}>
                            Sign Out
                        </Button>
                        <Button type="submit" disabled={isLoading}>
                            {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            Save Changes
                        </Button>
                    </CardFooter>
                </Card>
            </form>
        </div>
    );
}
