import { NextRequest, NextResponse } from 'next/server';
import { getRatelimit } from '@/lib/rate-limit';
import { validateRequest, createAlertSchema, updateAlertSchema } from '@/lib/api-validation';
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
  updateDoc,
  doc as firestoreDoc,
  getDoc,
  orderBy
} from 'firebase/firestore';

/**
 * GET /api/alerts - List alerts for the user's hospital
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
            headers: { 'Retry-After': retryAfter.toString() }
          }
        );
      }
    }

    // 3. Get query parameters
    const { searchParams } = new URL(request.url);
    const status = searchParams.get('status'); // active, acknowledged, resolved
    const priority = searchParams.get('priority'); // low, medium, high, critical
    const limitCount = Math.min(parseInt(searchParams.get('limit') || '50', 10), 100);

    // 4. Business logic - Fetch alerts from Firestore
    const alertsRef = collection(db, 'alerts');
    let q = query(alertsRef, where('hospitalId', '==', session.user.hospitalId));

    if (status) q = query(q, where('status', '==', status));
    if (priority) q = query(q, where('priority', '==', priority));

    q = query(q, orderBy('triggeredAt', 'desc'), firestoreLimit(limitCount));

    const snapshot = await getDocs(q);
    const alerts = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));

    return NextResponse.json({
      data: alerts,
      filters: { status, priority },
      limit: limitCount,
      count: alerts.length,
    });

  } catch (error) {
    console.error('Error fetching alerts:', error);
    return NextResponse.json(
      { error: 'Internal Server Error' },
      { status: 500 }
    );
  }
}

/**
 * POST /api/alerts - Create a new alert
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
    const validatedData = validateRequest(createAlertSchema, body);

    // 5. Hospital isolation check
    if (validatedData.hospitalId !== session.user.hospitalId) {
      return NextResponse.json(
        { error: 'Forbidden: Cannot create alerts for other hospitals' },
        { status: 403 }
      );
    }

    // 6. Business logic - Create alert in Firestore
    const alertsRef = collection(db, 'alerts');
    const alertDoc = await addDoc(alertsRef, {
      ...validatedData,
      createdBy: session.user.id,
      triggeredAt: new Date().toISOString(),
      status: 'active',
    });

    // 7. Audit logging
    const auditRef = collection(db, 'audit_logs'); // Fixed collection name
    await addDoc(auditRef, {
      userId: session.user.id,
      action: 'CREATE_ALERT',
      resource: 'alerts',
      resourceId: alertDoc.id,
      hospitalId: session.user.hospitalId,
      timestamp: new Date().toISOString(),
      ipAddress: clientIp,
    });

    return NextResponse.json(
      {
        message: 'Alert created successfully',
        data: { id: alertDoc.id }
      },
      { status: 201 }
    );

  } catch (error) {
    // Handle validation errors
    if (error && typeof error === 'object' && 'status' in error && error.status === 400) {
      const validationError = error as { status: number; message: string; errors: unknown };
      return NextResponse.json(
        { error: validationError.message, details: validationError.errors },
        { status: 400 }
      );
    }

    console.error('Error creating alert:', error);
    return NextResponse.json(
      { error: 'Internal Server Error' },
      { status: 500 }
    );
  }
}

/**
 * PATCH /api/alerts - Update an alert (e.g., acknowledge, resolve)
 */
export async function PATCH(request: NextRequest) {
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
        return NextResponse.json(
          { error: 'Too Many Requests' },
          { status: 429 }
        );
      }
    }

    // 4. Input validation
    const body = await request.json();
    const { id: alertId, ...updateData } = body;

    if (!alertId || typeof alertId !== 'string') {
      return NextResponse.json(
        { error: 'Alert ID is required' },
        { status: 400 }
      );
    }

    const validatedData = validateRequest(updateAlertSchema, updateData);

    // 5. Verify alert exists and belongs to user's hospital
    const alertRef = firestoreDoc(db, 'alerts', alertId);
    const alertDoc = await getDoc(alertRef);

    if (!alertDoc.exists()) {
      return NextResponse.json({ error: 'Alert not found' }, { status: 404 });
    }

    const alertData = alertDoc.data();
    if (alertData?.hospitalId !== session.user.hospitalId) {
      return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
    }

    // 6. Business logic - Update alert
    await updateDoc(alertRef, {
      ...validatedData,
      updatedBy: session.user.id,
      updatedAt: new Date().toISOString(),
    });

    // 7. Audit logging - Log changes with validatedData
    const auditRef = collection(db, 'audit_logs');
    await addDoc(auditRef, {
      userId: session.user.id,
      action: 'UPDATE_ALERT',
      resource: 'alerts',
      resourceId: alertId,
      changes: validatedData,
      hospitalId: session.user.hospitalId,
      timestamp: new Date().toISOString(),
      ipAddress: clientIp,
    });

    return NextResponse.json({
      message: 'Alert updated successfully',
      id: alertId,
      updated: Object.keys(validatedData), // Show which fields were updated
    });

  } catch (error) {
    if (error && typeof error === 'object' && 'status' in error && error.status === 400) {
      const validationError = error as { status: number; message: string; errors: unknown };
      return NextResponse.json(
        { error: validationError.message, details: validationError.errors },
        { status: 400 }
      );
    }

    console.error('Error updating alert:', error);
    return NextResponse.json(
      { error: 'Internal Server Error' },
      { status: 500 }
    );
  }
}

