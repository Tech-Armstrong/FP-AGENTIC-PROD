import { NextResponse } from "next/server";
import { fetchFastApi } from "@/lib/fastapi-proxy";

export async function POST(req: Request) {
  let record_id = "";
  let education_targets: unknown[] | undefined;
  try {
    const body = await req.json();
    record_id = String(body?.record_id ?? "");
    education_targets = Array.isArray(body?.education_targets)
      ? body.education_targets
      : undefined;
  } catch {
    return NextResponse.json({ detail: "Invalid JSON body" }, { status: 400 });
  }
  if (!record_id) {
    return NextResponse.json(
      { detail: "record_id is required" },
      { status: 400 },
    );
  }
  const { ok, status, data } = await fetchFastApi("/financial-plan/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      record_id,
      ...(education_targets ? { education_targets } : {}),
    }),
  });
  return NextResponse.json(data, { status: ok ? 200 : status });
}
