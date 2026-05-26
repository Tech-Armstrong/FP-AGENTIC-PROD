import { Calendar, CheckCircle, Loader } from "lucide-react";

type CurrentDateToolProps = {
  status: "executing" | "inProgress" | "complete" | "error";
};

export function CurrentDateTool({ status }: CurrentDateToolProps) {
  return (
    <div className="bg-white dark:bg-gray-800 p-3 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm">
      <div className="flex items-center gap-2 mb-1">
        <Calendar className="h-4 w-4 text-blue-500" />
        <h3 className="text-sm font-medium">getCurrentDate</h3>
      </div>

      {(status === "executing" || status === "inProgress") && (
        <div className="flex items-center gap-2 text-xs text-blue-500">
          <Loader className="h-3 w-3 animate-spin" />
          <span>Fetching today&apos;s date...</span>
        </div>
      )}

      {status === "complete" && (
        <div className="flex items-center gap-2 text-xs text-green-600 dark:text-green-400">
          <CheckCircle className="h-3 w-3" />
          <span>Current date retrieved for age and timeline calculations</span>
        </div>
      )}

      {status === "error" && (
        <p className="text-xs text-red-500">Could not retrieve current date</p>
      )}
    </div>
  );
}
