/**
 * Patient API Route
 * 
 * Protected API route for managing patients with full security implementation:
 * - Authentication required
 * - Rate limiting (20 req/min)
 * - Input validation with Zod
 * - Role-based authorization
 * - Hospital isolation (multi-tenancy)
 * - Audit logging
 */

import { NextRequest, NextResponse } from 'next/server';
import { getRatelimit } from '@/lib/rate-limit';
import { validateRequest, createPatientSchema } from '@/lib/api-validation';
import { auth } from '@/lib/auth';
import { validateCsrfToken } from '@/lib/csrf';

/**
 * GET /api/patients - List patients for the user's hospital
 */
export async function GET(request: NextRequest) {
  try {
    // 1. Authentication check
    const session = await auth();
    if (!session?.user) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    // 2. Rate limiting
    const clientIp = request.headers.get('x-forwarded-for')?.split(',')[0].trim() 
                   || request.headers.get('x-real-ip') 
                   || 'unknown';
    
    const ratelimit = getRatelimit('api');
    if (ratelimit) {
      const result = await ratelimit.limit(clientIp);
      if (!result.success) {
        const resetTime = result.reset instanceof Date ? result.reset : new Date(result.reset);
        const retryAfter = Math.ceil((resetTime.getTime() - Date.now()) / 1000);
        
        return NextResponse.json(
          { error: 'Too Many Requests', retryAfter },
          { 
            status: 429,
            headers: {
              'Retry-After': retryAfter.toString(),
              'X-RateLimit-Limit': result.limit.toString(),
              'X-RateLimit-Remaining': result.remaining.toString(),
              'X-RateLimit-Reset': resetTime.toISOString(),
            }
          }
        );
      }
    }

    // 3. Get query parameters
    const { searchParams } = new URL(request.url);
    const page = parseInt(searchParams.get('page') || '1', 10);
    const limit = Math.min(parseInt(searchParams.get('limit') || '20', 10), 100);

    // 4. Business logic - Fetch patients from Firestore
    const { getAdminDb } = await import('@/lib/firebase-admin');
    const db = await getAdminDb();
    
    const patientsRef = db.collection('patients')
      .where('hospitalId', '==', session.user.hospitalId)
      .limit(limit)
      .offset((page - 1) * limit);
    
    const snapshot = await patientsRef.get();
    const patients = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
    
    // Get total count for pagination
    const totalSnapshot = await db.collection('patients')
      .where('hospitalId', '==', session.user.hospitalId)
      .count()
      .get();
    const total = totalSnapshot.data().count;

    return NextResponse.json({
      data: patients,
      page,
      limit,
      total,
    });

  } catch (error) {
    console.error('Error fetching patients:', error);
    return NextResponse.json(
      { error: 'Internal Server Error' },
      { status: 500 }
    );
  }
}

/**
 * POST /api/patients - Create a new patient
 */
export async function POST(request: NextRequest) {
  try {
    // 1. Authentication check
    const session = await auth();
    if (!session?.user) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    // 2. CSRF protection
    const isValidCsrf = await validateCsrfToken(request);
    if (!isValidCsrf) {
      return NextResponse.json(
        { error: 'Invalid CSRF token' },
        { status: 403 }
      );
    }

    // 3. Rate limiting
    const clientIp = request.headers.get('x-forwarded-for')?.split(',')[0].trim() 
                   || request.headers.get('x-real-ip') 
                   || 'unknown';
    
    const ratelimit = getRatelimit('api');
    if (ratelimit) {
      const result = await ratelimit.limit(clientIp);
      if (!result.success) {
        const resetTime = result.reset instanceof Date ? result.reset : new Date(result.reset);
        const retryAfter = Math.ceil((resetTime.getTime() - Date.now()) / 1000);
        
        return NextResponse.json(
          { error: 'Too Many Requests', retryAfter },
          { status: 429, headers: { 'Retry-After': retryAfter.toString() } }
        );
      }
    }

    // 4. Input validation
    const body = await request.json();
    const validatedData = validateRequest(createPatientSchema, body);

    // 5. Authorization check - Only coordinators and admins can create patients
    if (session.user.role !== 'coordinator' && session.user.role !== 'admin') {
      return NextResponse.json(
        { error: 'Forbidden: Only coordinators and admins can create patients' },
        { status: 403 }
      );
    }

    // 6. Hospital isolation check
    if (validatedData.hospitalId !== session.user.hospitalId) {
      return NextResponse.json(
        { error: 'Forbidden: Cannot create patients for other hospitals' },
        { status: 403 }
      );
    }

    // 7. Business logic - Create patient in Firestore
    const { getAdminDb } = await import('@/lib/firebase-admin');
    const db = await getAdminDb();
    
    const patientRef = await db.collection('patients').add({
      ...validatedData,
      createdBy: session.user.id,
      createdAt: new Date().toISOString(),
    });

    // 8. Audit logging
    await db.collection('auditLogs').add({
      userId: session.user.id,
      action: 'CREATE_PATIENT',
      resource: 'patients',
      resourceId: patientRef.id,
      hospitalId: session.user.hospitalId,
      timestamp: new Date().toISOString(),
      ipAddress: clientIp,
    });

    return NextResponse.json(
      { 
        message: 'Patient created successfully',
        data: { id: patientRef.id }
      },
      { status: 201 }
    );

  } catch (error) {
    // Handle validation errors
    if (error && typeof error === 'object' && 'status' in error && error.status === 400) {
      const validationError = error as { status: number; message: string; errors: unknown };
      return NextResponse.json(
        { 
          error: validationError.message,
          details: validationError.errors 
        },
        { status: 400 }
      );
    }

    // Handle other errors
    console.error('Error creating patient:', error);
    return NextResponse.json(
      { error: 'Internal Server Error' },
      { status: 500 }
    );
  }
}
