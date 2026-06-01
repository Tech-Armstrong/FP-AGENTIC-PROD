import { NextResponse } from "next/server";
import { fetchFastApi } from "@/lib/fastapi-proxy";

export async function POST(req: Request) {
  let body: {
    record_id?: string;
    education_targets?: unknown[];
    overrides?: unknown;
  } = {};
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ detail: "Invalid JSON body" }, { status: 400 });
  }
  const record_id = String(body?.record_id ?? "");
  if (!record_id) {
    return NextResponse.json(
      { detail: "record_id is required" },
      { status: 400 },
    );
  }
  const education_targets = Array.isArray(body?.education_targets)
    ? body.education_targets
    : undefined;
  const { ok, status, data } = await fetchFastApi("/financial-plan/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      record_id,
      ...(education_targets ? { education_targets } : {}),
      ...(body.overrides ? { overrides: body.overrides } : {}),
    }),
  });
  return NextResponse.json(data, { status: ok ? 200 : status });
}
