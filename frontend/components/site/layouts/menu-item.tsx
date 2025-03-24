// import { CheckCircleFillIcon } from "@/components/ui/icons";
import {
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarMenuAction,
} from "@/components/ui/sidebar";
import { Chat } from "@/types";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  // DropdownMenuSub,
  // DropdownMenuSubTrigger,
  // DropdownMenuPortal,
  // DropdownMenuSubContent,
  DropdownMenuItem,
} from "@/components/ui/dropdown-menu";
import {
  MoreHorizontalIcon,
  // ShareIcon,
  // LockIcon,
  // GlobeIcon,
  TrashIcon,
} from "lucide-react";
import { memo } from "react";
import Link from "next/link";

const PureChatItem = ({
  chat,
  isActive,
  onDelete,
  setOpenMobile,
}: {
  chat: Chat;
  isActive: boolean;
  onDelete: (chatId: string) => void;
  setOpenMobile: (open: boolean) => void;
}) => {
  return (
    <SidebarMenuItem>
      <SidebarMenuButton asChild isActive={isActive}>
        <Link href={`/chat/${chat.id}`} onClick={() => setOpenMobile(false)}>
          <span>{chat.title}</span>
        </Link>
      </SidebarMenuButton>

      <DropdownMenu modal={true}>
        <DropdownMenuTrigger asChild>
          <SidebarMenuAction
            className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground mr-0.5"
            showOnHover={!isActive}
          >
            <MoreHorizontalIcon />
            <span className="sr-only">More</span>
          </SidebarMenuAction>
        </DropdownMenuTrigger>

        <DropdownMenuContent side="bottom" align="start">
          {/* <DropdownMenuSub>
            <DropdownMenuSubTrigger className="cursor-pointer">
              <ShareIcon />
              <span>Chia sẻ</span>
            </DropdownMenuSubTrigger>
            <DropdownMenuPortal>
              <DropdownMenuSubContent>
                <DropdownMenuItem className="cursor-pointer flex-row justify-between">
                  <div className="flex flex-row gap-2 items-center">
                    <LockIcon size={12} />
                    <span>Private</span>
                  </div>

                  <CheckCircleFillIcon />
                </DropdownMenuItem>
                <DropdownMenuItem className="cursor-pointer flex-row justify-between">
                  <div className="flex flex-row gap-2 items-center">
                    <GlobeIcon />
                    <span>Public</span>
                  </div>
                  <CheckCircleFillIcon />
                </DropdownMenuItem>
              </DropdownMenuSubContent>
            </DropdownMenuPortal>
          </DropdownMenuSub> */}

          <DropdownMenuItem
            className="cursor-pointer text-destructive focus:bg-destructive/15 focus:text-destructive dark:text-red-500"
            onSelect={() => onDelete(chat.id)}
          >
            <TrashIcon />
            <span>Xoá</span>
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </SidebarMenuItem>
  );
};
export const MenuItem = memo(PureChatItem, (prevProps, nextProps) => {
  if (prevProps.isActive !== nextProps.isActive) return false;
  return true;
});
