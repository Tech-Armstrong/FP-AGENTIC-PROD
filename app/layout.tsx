import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { CopilotKit } from "@copilotkit/react-core";
import "@copilotkit/react-ui/styles.css";

/** When LANGGRAPH_AGENT_URL is set, chat goes through the LangGraph agent (see agent/main.py). */
const langGraphAgentId = process.env.LANGGRAPH_AGENT_URL
  ? (process.env.NEXT_PUBLIC_LANGGRAPH_AGENT_ID ?? "dashboard_agent")
  : undefined;

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Armstrong Capital — Client Dashboard",
  description:
    "Financial planning dashboard with AI-assisted client insights",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <CopilotKit
          runtimeUrl="/api/copilotkit"
          agent={langGraphAgentId}
          showDevConsole={false}
        >
          {children}
        </CopilotKit>
      </body>
    </html>
  );
}
