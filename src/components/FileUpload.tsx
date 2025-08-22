import React, { useState, useRef } from 'react';
import { Upload, File, X } from 'lucide-react';
import { uploadFile, checkProcessingStatus } from '../services/api';
import { toast } from 'react-toastify';

interface FileUploadProps {
  onFileUpload: (file: File, extractedText: string, extractedImages: string[], jsonData: any[], uploadId?: string, taskId?: string) => void;
}

interface ProcessingStatus {
  status: 'processing' | 'completed' | 'error' | 'extracted' | 'failed';
  progress: number;
  result?: any;
  error?: string;
}

const FileUpload: React.FC<FileUploadProps> = ({ onFileUpload }) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [taskId, setTaskId] = useState<string | null>(null);
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

  const handleFileUpload = async (file: File) => {
    // Check file type
    const fileType = file.type;
    const validTypes = [
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'image/jpeg',
      'image/png',
      'text/plain'
    ];

    if (!validTypes.includes(fileType)) {
      toast.error('Invalid file type. Please upload a PDF, DOCX, JPG, PNG, or TXT file.');
      return;
    }

    setIsUploading(true);
    
    try {
      const response = await uploadFile(file);
      
      // Check if response indicates async processing
      if (response.task_id) {
        setIsUploading(false);
        setIsProcessing(true);
        setTaskId(response.task_id);
        pollProcessingStatus(response.task_id);
      } else {
        // Synchronous processing completed
        setIsUploading(false);
        setProgress(100);
        onFileUpload(file, response.extracted_text || '', response.extracted_images || [], response.extracted_json || [], response.id);
      }
    } catch (error) {
      console.error('Upload error:', error);
      setIsUploading(false);
      setIsProcessing(false);
      toast.error('Failed to upload file. Please try again.');
    }
  };

  const pollProcessingStatus = async (taskId: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const status: ProcessingStatus = await checkProcessingStatus(taskId);
        setProgress(status.progress);
        
        if (status.status === 'completed') {
          clearInterval(pollInterval);
          setIsProcessing(false);
          setProgress(100);
          
          if (status.result) {
            onFileUpload(status.result.file, status.result.extracted_text || '', status.result.extracted_images || [], status.result.extracted_json || [], status.result.id, taskId);
          }
        } else if (status.status === 'error') {
          clearInterval(pollInterval);
          setIsProcessing(false);
          console.error('Processing error:', status.error);
          toast.error(`Processing failed: ${status.error}`);
        } else if (status.status === 'failed') {
          clearInterval(pollInterval);
          setIsProcessing(false);
          console.error('Processing failed:', status.error);
          toast.error(`Processing failed: ${status.error}`);
        }
      } catch (error) {
        console.error('Error checking status:', error);
      }
    }, 2000); // Poll every 2 seconds
  };

  const getStatusMessage = () => {
    if (isUploading) return 'Uploading file...';
    if (isProcessing) return `Processing file... ${progress}%`;
    return '';
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
        } ${isUploading || isProcessing ? 'pointer-events-none opacity-50' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {(isUploading || isProcessing) ? (
          <div className="space-y-4">
            <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
            <p className="text-lg font-medium text-gray-900">{getStatusMessage()}</p>
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${progress}%` }}
              ></div>
            </div>
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