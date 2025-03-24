import { cn } from "@/lib/utils";
import { X } from "lucide-react";

interface UploadedFilesProps {
  files: File[];
  onDelete: (index: number) => void;
}

export function UploadedFiles({ files, onDelete }: UploadedFilesProps) {
  if (files.length === 0) return null;

  return (
    <div className="px-4 py-2 bg-gray-50 border-t border-gray-200">
      <div className="max-w-4xl mx-auto">
        <p className="text-sm text-gray-600 mb-2">
          Tập tin đã tải lên ({files.length}):
        </p>
        <div className="flex flex-wrap gap-2">
          {files.map((file, index) => (
            <div
              key={index}
              className={cn(
                "px-3 py-1 rounded-full text-xs flex items-center border",
                file.type.endsWith("pdf")
                  ? "bg-blue-50"
                  : file.type.endsWith("docx")
                  ? "bg-green-50"
                  : file.type.endsWith("csv")
                  ? "bg-yellow-50"
                  : "bg-gray-50"
              )}
            >
              <span className="truncate max-w-[150px] font-semibold">
                {file.name}
              </span>
              <button
                className="ml-2 text-gray-500 bg-red-100 hover:text-red-500 hover:bg-red-300 hover:border hover:border-red-500 rounded-full p-1 cursor-pointer"
                onClick={() => onDelete(index)}
              >
                <X size={14} />
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
