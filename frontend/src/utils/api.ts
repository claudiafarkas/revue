import { getStoredToken } from '../lib/auth';

export function getApiBaseUrl() {
  return process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8011/api';
}

export async function authenticatedApiFetch(path: string, init: RequestInit = {}) {
  const token = getStoredToken();
  if (!token) {
    throw new Error('Please sign in to continue.');
  }

  const timeoutMs = 20000;
  const controller = init.signal ? null : new AbortController();
  const timeoutId = controller ? window.setTimeout(() => controller.abort(), timeoutMs) : null;

  const headers = new Headers(init.headers);
  headers.set('Authorization', `Bearer ${token}`);

  try {
    const response = await fetch(`${getApiBaseUrl()}${path}`, {
      ...init,
      headers,
      signal: init.signal ?? controller?.signal,
    });
    return response;
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new Error('Request timed out. Please retry.');
    }
    throw error;
  } finally {
    if (timeoutId) {
      window.clearTimeout(timeoutId);
    }
  }
}

export async function readJsonResponse(response: Response): Promise<unknown> {
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    return null;
  }

  try {
    return await response.json();
  } catch {
    return null;
  }
}
