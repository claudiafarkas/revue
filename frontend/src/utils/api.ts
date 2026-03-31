export function getApiBaseUrl() {
  return process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8011/api';
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
