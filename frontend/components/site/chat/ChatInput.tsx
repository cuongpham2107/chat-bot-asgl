import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

import SwirlingEffectSpinner from "../../ui/spin-swirling-effect";

import {
  PlusIcon,
  Send
} from "lucide-react";
// import { Badge } from "@/components/ui/badge";

import { OptionItem } from "@/hooks/useChat";
import OptionChatWithApi from "./OptionChatWithApi";

interface ChatInputProps {
  input: string;
  setInput: (value: string) => void;
  optionDataApi: OptionItem[];
  selectedOptionDataApi: OptionItem | null;
  setSelectedOptionDataApi: (value: OptionItem | null) => void;
  handleSubmit: (e: React.FormEvent) => void;
  isLoading: boolean;
  isUploading: boolean;
  setIsUploadDialogOpen: (value: boolean) => void;
  uploadedFilesCount: number;
}

export function ChatInput({
  input,
  setInput,
  optionDataApi,
  selectedOptionDataApi,
  setSelectedOptionDataApi,
  handleSubmit,
  isLoading,
  isUploading,
  setIsUploadDialogOpen,
  uploadedFilesCount,
}: ChatInputProps) {

  return (
    <div className="p-2 max-w-4xl mx-auto w-full">
      <form
        onSubmit={handleSubmit}
        className="flex flex-col gap-2 border border-gray-600 rounded-xl p-2"
      >
        <textarea
          value={input}
          onChange={(e) => {
            setInput(e.target.value);
            e.target.style.height = "auto"; // Reset height
            e.target.style.height = `${e.target.scrollHeight}px`; // Set height based on scroll height
          }}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              if ((input.trim() || uploadedFilesCount > 0) && !isLoading) {
                handleSubmit(e);
              }
            }
          }}
          placeholder="Nhập tin nhắn..."
          className="focus-visible:border-none focus:outline-none focus:border-blue-500 border-none rounded-md p-2 w-full max-h-36 overflow-y-auto"
          rows={1}
          disabled={isLoading}
        />
        <div className="flex flex-row items-center justify-between gap-2">
          <div className="flex flex-row items-center gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => setIsUploadDialogOpen(true)}
              className="rounded-full px-2.5 m-0 has-[>svg]:px-2.5"
              disabled={isLoading || isUploading}
            >
              <PlusIcon size={18} />
            </Button>
            <OptionChatWithApi optionDataApi={optionDataApi} selectedOptionDataApi={selectedOptionDataApi} setSelectedOptionDataApi={setSelectedOptionDataApi}/>
          </div>

          <Button
            type="submit"
            disabled={
              isLoading ||
              isUploading ||
              (!input.trim() && uploadedFilesCount === 0)
            }
            className={cn(
              "flex items-center justify-center rounded-full min-w-10 h-10 transition-colors has-[>svg]:p-0",
              input.trim() || uploadedFilesCount > 0
                ? "bg-blue-500 hover:bg-blue-600 text-white border-transparent"
                : "bg-gray-100 border-gray-200 text-gray-400",
              "disabled:opacity-50 disabled:cursor-not-allowed"
            )}
          >
            {isLoading || isUploading ? (
              <SwirlingEffectSpinner />
            ) : (
              <Send size={18} />
            )}
          </Button>
        </div>
      </form>
    </div>
  );
}
