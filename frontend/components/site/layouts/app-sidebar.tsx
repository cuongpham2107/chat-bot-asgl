"use client";

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
  SidebarMenu,
  SidebarRail,
  useSidebar,
} from "@/components/ui/sidebar";
import { groupChatsByDate } from "@/lib/utils";
import { Chat } from "@/types";
import { useEffect, useState } from "react";
import { MenuItem } from "./menu-item";
import { useParams } from "next/navigation";
import {
  AlertDialogHeader,
  AlertDialogFooter,
} from "@/components/ui/alert-dialog";
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogCancel,
  AlertDialogAction,
} from "@/components/ui/alert-dialog";
import { toast } from "@/components/ui/toast";
import { NavUser } from "./nav-user";
import { useSession } from "next-auth/react"

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  // Kiểm tra tính hợp lệ của mã thông báo trên giá treo và cứ sau 5 phút
  //  const { isValidating } = useAuthProtection(true, 5 * 60 * 1000);
  const { data: session } = useSession()

  const BACKEND_API_URL = process.env.NEXT_PUBLIC_BACKEND_API_URL!;


  const { setOpenMobile } = useSidebar();
  const { id } = useParams();

  const [historiesChat, setHistoriesChat] = useState<Chat[]>([]);

  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  useEffect(() => {
    const fetchHistories = async () => {
      fetch(`${BACKEND_API_URL}/api/chats`, { method: "GET" , headers: { "Content-Type": "application/json" , "Authorization": `Bearer ${session?.user?.accessToken}` } })
        .then((response) => response.json())
        .then((data) => {
          setHistoriesChat(data);
        });
    };
    fetchHistories();
  }, [BACKEND_API_URL, session?.user?.accessToken]);

  const handleDeleteChat = async () => {
    if (deleteId) {
      fetch(`${BACKEND_API_URL}/api/chats/` + deleteId, { method: "DELETE", headers: { "Content-Type": "application/json" , "Authorization": `Bearer ${session?.user?.accessToken}` } })
        .then((response) => {
          if (response.ok) {
            setHistoriesChat((prevChats) =>
              prevChats.filter((chat) => chat.id !== deleteId)
            );
            setShowDeleteDialog(false);
            toast({
              type: "success",
              description: "Xóa lịch sử trò chuyện thành công",
            });
          } else {
            toast({
              type: "error",
              description: "Xóa lịch sử trò chuyện không thành công",
            });
          }
        })
        .catch((error) => {
          toast({
            type: "error",
            description:
              error instanceof Error
                ? error.message
                : "Đã xảy ra lỗi không xác định",
          });
        });
    }
  };

  return (
    <>
      <Sidebar {...props}>
        <SidebarHeader>
          <div className="flex flex-row items-center justify-between px-2 py-2">
            <div className="flex flex-col gap-1">
              <h1 className="text-lg font-semibold text-sidebar-foreground">
                Lịch sử trò chuyện
              </h1>
              <p className="text-xs text-sidebar-foreground/50">
                Cuộc trò chuyện của bạn với AI
              </p>
            </div>
            
          </div>
        </SidebarHeader>
        <SidebarContent>
          <SidebarGroup>
            <SidebarGroupContent>
              <SidebarMenu>
                {historiesChat &&
                  (() => {
                    const groupedChats = groupChatsByDate(historiesChat);

                    return (
                      <>
                        {groupedChats.today.length > 0 && (
                          <>
                            <div className="px-2 py-1 text-xs text-sidebar-foreground/50">
                              Hôm nay
                            </div>
                            {groupedChats.today.map((chat) => (
                              <MenuItem
                                key={chat.id}
                                chat={chat}
                                isActive={chat.id === id}
                                onDelete={(chatId) => {
                                  setDeleteId(chatId);
                                  setShowDeleteDialog(true);
                                }}
                                setOpenMobile={setOpenMobile}
                              />
                            ))}
                          </>
                        )}

                        {groupedChats.yesterday.length > 0 && (
                          <>
                            <div className="px-2 py-1 text-xs text-sidebar-foreground/50 mt-6">
                              Hôm qua
                            </div>
                            {groupedChats.yesterday.map((chat) => (
                              <MenuItem
                                key={chat.id}
                                chat={chat}
                                isActive={chat.id === id}
                                onDelete={(chatId) => {
                                  setDeleteId(chatId);
                                  setShowDeleteDialog(true);
                                }}
                                setOpenMobile={setOpenMobile}
                              />
                            ))}
                          </>
                        )}

                        {groupedChats.lastWeek.length > 0 && (
                          <>
                            <div className="px-2 py-1 text-xs text-sidebar-foreground/50 mt-6">
                              7 ngày qua
                            </div>
                            {groupedChats.lastWeek.map((chat) => (
                              <MenuItem
                                key={chat.id}
                                chat={chat}
                                isActive={chat.id === id}
                                onDelete={(chatId) => {
                                  setDeleteId(chatId);
                                  setShowDeleteDialog(true);
                                }}
                                setOpenMobile={setOpenMobile}
                              />
                            ))}
                          </>
                        )}

                        {groupedChats.lastMonth.length > 0 && (
                          <>
                            <div className="px-2 py-1 text-xs text-sidebar-foreground/50 mt-6">
                              30 ngày qua
                            </div>
                            {groupedChats.lastMonth.map((chat) => (
                              <MenuItem
                                key={chat.id}
                                chat={chat}
                                isActive={chat.id === id}
                                onDelete={(chatId) => {
                                  setDeleteId(chatId);
                                  setShowDeleteDialog(true);
                                }}
                                setOpenMobile={setOpenMobile}
                              />
                            ))}
                          </>
                        )}

                        {groupedChats.older.length > 0 && (
                          <>
                            <div className="px-2 py-1 text-xs text-sidebar-foreground/50 mt-6">
                              Cũ hơn
                            </div>
                            {groupedChats.older.map((chat) => (
                              <MenuItem
                                key={chat.id}
                                chat={chat}
                                isActive={chat.id === id}
                                onDelete={(chatId) => {
                                  setDeleteId(chatId);
                                  setShowDeleteDialog(true);
                                }}
                                setOpenMobile={setOpenMobile}
                              />
                            ))}
                          </>
                        )}
                      </>
                    );
                  })()}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        </SidebarContent>
        <SidebarRail />
        <SidebarFooter>
        <NavUser 
            user={session?.user?.user ? JSON.parse(session.user.user as string) : {}} 
          />
        </SidebarFooter>
      </Sidebar>
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              Bạn có hoàn toàn chắc chắn không?
            </AlertDialogTitle>
            <AlertDialogDescription>
              Hành động này không thể được hoàn tác. Điều này sẽ xóa vĩnh viễn
              trò chuyện và loại bỏ nó khỏi máy chủ của chúng tôi.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Hủy bỏ</AlertDialogCancel>
            <AlertDialogAction onClick={handleDeleteChat}>
              Tiếp tục
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
