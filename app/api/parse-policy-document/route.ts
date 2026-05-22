import { NextResponse } from "next/server";

const AGENT_BASE =
  process.env.LANGGRAPH_AGENT_URL?.replace(/\/copilotkit\/?$/, "") ||
  "http://localhost:8000";

export async function POST(req: Request) {
  let body: Record<string, unknown>;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ detail: "Invalid JSON body" }, { status: 400 });
  }

  try {
    const res = await fetch(`${AGENT_BASE}/parse-policy-document`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      cache: "no-store",
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.ok ? 200 : res.status });
  } catch (err) {
    return NextResponse.json(
      {
        detail: `Could not reach agent parser: ${(err as Error).message}`,
      },
      { status: 502 },
    );
  }
}
