/**
 * CSP reports can contain full document URLs. Deliberately discard the body so
 * sensitive paths and query strings never enter application logs or storage.
 */
export async function POST(request: Request) {
  await request.body?.cancel();
  return new Response(null, { status: 204 });
}
