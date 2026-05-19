import { NextResponse } from "next/server";

const FASTAPI_BASE = process.env.FASTAPI_BASE_URL ?? "http://localhost:8001";

export async function GET() {
  try {
    const res = await fetch(`${FASTAPI_BASE}/clients`, { cache: "no-store" });
    if (!res.ok) {
      return NextResponse.json(
        { error: `FastAPI error: ${res.status}` },
        { status: res.status }
      );
    }
    const data = await res.json();
    return NextResponse.json(data);
  } catch (err) {
    return NextResponse.json(
      { error: `Could not reach FastAPI: ${(err as Error).message}` },
      { status: 502 }
    );
  }
}
