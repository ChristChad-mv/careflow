/**
 * Authentication and Authorization Type Definitions
 * 
 * Defines user roles, permissions, and related types for hospital staff.
 */

export type UserRole = "nurse" | "coordinator" | "admin";

export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  name: string; // Full name
  role: UserRole;
  department?: string;
  hospitalId: string;
  employeeId: string;
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
}

export interface AuthUser {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  department?: string;
  hospitalId?: string;
}

// Permission levels for different roles
export const RolePermissions = {
  nurse: {
    canViewAssignedPatients: true,
    canViewAllPatients: false,
    canEditPatients: false,
    canViewAlerts: true,
    canDismissAlerts: false,
    canManageUsers: false,
    canAccessReports: false,
    canConfigureSystem: false,
  },
  coordinator: {
    canViewAssignedPatients: true,
    canViewAllPatients: true,
    canEditPatients: true,
    canViewAlerts: true,
    canDismissAlerts: true,
    canManageUsers: false,
    canAccessReports: true,
    canConfigureSystem: false,
  },
  admin: {
    canViewAssignedPatients: true,
    canViewAllPatients: true,
    canEditPatients: true,
    canViewAlerts: true,
    canDismissAlerts: true,
    canManageUsers: true,
    canAccessReports: true,
    canConfigureSystem: true,
  },
} as const;

export type Permission = keyof typeof RolePermissions.admin;

// Helper function to check if a user has a specific permission
export function hasPermission(role: UserRole, permission: Permission): boolean {
  return RolePermissions[role][permission];
}

// Helper function to check if user can access a patient
export function canAccessPatient(
  userRole: UserRole,
  userId: string,
  patientAssignedNurseId?: string
): boolean {
  // Admins and coordinators can access all patients
  if (userRole === "admin" || userRole === "coordinator") {
    return true;
  }

  // Nurses can only access their assigned patients
  if (userRole === "nurse") {
    return userId === patientAssignedNurseId;
  }

  return false;
}

// Registration request types
export interface RegistrationRequest {
  firstName: string;
  lastName: string;
  email: string;
  password: string;
  role: UserRole;
  department: string;
  employeeId: string;
  hospitalId: string;
}

export interface RegistrationRequestWithStatus extends RegistrationRequest {
  id: string;
  status: "pending" | "approved" | "rejected";
  requestedAt: Date;
  reviewedAt?: Date;
  reviewedBy?: string;
  notes?: string;
}
