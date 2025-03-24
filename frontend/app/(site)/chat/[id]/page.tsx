import ChatComponent from "@/components/site/chat"

export default async function Page({
    params,
  }: {
    params: Promise<{ id: string }>
  }) {
    const { id } = await params
    return (
        <ChatComponent id={id} />
    )
  }