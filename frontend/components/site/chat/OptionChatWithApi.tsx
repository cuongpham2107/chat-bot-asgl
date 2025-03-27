import { OptionItem } from "@/hooks/useChat";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "../../ui/alert-dialog";

import * as RadioGroup from "@radix-ui/react-radio-group";
import { CircleCheck, X } from "lucide-react";

import { Captions, CircleFadingArrowUp, Rocket } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import Image from "next/image";

interface OptionChatWithApiProps {
  optionDataApi: OptionItem[];
  selectedOptionDataApi: OptionItem | null;
  setSelectedOptionDataApi: (value: OptionItem | null) => void;
}
export default function OptionChatWithApi({
  optionDataApi,
  selectedOptionDataApi,
  setSelectedOptionDataApi,
}: OptionChatWithApiProps) {
  return (
    <>
      <AlertDialog>
        <AlertDialogTrigger asChild>
          {selectedOptionDataApi ? (
            <Button
              variant="outline"
              className="rounded-full border-2 border-sky-500 bg-gray-100 relative"
            >
              <Image
                src={selectedOptionDataApi.icon}
                alt=""
                width={16}
                height={16}
              />
              {selectedOptionDataApi.name}
              <div
                onClick={(e) => {
                  setSelectedOptionDataApi(null)
                  e.preventDefault()
                }}
                className="border-2 border-red-400 bg-red-50 rounded-full absolute top-0 right-0 translate-x-1/3 -translate-y-1/3 cursor-pointer hover:bg-red-100 transition-all duration-200 ease-in-out"
              >
                <X size={12} color="red" strokeWidth={2.5} />
              </div>
            </Button>
          ) : (
            <Button variant="outline" className="rounded-full">
              <Captions />
              Lựa chọn
            </Button>
          )}
        </AlertDialogTrigger>
        <AlertDialogContent className="sm:max-w-5xl w-full">
          <AlertDialogHeader>
            <AlertDialogTitle>
              <div className="flex flex-row items-center space-x-2">
                <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary/10">
                  <CircleFadingArrowUp className="h-[18px] w-[18px] text-primary" />
                </div>
                <h2 className="text-xl font-bold tracking-tight">
                  Chọn dữ liệu cần trò chuyện
                </h2>
              </div>
            </AlertDialogTitle>
            <AlertDialogDescription className="!mt-1 !mb-4 text-xs">
              Chọn loại dữ liệu mà bạn muốn trò chuyện với AI. Bạn có thể chọn
              một loại dữ liệu mà bạn muốn.
              <br />
              AI sẽ truy cập vào dữ liệu này để trả lời câu hỏi của bạn.
            </AlertDialogDescription>
            <RadioGroup.Root
              defaultValue={selectedOptionDataApi?.id}
              onValueChange={(value: string) => {
                const selectedOption = optionDataApi.find(
                  (option) => option.id === value
                );
                if (selectedOption) setSelectedOptionDataApi(selectedOption);
              }}
              className="w-full grid grid-cols-3 gap-2"
            >
              {optionDataApi?.length > 0 && optionDataApi.map((option) => (
                <RadioGroup.Item
                  key={option.id}
                  value={option.id}
                  disabled={!option.active}
                  className={cn(
                    "relative flex flex-row space-x-3 items-center group ring-[1px] ring-border rounded-2xl py-1 px-2 pr-3 text-start",
                    "data-[state=checked]:ring-2 data-[state=checked]:ring-blue-500",
                    option.active == false ? "opacity-50 cursor-not-allowed" : "",
                  )}
                >
                  <CircleCheck className="absolute top-1 -right-1 -translate-y-1/2 translate-x-1/2 h-4 w-4 text-primary fill-blue-500 stroke-white group-data-[state=unchecked]:hidden" />
                  <Image
                    src={option.icon}
                    alt={option.name}
                    width={25}
                    height={25}
                  />
                  <div className="flex flex-col space-y-1">
                    <span className="text-sm font-semibold tracking-tight">
                      {option.name}
                    </span>
                    <p className="text-xs max-w-full break-words italic">
                      {option.description}
                    </p>
                  </div>
                </RadioGroup.Item>
              ))}
            </RadioGroup.Root>
          </AlertDialogHeader>
          <AlertDialogFooter className="mt-4">
            <AlertDialogCancel>Đóng</AlertDialogCancel>
            <AlertDialogAction>
              <Rocket /> Sử dụng dữ liệu
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
