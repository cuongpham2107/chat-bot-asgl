"use client";

import { SidebarTrigger } from "@/components/ui/sidebar";
import { PenBox } from "lucide-react";
import { useRouter } from "next/navigation";

export default function Header() {
  const route = useRouter();
  return (
    <>
      <header className="flex h-16 shrink-0 items-center gap-2 px-4 absolute top-0 left-0 right-0 z-10">
        <SidebarTrigger className="-ml-1 border border-gray-300 w-8 h-8 rounded-lg" />
        <div
          className="flex items-center justify-center w-8 h-8 rounded-lg cursor-pointer border-1 border-gray-300 hover:border-gray-400 focus:outline-none focus:ring-2 transition duration-200 ease-in-out"
          onClick={() => route.push("/")}
        >
          <PenBox color="black" size={16} strokeWidth={2.5} />
        </div>
      </header>
    </>
  );
}
