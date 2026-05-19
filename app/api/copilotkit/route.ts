import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  OpenAIAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { LangGraphHttpAgent } from "@copilotkit/runtime/langgraph";
import { createOpenAI } from "@ai-sdk/openai";
import { tavily } from "@tavily/core";
import type { LanguageModel } from "ai";
import { NextRequest } from "next/server";
import OpenAI from "openai";

/** Must match LangGraphAGUIAgent name in agent/main.py and layout.tsx */
export const LANGGRAPH_AGENT_ID = "dashboard_agent";

const langGraphAgentUrl = process.env.LANGGRAPH_AGENT_URL?.trim();
const useLangGraph = Boolean(langGraphAgentUrl);

function createAzureFetch(apiVersion: string): typeof fetch {
  return async (input, init) => {
    const url = new URL(
      typeof input === "string"
        ? input
        : input instanceof URL
          ? input.href
          : input.url,
    );
    if (!url.searchParams.has("api-version")) {
      url.searchParams.set("api-version", apiVersion);
    }
    return fetch(url, init);
  };
}

function createAzureOpenAIClient() {
  const apiKey = process.env.AZURE_API_KEY;
  const azureBase = process.env.AZURE_API_BASE?.replace(/\/$/, "");
  const deployment = process.env.AZURE_DEPLOYMENT_NAME ?? "gpt-4o";
  const apiVersion =
    process.env.AZURE_API_VERSION ?? "2024-08-01-preview";

  if (apiKey && azureBase) {
    return new OpenAI({
      apiKey,
      baseURL: `${azureBase}/openai/deployments/${deployment}`,
      defaultQuery: { "api-version": apiVersion },
      defaultHeaders: { "api-key": apiKey },
    });
  }

  return new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
}

function createAzureChatLanguageModel(): LanguageModel {
  const apiKey = process.env.AZURE_API_KEY!;
  const azureBase = process.env.AZURE_API_BASE!.replace(/\/$/, "");
  const deployment = process.env.AZURE_DEPLOYMENT_NAME ?? "gpt-4o";
  const apiVersion =
    process.env.AZURE_API_VERSION ?? "2024-08-01-preview";

  const provider = createOpenAI({
    apiKey,
    baseURL: `${azureBase}/openai/deployments/${deployment}`,
    headers: { "api-key": apiKey },
    fetch: createAzureFetch(apiVersion),
  });

  return provider.chat(deployment);
}

function createDirectLlmRuntime() {
  const deployment = process.env.AZURE_DEPLOYMENT_NAME ?? "gpt-4o";
  const openai = createAzureOpenAIClient();
  const serviceAdapter = new OpenAIAdapter({
    openai,
    model: deployment,
  });

  if (process.env.AZURE_API_KEY && process.env.AZURE_API_BASE) {
    serviceAdapter.getLanguageModel = () => createAzureChatLanguageModel();
  }

  const runtime = new CopilotRuntime({
    actions: () => [
      {
        name: "searchInternet",
        description: "Searches the internet for information.",
        parameters: [
          {
            name: "query",
            type: "string",
            description: "The query to search the internet for.",
            required: true,
          },
        ],
        handler: async ({ query }: { query: string }) => {
          const tvly = tavily({ apiKey: process.env.TAVILY_API_KEY });
          return await tvly.search(query, { max_results: 5 });
        },
      },
    ],
  });

  return { runtime, serviceAdapter };
}

function createLangGraphRuntime() {
  const serviceAdapter = new ExperimentalEmptyAdapter();
  const runtime = new CopilotRuntime({
    agents: {
      [LANGGRAPH_AGENT_ID]: new LangGraphHttpAgent({
        url: langGraphAgentUrl!,
      }),
    },
  });
  return { runtime, serviceAdapter };
}

const { runtime, serviceAdapter } = useLangGraph
  ? createLangGraphRuntime()
  : createDirectLlmRuntime();

if (useLangGraph) {
  console.log("[copilotkit] mode=LangGraph", {
    url: langGraphAgentUrl,
    agentId: LANGGRAPH_AGENT_ID,
  });
} else {
  console.log("[copilotkit] mode=direct Azure (LANGGRAPH_AGENT_URL unset)");
}

const copilotEndpoint = copilotRuntimeNextJSAppRouterEndpoint({
  runtime,
  serviceAdapter,
  endpoint: "/api/copilotkit",
});

/** Runtime info for smoke tests (curl GET /api/copilotkit). */
export async function GET() {
  return Response.json({
    mode: useLangGraph ? "LangGraph" : "direct Azure",
    agents: useLangGraph ? [LANGGRAPH_AGENT_ID] : [],
    langGraphAgentUrl: useLangGraph ? langGraphAgentUrl : undefined,
  });
}

export const POST = async (req: NextRequest) => {
  return copilotEndpoint.handleRequest(req);
};
