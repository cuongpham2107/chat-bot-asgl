export type Chat = {
    id: string;
    userId: string;
    title: string;
    visibility?: string;
    createdAt: Date;
    updatedAt: Date;
    messages: Message[];
};

export type Message = {
    id: string;
    chatId: string;
    role: string;
    content: string;
    createdAt: Date;
    updatedAt: Date;
};


export type GroupedChats = {
    today: Chat[];
    yesterday: Chat[];
    lastWeek: Chat[];
    lastMonth: Chat[];
    older: Chat[];
  };

