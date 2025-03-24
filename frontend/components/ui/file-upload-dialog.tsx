"use client";

import { useState, useRef, useEffect } from "react";
import { X, Upload, File as FileIcon, Trash2 } from "lucide-react";

interface FileUploadDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onFileUpload: (files: File[]) => void;
  existingFiles?: File[];
}

export function FileUploadDialog({
  isOpen,
  onClose,
  onFileUpload,
  existingFiles = [],
}: FileUploadDialogProps) {
  const [files, setFiles] = useState<File[]>(existingFiles);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dialogRef = useRef<HTMLDivElement>(null);

  // Reset files state when existingFiles prop changes
  useEffect(() => {
    setFiles(existingFiles);
  }, [existingFiles]);

  // Handle click outside to close
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dialogRef.current && !dialogRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen, onClose]);

  // Handle escape key to close
  useEffect(() => {
    const handleEscKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener("keydown", handleEscKey);
    }

    return () => {
      document.removeEventListener("keydown", handleEscKey);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const newFiles = Array.from(e.target.files);
      setFiles((prevFiles) => [...prevFiles, ...newFiles]);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const newFiles = Array.from(e.dataTransfer.files);
      setFiles((prevFiles) => [...prevFiles, ...newFiles]);
    }
  };

  const removeFile = (index: number) => {
    setFiles((prevFiles) => prevFiles.filter((_, i) => i !== index));
  };

  const handleSubmit = () => {
    onFileUpload(files);
    onClose();
  };

  const triggerFileInput = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop with blur effect */}
      <div className="absolute inset-0 bg-black/30 backdrop-blur-sm" />
      
      {/* Dialog content */}
      <div 
        ref={dialogRef}
        className="relative bg-white rounded-lg w-full max-w-md p-6 shadow-xl animate-in fade-in duration-200">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">Upload Files</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        <div
          className={`border-2 border-dashed rounded-lg p-6 mb-4 text-center transition-colors duration-200 ${
            isDragging ? "border-blue-500 bg-blue-50" : "border-gray-300 hover:border-gray-400"
          }`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <input
            ref={fileInputRef}
            type="file"
            onChange={handleFileChange}
            className="hidden"
            multiple
          />
          <Upload className="mx-auto h-12 w-12 text-gray-400" />
          <p className="mt-2 text-sm text-gray-600">
            Kéo và thả file vào đây hoặc{" "}
            <button
              type="button"
              className="text-blue-500 hover:text-blue-700 font-medium"
              onClick={triggerFileInput}
            >
              chọn file
            </button>
          </p>
          <p className="text-xs text-gray-500 mt-1">
            Hỗ trợ tất cả các định dạng file
          </p>
        </div>

        {files.length > 0 && (
          <div className="mb-4">
            <h3 className="font-medium mb-2">Danh sách file ({files.length})</h3>
            <div className="max-h-40 overflow-y-auto rounded border border-gray-100">
              {files.map((file, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between py-2 px-3 bg-gray-50 hover:bg-gray-100 transition-colors border-b last:border-b-0 border-gray-100"
                >
                  <div className="flex items-center">
                    <FileIcon size={16} className="text-gray-500 mr-2" />
                    <div className="text-sm">
                      <p className="font-medium truncate max-w-[200px]">{file.name}</p>
                      <p className="text-xs text-gray-500">
                        {(file.size / 1024).toFixed(2)} KB
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => removeFile(index)}
                    className="text-gray-400 hover:text-red-500 transition-colors p-1 rounded-full hover:bg-gray-200"
                    aria-label="Remove file"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="flex justify-end gap-2">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
          >
            Hủy
          </button>
          <button
            onClick={handleSubmit}
            className={`px-4 py-2 text-sm text-white rounded-md transition-colors ${
              files.length === 0 
                ? "bg-blue-300 cursor-not-allowed" 
                : "bg-blue-500 hover:bg-blue-600"
            }`}
            disabled={files.length === 0}
          >
            Upload
          </button>
        </div>
      </div>
    </div>
  );
}
