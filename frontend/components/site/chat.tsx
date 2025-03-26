"use client";

import { useChat } from "@/hooks/useChat";
import { FileUploadDialog } from "@/components/ui/file-upload-dialog";
import { ChatMessage } from "@/components/site/chat/ChatMessage";
import { ThinkingIndicator } from "@/components/site/chat/ThinkingIndicator";
import { StreamingMessage } from "@/components/site/chat/StreamingMessage";
import { UploadedFiles } from "@/components/site/chat/UploadedFiles";
import { ChatInput } from "@/components/site/chat/ChatInput";

interface ChatComponentProps {
  id?: string;
}

export default function ChatComponent({ id }: ChatComponentProps) {
  const {
    userInfo,
    messages,
    input,
    setInput,
    optionDataApi,
    selectedOptionDataApi,
    setSelectedOptionDataApi,
    isLoading,
    isThinking,
    streamingMessage,
    messagesEndRef,
    uploadedFiles,
    isUploadDialogOpen,
    setIsUploadDialogOpen,
    isUploading,
    handleSubmit,
    handleFileUpload,
    handleFileDelete,
  } = useChat({ chatId: id });
  return (
    
    <div className="flex flex-col h-[calc(100vh)] w-full">
      {/* Chat messages */}
      <div className="flex-1 overflow-y-auto w-full">
        <div className="flex flex-col p-4 space-y-4 max-w-4xl mx-auto w-full">
          {messages ? (
            Array.isArray(messages) && messages.length > 0 ? (
              messages.map((message) => (
                <ChatMessage key={message.id} message={message} userInfo={userInfo} />
              ))
            ) : (
              <div className="text-center text-gray-500 py-8">
                Bắt đầu một cuộc trò chuyện!
              </div>
            )
          ) : null}

          {/* Thinking indicator */}
          {isThinking && <ThinkingIndicator />}

          {/* Streaming message */}
          {streamingMessage && <StreamingMessage message={streamingMessage} />}

          {/* Invisible element to scroll to */}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Display uploaded files */}
      <UploadedFiles files={uploadedFiles} onDelete={handleFileDelete} />

      {/* Chat input */}
      <ChatInput
        input={input}
        setInput={setInput}
        optionDataApi={optionDataApi}
        selectedOptionDataApi={selectedOptionDataApi}
        setSelectedOptionDataApi={setSelectedOptionDataApi}
        handleSubmit={handleSubmit}
        isLoading={isLoading}
        isUploading={isUploading}
        setIsUploadDialogOpen={setIsUploadDialogOpen}
        uploadedFilesCount={uploadedFiles.length}
      />

      {/* File Upload Dialog */}
      <FileUploadDialog
        isOpen={isUploadDialogOpen}
        onClose={() => setIsUploadDialogOpen(false)}
        onFileUpload={handleFileUpload}
        existingFiles={uploadedFiles}
      />
    </div>
  );
}
