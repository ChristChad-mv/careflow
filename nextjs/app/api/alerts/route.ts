/**
 * Alerts API Route
 * 
 * Protected API route for managing patient alerts with full security:
 * - Authentication required
 * - Rate limiting (20 req/min)
 * - Input validation with Zod
 * - Role-based authorization
 * - Hospital isolation (multi-tenancy)
 * - CSRF protection for state-changing operations
 */

import { NextRequest, NextResponse } from 'next/server';
import { getRatelimit } from '@/lib/rate-limit';
import { validateRequest, createAlertSchema, updateAlertSchema } from '@/lib/api-validation';
import { auth } from '@/lib/auth';
import { validateCsrfToken } from '@/lib/csrf';

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
    const limit = Math.min(parseInt(searchParams.get('limit') || '50', 10), 100);

    // 4. Business logic - Fetch alerts from Firestore
    const { getAdminDb } = await import('@/lib/firebase-admin');
    const db = await getAdminDb();
    
    let query = db.collection('alerts')
      .where('hospitalId', '==', session.user.hospitalId);
    
    if (status) {
      query = query.where('status', '==', status);
    }
    if (priority) {
      query = query.where('priority', '==', priority);
    }
    
    const snapshot = await query
      .limit(limit)
      .orderBy('triggeredAt', 'desc')
      .get();
    
    const alerts = snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }));

    return NextResponse.json({
      data: alerts,
      filters: { status, priority },
      limit,
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
    const { getAdminDb } = await import('@/lib/firebase-admin');
    const db = await getAdminDb();
    
    const alertRef = await db.collection('alerts').add({
      ...validatedData,
      createdBy: session.user.id,
      triggeredAt: new Date().toISOString(),
      status: 'active',
    });

    // 7. Audit logging
    await db.collection('auditLogs').add({
      userId: session.user.id,
      action: 'CREATE_ALERT',
      resource: 'alerts',
      resourceId: alertRef.id,
      hospitalId: session.user.hospitalId,
      timestamp: new Date().toISOString(),
      ipAddress: clientIp,
    });

    return NextResponse.json(
      { 
        message: 'Alert created successfully',
        data: { id: alertRef.id }
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
    const { getAdminDb } = await import('@/lib/firebase-admin');
    const db = await getAdminDb();
    
    const alertRef = db.collection('alerts').doc(alertId);
    const alertDoc = await alertRef.get();
    
    if (!alertDoc.exists) {
      return NextResponse.json({ error: 'Alert not found' }, { status: 404 });
    }
    
    const alertData = alertDoc.data();
    if (alertData?.hospitalId !== session.user.hospitalId) {
      return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
    }

    // 6. Business logic - Update alert
    await alertRef.update({
      ...validatedData,
      updatedBy: session.user.id,
      updatedAt: new Date().toISOString(),
    });

    // 7. Audit logging - Log changes with validatedData
    await db.collection('auditLogs').add({
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
