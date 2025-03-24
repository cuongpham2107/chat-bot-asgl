import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

export function ThinkingIndicator() {
  return (
    <div className="flex flex-col items-start gap-4 p-4 rounded-lg bg-gray-50 mr-12">
      <div className="flex gap-3">
        <Avatar>
          <AvatarImage src="/chatbot.png" alt="Assistant" />
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
        <div className="mt-1 text-sm animate-pulse">Suy luận...</div>
      </div>
    </div>
  );
}
