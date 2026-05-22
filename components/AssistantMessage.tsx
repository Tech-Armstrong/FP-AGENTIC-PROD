import { AssistantMessageProps } from "@copilotkit/react-ui";
import { Loader } from "lucide-react";
import { ChatMarkdown } from "./ChatMarkdown";

export const CustomAssistantMessage = (props: AssistantMessageProps) => {
  const { message, isLoading, subComponent } = props;

  return (
    <div className="pb-4">
      {(message || isLoading) && (
        <div className="rounded-lg border border-[var(--border-subtle)] bg-[var(--surface)] p-4 shadow-sm dark:border-gray-700">
          <div className="text-sm text-[var(--text-body)]">
            <ChatMarkdown content={message?.content || ""} />
            {isLoading && (
              <div className="mt-2 flex items-center gap-2 text-xs text-[var(--brand)]">
                <Loader className="h-3 w-3 animate-spin" />
                <span>Thinking...</span>
              </div>
            )}
          </div>
        </div>
      )}

      {subComponent && <div>{subComponent}</div>}
    </div>
  );
};
