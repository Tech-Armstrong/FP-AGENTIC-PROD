"use client";

import { CopilotSidebar } from "@copilotkit/react-ui";
import { ClientsDashboard } from "../components/ClientsDashboard";
import { Header } from "../components/Header";
import { Footer } from "../components/Footer";
import { CustomAssistantMessage } from "../components/AssistantMessage";
import { prompt } from "../lib/prompt";
import { PolicyDocumentHitl } from "../components/PolicyDocumentHitl";
import { ChartTools } from "../components/ChartTools";

import { Suspense } from "react";

function HomeContent() {
  return (
    <>
      <PolicyDocumentHitl />
      <ChartTools />
      <CopilotSidebar
        defaultOpen
        instructions={prompt}
        AssistantMessage={CustomAssistantMessage}
        labels={{
          title: "FP Assistant",
          initial:
            "Hello, I'm here to help you understand your data. How can I help?",
          placeholder: "Ask any questions about client's data..",
        }}
      >
        <div className="min-h-screen bg-gray-50 flex flex-col dark:bg-gray-950">
          <Header />
          <main className="w-full max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8 flex-grow">
            <ClientsDashboard />
          </main>
          <Footer />
        </div>
      </CopilotSidebar>
    </>
  );
}

export default function Home() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        </div>
      }
    >
      <HomeContent />
    </Suspense>
  );
}
