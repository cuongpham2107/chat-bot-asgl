import { useState, useCallback, useEffect, useRef } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { toast } from "@/components/ui/toast";
const generateId = () => Math.random().toString(36).substring(2, 10);

export interface UserInfo {
  asgl_id: string;
  name: string;
  email: string;
  mobile_phone: string;
  username: string;
  avatar_url: string;
}

export interface Message {
  id: string;
  chatId: string;
  role: "user" | "assistant";
  content: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface UploadedFileInfo {
  id: string;
  filename: string;
  filepath: string;
  metadata: {
    collection_id: string;
  };
  createdAt: string;
  updatedAt: string;
}

interface UseChatProps {
  chatId?: string;
}

export interface OptionItem {
  id: string;
  name: string;
  icon: string;
  description: string;
  url: string;
}

export function useChat({ chatId }: UseChatProps) {
  const { data: session } = useSession();
  const [userInfo, setUserInfo] = useState<UserInfo>();
  const BACKEND_API_URL = process.env.NEXT_PUBLIC_BACKEND_API_URL!;
  const router = useRouter();

  // State variables
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isThinking, setIsThinking] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState<Message | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [uploadedFileInfos, setUploadedFileInfos] = useState<UploadedFileInfo[]>([]);
  const [isUploadDialogOpen, setIsUploadDialogOpen] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  const [optionDataApi, setOptionDataApi] = useState<OptionItem[]>([]);
  const [selectedOptionDataApi, setSelectedOptionDataApi] = useState<OptionItem | null>(null);

  // Helper function to create API request headers
  const createHeaders = useCallback(() => {
    return {
      accept: "application/json",
      "Content-Type": "application/json",
      Authorization: `Bearer ${session?.user.accessToken}`,
    };
  }, [session?.user.accessToken]);

  // Helper function to make API requests
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const makeApiRequest = useCallback(async (url: string, method: string, body?: any) => {
    const response = await fetch(url, {
      method,
      headers: createHeaders(),
      body: body ? JSON.stringify(body) : undefined,
    });

    if (!response.ok) {
      throw new Error(`API request failed with status ${response.status}`);
    }

    return await response.json();
  }, [createHeaders]);

  // Helper function to send a message to the API
  const sendMessageToApi = useCallback(async (
    chatId: string, 
    messageContent: string, 
    useApiChat: boolean, 
    apiUrl?: string, 
    fileId?: string
  ) => {
    let url;
    let body;

    if (useApiChat) {
      url = `${BACKEND_API_URL}/api/messages/${chatId}/api-chat`;
      body = {
        content: messageContent,
        api_url: apiUrl
      };
    } else {
      url = `${BACKEND_API_URL}/api/messages/chat/${chatId}/send`;
      body = {
        content: messageContent,
        source_file_id: fileId,
        metadata: null,
      };
    }

    return await makeApiRequest(url, "POST", body);
  }, [BACKEND_API_URL, makeApiRequest]);

  // Set Option Data API with get from API
  useEffect(() => {
    const fetchOptionDataApi = async () => {
      try {
        const data = await makeApiRequest(`${BACKEND_API_URL}/api/options`, "GET");
        setOptionDataApi(data);
      } catch (error) {
        console.error("Error fetching options:", error);
      }
    };

    fetchOptionDataApi();
  }, [BACKEND_API_URL, makeApiRequest]);

  // Set user information from session
  useEffect(() => {
    if (typeof session?.user?.user === "string") {
      const user = JSON.parse(session.user.user) as UserInfo;
      setUserInfo(user);
    }
  }, [session?.user]);

  // Fetch message history when chatId changes
  const fetchHistoryMessages = useCallback(async () => {
    try {
      const data = await makeApiRequest(`/api/chats/${chatId}`, "GET");
      setMessages(data);
    } catch (error) {
      console.error("Error fetching message history:", error);
    }
  }, [chatId, makeApiRequest]);

  useEffect(() => {
    if (!chatId) return;
    fetchHistoryMessages();
  }, [fetchHistoryMessages, chatId]);

  // Scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingMessage?.content]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // Simulate streaming text API
  const simulateStreamingResponse = async (assistantMessage: Message) => {
    setIsThinking(false);
    // Create a temporary message object for streaming
    const tempMessage: Message = {
      id: assistantMessage.id,
      chatId: assistantMessage.chatId,
      role: assistantMessage.role,
      content: "",
      createdAt: assistantMessage.createdAt,
      updatedAt: assistantMessage.updatedAt,
    };
    setIsLoading(true);
    setStreamingMessage(tempMessage);

    // Generate a response based on user input
    const response = assistantMessage.content;
    const words = response.split(" ");

    // Stream each word with a delay
    for (let i = 0; i < words.length; i++) {
      await new Promise((resolve) => setTimeout(resolve, 50)); // Adjust speed as needed
      setStreamingMessage((prev) => {
        if (!prev) return null;
        return {
          ...prev,
          content: prev.content + (i === 0 ? "" : " ") + words[i],
        };
      });
    }

    // Add the complete message to the messages array
    setMessages((prev) => [...prev, { ...tempMessage, content: response }]);
    setStreamingMessage(null);
    setIsLoading(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if ((!input.trim() && uploadedFiles.length === 0) || isLoading) return;

    // Create message content including file information if files are uploaded
    let messageContent = input.trim();
    if (uploadedFiles.length > 0) {
      const fileNames = uploadedFiles.map((file) => file.name).join(", ");
      messageContent += messageContent
        ? `\n\n🔗: ${fileNames}`
        : `🔗: ${fileNames}`;
    }

    setIsThinking(true);
    setIsLoading(true);
    setInput("");

    try {
      // Add user message to UI immediately
      const userMessage: Message = {
        id: generateId(),
        chatId: chatId || "new-chat",
        role: "user",
        content: messageContent,
        createdAt: new Date(),
        updatedAt: new Date(),
      };

      if (!chatId) {
        setMessages([userMessage]);
        await actionNewChat(messageContent);
      } else {
        setMessages((prev) => [...prev, userMessage]);
        await actionOldChat(messageContent);
      }
    } catch (error) {
      console.error("Error sending message:", error);
      toast({
        type: "error",
        description: "Failed to send message. Please try again.",
      });
    } finally {
      setIsLoading(false);
      setIsThinking(false);
    }
  };

  // Create new chat
  const actionNewChat = async (messageContent: string) => {
    try {
      // Get file ID if available
      const fileId = uploadedFileInfos.length > 0 ? uploadedFileInfos[0].id : undefined;
      
      // Create a new chat
      const chatNewData = await makeApiRequest(`${BACKEND_API_URL}/api/chats`, "POST", {
        title: "Cuộc trò chuyện mới",
        visibility: "public",
        userId: session?.user.id,
      });
      
      const chatId = chatNewData.id;
      
      // Send message to the appropriate API endpoint
      const useApiChat = !!(selectedOptionDataApi && selectedOptionDataApi.id);
      const apiUrl = selectedOptionDataApi?.url;
      
      const data = await sendMessageToApi(
        chatId, 
        messageContent, 
        useApiChat, 
        apiUrl, 
        fileId
      );
      
      await simulateStreamingResponse(data as Message);
      
      // Redirect to the new chat page
      router.push(`/chat/${chatId}`);
      router.refresh();
    } catch (error) {
      console.error("Error creating new chat:", error);
      toast({
        type: "error",
        description: "Failed to create new chat. Please try again.",
      });
    }
  };

  // Send message in existing chat
  const actionOldChat = async (messageContent: string) => {
    try {
      // Get file ID if available
      const fileId = uploadedFileInfos.length > 0 ? uploadedFileInfos[0].id : undefined;
      
      // Determine if we should use the API chat endpoint
      const useApiChat = !!(selectedOptionDataApi && selectedOptionDataApi.id);
      const apiUrl = selectedOptionDataApi?.url;
      
      // Send message to the appropriate API endpoint
      const data = await sendMessageToApi(
        chatId!, 
        messageContent, 
        useApiChat, 
        apiUrl, 
        fileId
      );
      
      await simulateStreamingResponse(data as Message);
    } catch (error) {
      console.error("Error sending message to existing chat:", error);
      toast({
        type: "error",
        description: "Failed to send message. Please try again.",
      });
    }
  };

  // File upload handling
  const handleFileUpload = (files: File[]) => {
    setUploadedFiles(files);

    // Only upload files if there are files to upload
    if (files.length > 0) {
      uploadFiles(files);
    } else {
      // Clear uploaded file infos if no files are selected
      setUploadedFileInfos([]);
    }
  };

  const uploadFiles = async (files: File[]) => {
    if (files.length === 0) {
      setUploadedFileInfos([]);
      return;
    }
    setIsUploading(true);

    try {
      const formData = new FormData();
      files.forEach((file) => {
        formData.append("files", file);
      });

      const response = await fetch(`${BACKEND_API_URL}/api/files/upload`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${session?.user.accessToken}`,
        },
        body: formData,
      });

      if (!response.ok) {
        throw new Error(
          `Tải lên không thành công với trạng thái ${response.status}`
        );
      }

      const data = await response.json();
      // Store the uploaded file information
      if (data && Array.isArray(data)) {
        setUploadedFileInfos(data);
        toast({
          type: "success",
          description: `${files.length} Tệp được tải lên thành công`,
        });
      } else {
        setUploadedFileInfos([]);
        toast({
          type: "error",
          description: "Định dạng phản hồi không mong muốn từ máy chủ",
        });
      }
    } catch (error) {
      setUploadedFileInfos([]);
      toast({
        type: "error",
        description:
          error instanceof Error
            ? error.message
            : "Đã xảy ra lỗi trong quá trình tải lên tệp",
      });
    } finally {
      setIsUploading(false);
    }
  };

  // Handle file deletion
  const handleFileDelete = async (index: number) => {
    try {
      // Get the file information to be deleted
      const fileInfo = uploadedFileInfos[index];

      if (fileInfo && fileInfo.id) {
        // Call API to delete the file from backend
        await makeApiRequest(`${BACKEND_API_URL}/api/files/${fileInfo.id}`, "DELETE");

        toast({
          type: "success",
          description: "Tệp đã xóa thành công",
        });
      }

      // Update frontend state to remove the file
      setUploadedFiles((files) => files.filter((_, i) => i !== index));
      setUploadedFileInfos((infos) => infos.filter((_, i) => i !== index));
    } catch (error) {
      toast({
        type: "error",
        description:
          error instanceof Error
            ? error.message
            : "An error occurred while deleting the file",
      });
    }
  };

  return {
    userInfo,
    messages,
    input,
    setInput,
    optionDataApi,
    setOptionDataApi,
    selectedOptionDataApi,
    setSelectedOptionDataApi,
    isLoading,
    isThinking,
    streamingMessage,
    messagesEndRef,
    uploadedFiles,
    uploadedFileInfos,
    isUploadDialogOpen,
    setIsUploadDialogOpen,
    isUploading,
    handleSubmit,
    handleFileUpload,
    handleFileDelete,
  };
}