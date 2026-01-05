/**
 * Server-side Authorization Helpers
 * 
 * Utilities to protect routes and check permissions in Server Components.
 */

import { redirect } from "next/navigation";
import { auth } from "@/lib/auth";
import { UserRole, hasPermission, Permission } from "@/types/auth";

/**
 * Get the current authenticated user or redirect to login
 * Use this in Server Components to require authentication
 */
export async function requireAuth() {
  const session = await auth();
  
  if (!session?.user) {
    redirect("/auth/login");
  }
  
  return session.user;
}

/**
 * Require authentication and specific role
 * Use this to protect routes that need specific roles
 */
export async function requireRole(allowedRoles: UserRole | UserRole[]) {
  const user = await requireAuth();
  const roles = Array.isArray(allowedRoles) ? allowedRoles : [allowedRoles];
  
  if (!roles.includes(user.role)) {
    redirect("/unauthorized");
  }
  
  return user;
}

/**
 * Check if current user has a specific permission
 */
export async function checkPermission(permission: Permission): Promise<boolean> {
  const session = await auth();
  
  if (!session?.user) {
    return false;
  }
  
  return hasPermission(session.user.role, permission);
}

/**
 * Require a specific permission or redirect
 */
export async function requirePermission(permission: Permission) {
  const user = await requireAuth();
  
  if (!hasPermission(user.role, permission)) {
    redirect("/unauthorized");
  }
  
  return user;
}

/**
 * Get current session (returns null if not authenticated)
 * Use this when you want to check auth but not require it
 */
export async function getSession() {
  return await auth();
}

/**
 * Check if user is authenticated
 */
export async function isAuthenticated(): Promise<boolean> {
  const session = await auth();
  return !!session?.user;
}
