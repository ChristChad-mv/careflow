import { NextRequest, NextResponse } from 'next/server';
import { getRatelimit } from '@/lib/rate-limit';
import { validateRequest, createPatientSchema } from '@/lib/api-validation';
import { auth } from '@/lib/auth';
import { validateCsrfToken } from '@/lib/csrf';
import { db } from '@/lib/firebase';
import {
  collection,
  query,
  where,
  limit as firestoreLimit,
  getDocs,
  addDoc,
  getCountFromServer
} from 'firebase/firestore';

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
    const limitParams = Math.min(parseInt(searchParams.get('limit') || '20', 10), 100); // Renamed to avoid conflict with firestore limit

    // 4. Business logic - Fetch patients from Firestore
    const patientsRef = collection(db, 'patients');

    // Note: Firestore offset() is not available in lite/client SDK commonly used without deep pagination optimization 
    // or requires additional setup, but standard SDK supports limits. 
    // Implementing offset-like pagination or simple cursor-based is complex without cursors.
    // For now, fetching limit * page items and slicing is a safe fallback for small-scale, 
    // or we use firestoreLimit(limit * page) and slice in memory if strict "offset" is needed.
    // Given the previous code used offset(), we can try to emulate or just fetch enough.
    // Let's stick to simple limit for simplicity or emulated offset if needed.
    // The previous code: .limit(limit).offset((page - 1) * limit) works in Node Admin SDK.
    // Client SDK doesn't support .offset() directly in the same way query-building works easily without cursor.
    // We will use a basic query here.

    const q = query(
      patientsRef,
      where('hospitalId', '==', session.user.hospitalId),
      firestoreLimit(limitParams * page) // Get enough items up to current page
    );

    const snapshot = await getDocs(q);
    // Emulate offset/limit in memory for Client SDK (since real cursor pagination requires 'startAfter')
    const allDocs = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));
    const patients = allDocs.slice((page - 1) * limitParams, page * limitParams);

    // Get total count for pagination
    const totalQuery = query(patientsRef, where('hospitalId', '==', session.user.hospitalId));
    const totalSnapshot = await getCountFromServer(totalQuery);
    const total = totalSnapshot.data().count;

    return NextResponse.json({
      data: patients,
      page,
      limit: limitParams,
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
    const patientsRef = collection(db, 'patients');
    const patientDoc = await addDoc(patientsRef, {
      ...validatedData,
      createdBy: session.user.id,
      createdAt: new Date().toISOString(),
    });

    // 8. Audit logging
    const auditRef = collection(db, 'audit_logs'); // Fixed collection name to match AuditService
    await addDoc(auditRef, {
      userId: session.user.id,
      action: 'CREATE_PATIENT',
      resource: 'patients',
      resourceId: patientDoc.id,
      hospitalId: session.user.hospitalId,
      timestamp: new Date().toISOString(),
      ipAddress: clientIp,
    });

    return NextResponse.json(
      {
        message: 'Patient created successfully',
        data: { id: patientDoc.id }
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

