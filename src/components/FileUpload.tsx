import React, { useState, useRef } from 'react';
import { Upload, File, X } from 'lucide-react';

interface FileUploadProps {
  onFileUpload: (file: File) => void;
}

const FileUpload: React.FC<FileUploadProps> = ({ onFileUpload }) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileUpload(files[0]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileUpload(files[0]);
    }
  };

  const handleFileUpload = (file: File) => {
    setIsUploading(true);
    // Simulate upload delay
    setTimeout(() => {
      setIsUploading(false);
      onFileUpload(file);
    }, 1500);
  };

  const acceptedFormats = ['.pdf', '.jpg', '.jpeg', '.png', '.docx', '.txt'];

  return (
    <div className="p-6">
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Upload Your Document</h2>
        <p className="text-gray-600">
          Upload PDF, images, or text documents to start the conversion process
        </p>
      </div>

      <div
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-all ${
          isDragOver
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400'
        } ${isUploading ? 'pointer-events-none opacity-50' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {isUploading ? (
          <div className="space-y-4">
            <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
            <p className="text-lg font-medium text-gray-900">Uploading and processing...</p>
            <p className="text-gray-600">This may take a few moments</p>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto">
              <Upload className="h-8 w-8 text-blue-600" />
            </div>
            <div>
              <p className="text-lg font-medium text-gray-900 mb-2">
                Drag and drop your file here, or click to browse
              </p>
              <p className="text-gray-600 mb-4">
                Supported formats: PDF, JPG, PNG, DOCX, TXT
              </p>
              <button
                onClick={() => fileInputRef.current?.click()}
                className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors inline-flex items-center space-x-2"
              >
                <File className="h-5 w-5" />
                <span>Choose File</span>
              </button>
            </div>
          </div>
        )}
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept={acceptedFormats.join(',')}
        onChange={handleFileSelect}
        className="hidden"
      />

      <div className="mt-6 text-center">
        <p className="text-sm text-gray-500">
          Maximum file size: 50MB. Files are processed securely and deleted after conversion.
        </p>
      </div>
    </div>
  );
};

export default FileUpload;