import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Markdown } from "@/components/ui/markdown";
import { Message } from "@/hooks/useChat";

interface StreamingMessageProps {
  message: Message;
}

export function StreamingMessage({ message }: StreamingMessageProps) {
  return (
    <div
      key={message.id}
      className="flex flex-col items-start gap-4 p-4 rounded-lg bg-gray-50 mr-12"
    >
      <div className="flex gap-3">
        <Avatar>
          <AvatarImage src="/chatbot.png" alt="Chat Bot" />
          <AvatarFallback>A</AvatarFallback>
        </Avatar>
        <div className="flex flex-col">
          <span className="font-semibold tracking-tight">Trợ lý</span>
          <span className="leading-none text-sm text-muted-foreground">
            Giải đáp thắc mắc của bạn
          </span>
        </div>
      </div>
      <div className="flex-1">
        <div className="mt-1 flex flex-col">
          <Markdown>{message.content}</Markdown>
          <span className="animate-pulse h-4 ml-0.5">▎</span>
        </div>
      </div>
    </div>
  );
}
