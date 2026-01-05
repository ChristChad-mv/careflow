/**
 * API Route Example with Rate Limiting and Input Validation
 * 
 * This example shows how to use rate limiting and input validation
 * in your API routes.
 */

import { NextRequest, NextResponse } from 'next/server';
import { getRatelimit } from '@/lib/rate-limit';
import { validateRequest, createPatientSchema } from '@/lib/api-validation';
import { auth } from '@/lib/auth';

// Example: POST /api/patients - Create a new patient
export async function POST(request: NextRequest) {
  try {
    // 1. Check authentication
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
          { 
            error: 'Too Many Requests',
            retryAfter
          },
          { 
            status: 429,
            headers: {
              'Retry-After': retryAfter.toString()
            }
          }
        );
      }
    }

    // 3. Parse and validate input
    const body = await request.json();
    const validatedData = validateRequest(createPatientSchema, body);

    // 4. Authorization check (role-based)
    if (session.user.role !== 'coordinator' && session.user.role !== 'admin') {
      return NextResponse.json(
        { error: 'Forbidden: Only coordinators and admins can create patients' },
        { status: 403 }
      );
    }

    // 5. Hospital isolation check
    if (validatedData.hospitalId !== session.user.hospitalId) {
      return NextResponse.json(
        { error: 'Forbidden: Cannot create patients for other hospitals' },
        { status: 403 }
      );
    }

    // 6. Business logic - Create patient in Firestore
    // const patientRef = await db.collection('patients').add({
    //   ...validatedData,
    //   createdBy: session.user.id,
    //   createdAt: new Date().toISOString(),
    // });

    // 7. Create audit log
    // await db.collection('auditLogs').add({
    //   userId: session.user.id,
    //   action: 'CREATE_PATIENT',
    //   resource: 'patients',
    //   resourceId: patientRef.id,
    //   hospitalId: session.user.hospitalId,
    //   timestamp: new Date().toISOString(),
    //   ipAddress: clientIp,
    // });

    return NextResponse.json(
      { 
        message: 'Patient created successfully',
        // data: { id: patientRef.id }
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

// Example: GET /api/patients - List patients
export async function GET(request: NextRequest) {
  try {
    // 1. Check authentication
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
        return NextResponse.json(
          { error: 'Too Many Requests' },
          { status: 429 }
        );
      }
    }

    // 3. Get query parameters
    const { searchParams } = new URL(request.url);
    const page = parseInt(searchParams.get('page') || '1');
    const limit = Math.min(parseInt(searchParams.get('limit') || '20'), 100); // Max 100
    // const status = searchParams.get('status'); // For future filtering

    // 4. Fetch patients from Firestore (filtered by hospital)
    // const patientsRef = db.collection('patients')
    //   .where('hospitalId', '==', session.user.hospitalId);
    //
    // if (_status) {
    //   patientsRef = patientsRef.where('status', '==', _status);
    // }
    //
    // const snapshot = await patientsRef
    //   .limit(limit)
    //   .offset((page - 1) * limit)
    //   .get();
    //
    // const patients = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));

    return NextResponse.json({
      // data: patients,
      page,
      limit,
      // total: patients.length,
    });

  } catch (error) {
    console.error('Error fetching patients:', error);
    return NextResponse.json(
      { error: 'Internal Server Error' },
      { status: 500 }
    );
  }
}
