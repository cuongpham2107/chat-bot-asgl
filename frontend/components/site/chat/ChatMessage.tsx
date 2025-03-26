import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Markdown } from "@/components/ui/markdown";
import { cn } from "@/lib/utils";
import { Message, UserInfo } from "@/hooks/useChat";

interface ChatMessageProps {
  message: Message;
  userInfo?: UserInfo;
}

export function ChatMessage({ message, userInfo }: ChatMessageProps) {
  
  return (
    <div
      key={message.id}
      className={cn(
        "flex flex-col p-4 rounded-lg w-fit",
        message.role === "user"
          ? "bg-pink-50 items-end ml-auto"
          : "bg-gray-50 mr-12 items-start gap-4"
      )}
    >
      <div
        className={cn(
          "flex gap-2 items-center border-b border-gray-200 pb-2 w-full",
          message.role === "user" ? "flex-row-reverse" : "flex-row"
        )}
      >
        <Avatar>
          <AvatarImage
            src={
              message.role === "user"
                ? userInfo?.avatar_url
                : "/chatbot.png"
            }
            alt={message.role === "user" ? "User" : "Assistant"}
          />
          <AvatarFallback className="bg-blue-200">
            {message.role === "user" ? "U" : "A"}
          </AvatarFallback>
        </Avatar>
        <div
          className={cn(
            "flex flex-col",
            message.role === "user" ? "items-end" : ""
          )}
        >
          <span className="font-semibold tracking-tight">
            {message.role === "user" ? (userInfo?.name as string) : "Trợ lý"}
          </span>
          <span className="leading-none text-sm text-muted-foreground">
            {message.role === "user"
              ? userInfo?.email
              : "Giải đáp thắc mắc của bạn"}
          </span>
        </div>
      </div>
      <div className={`${message.role === "user" ? "" : "flex-1"}`}>
        <Markdown>{message.content}</Markdown>
      </div>
    </div>
  );
}
