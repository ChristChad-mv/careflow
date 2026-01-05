"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { updateUser } from "@/lib/actions";
import { useToast } from "@/hooks/use-toast";
import { User as UserIcon, Building, Shield, Loader2 } from "lucide-react";

interface UserData {
    name?: string | null;
    email?: string | null;
    role?: string | null;
    hospitalId?: string | null;
}

export function ProfileForm({ user }: { user: UserData }) {
    const [isLoading, setIsLoading] = useState(false);
    const { toast } = useToast();

    const handleSubmit = async (formData: FormData) => {
        setIsLoading(true);
        try {
            const result = await updateUser(formData);
            if (result.success) {
                toast({
                    title: "Profile Updated",
                    description: "Your profile information has been saved.",
                });
            } else {
                toast({
                    title: "Error",
                    description: result.error || "Failed to update profile.",
                    variant: "destructive",
                });
            }
        } catch (error) {
            toast({
                title: "Error",
                description: "An unexpected error occurred.",
                variant: "destructive",
            });
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <form action={handleSubmit}>
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
                                    name="hospitalId"
                                    defaultValue={user.hospitalId || ""}
                                    className="pl-9"
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
                <CardFooter className="flex justify-end">
                    <Button type="submit" disabled={isLoading}>
                        {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                        Save Changes
                    </Button>
                </CardFooter>
            </Card>
        </form>
    );
}
