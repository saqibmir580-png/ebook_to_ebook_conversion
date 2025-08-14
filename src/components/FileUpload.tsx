import React, { useState, useRef, useCallback } from 'react';
import { Upload, File, X, Loader2 } from 'lucide-react';
import { uploadFile, UploadResponse } from '../services/api';
import { toast } from 'react-toastify';

type UploadStatus = 'idle' | 'uploading' | 'processing' | 'completed' | 'error';

interface FileUploadProps {
  onFileUpload: (file: File, uploadId?: string, jatsXml?: string) => void;
}

const FileUpload: React.FC<FileUploadProps> = ({ onFileUpload }) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<UploadStatus>('idle');
  const [progress, setProgress] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [filePreview, setFilePreview] = useState<string | null>(null);

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

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      // Create preview for images
      if (files[0].type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = (event) => {
          if (event.target?.result) {
            setFilePreview(event.target.result as string);
          }
        };
        reader.readAsDataURL(files[0]);
      } else {
        setFilePreview(null);
      }
      handleFileUpload(files[0]);
    }
  }, []);

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

    if (!validTypes.some(type => fileType.startsWith(type.split('/')[0]))) {
      toast.error('Invalid file type. Please upload a PDF, DOCX, JPG, PNG, or TXT file.');
      return;
    }

    // Check file size (max 50MB)
    const maxSize = 50 * 1024 * 1024; // 50MB
    if (file.size > maxSize) {
      toast.error('File is too large. Maximum size is 50MB.');
      return;
    }

    setUploadStatus('uploading');
    
    try {
      // Start the file upload directly without the extra promise wrapper
      const response = await uploadFile(file, (progressEvent) => {
        if (progressEvent.total) {
          const percentComplete = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setProgress(percentComplete);
        }
      });
      
      // Update UI state
      setProgress(100);
      setUploadStatus('processing');
      
      // Pass the file and response to the parent component
      if (response && response.jats_xml) {
        // If we have JATS XML, pass it to the parent component
        onFileUpload(file, response.id, response.jats_xml);
      } else if (response && response.id) {
        // Fallback to the original behavior
        onFileUpload(file, response.id);
      } else {
        throw new Error('Invalid response from server');
      }
    } catch (error) {
      console.error('Error uploading file:', error);
      setUploadStatus('error');
      toast.error(`Failed to upload file: ${error instanceof Error ? error.message : 'Unknown error'}`);
      
      // Reset after error
      setTimeout(() => {
        setUploadStatus('idle');
        setProgress(0);
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
      }, 3000);
    }
  };

  const acceptedFormats = ['.pdf', '.jpg', '.jpeg', '.png', '.docx', '.txt'];

  const renderUploadState = () => {
    switch (uploadStatus) {
      case 'uploading':
        return (
          <div className="space-y-4">
            <div className="w-24 h-24 mx-auto relative">
              <div className="w-full h-full rounded-full border-4 border-gray-200 flex items-center justify-center">
                <div className="text-blue-600">
                  <Loader2 className="h-8 w-8 animate-spin" />
                </div>
              </div>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-sm font-medium text-gray-700">{Math.round(progress)}%</span>
              </div>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <div 
                className="bg-blue-600 h-2.5 rounded-full transition-all duration-300" 
                style={{ width: `${progress}%` }}
              ></div>
            </div>
            <p className="text-sm text-gray-600">
              {progress < 90 ? 'Uploading your file...' : 'Processing your document...'}
            </p>
          </div>
        );

      case 'processing':
        return (
          <div className="space-y-4">
            <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
            <p className="text-lg font-medium text-gray-900">Processing your document</p>
            <p className="text-gray-600">This may take a few moments</p>
          </div>
        );

      case 'error':
        return (
          <div className="space-y-4 text-center">
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto">
              <X className="h-8 w-8 text-red-600" />
            </div>
            <p className="text-lg font-medium text-gray-900">Upload failed</p>
            <p className="text-gray-600">Please try again</p>
            <button
              onClick={() => {
                setUploadStatus('idle');
                setProgress(0);
                if (fileInputRef.current) {
                  fileInputRef.current.value = '';
                }
              }}
              className="mt-4 text-blue-600 hover:text-blue-800 text-sm font-medium"
            >
              Try again
            </button>
          </div>
        );

      case 'completed':
        return (
          <div className="space-y-4 text-center">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto">
              <Check className="h-8 w-8 text-green-600" />
            </div>
            <p className="text-lg font-medium text-gray-900">Upload complete</p>
            <p className="text-gray-600">Processing your document...</p>
          </div>
        );

      default:
        return (
          <div className="space-y-4">
            {filePreview ? (
              <div className="w-32 h-32 mx-auto overflow-hidden rounded-lg border border-gray-200">
                <img 
                  src={filePreview} 
                  alt="Preview" 
                  className="w-full h-full object-cover"
                />
              </div>
            ) : (
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto">
                <Upload className="h-8 w-8 text-blue-600" />
              </div>
            )}
            <div>
              <p className="text-lg font-medium text-gray-900 mb-2">
                {filePreview ? 'File selected' : 'Drag and drop your file here, or click to browse'}
              </p>
              {filePreview && (
                <p className="text-sm text-gray-600 mb-4 truncate max-w-xs mx-auto">
                  {fileInputRef.current?.files?.[0]?.name}
                </p>
              )}
              <button
                onClick={() => fileInputRef.current?.click()}
                className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors inline-flex items-center space-x-2"
              >
                <File className="h-5 w-5" />
                <span>{filePreview ? 'Choose Another File' : 'Choose File'}</span>
              </button>
            </div>
          </div>
        );
    }
  };

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
        } ${uploadStatus !== 'idle' ? 'pointer-events-none' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {renderUploadState()}
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept={acceptedFormats.join(',')}
        onChange={handleFileSelect}
        className="hidden"
        disabled={uploadStatus === 'uploading' || uploadStatus === 'processing'}
      />

      <div className="mt-6 text-center">
        <p className="text-sm text-gray-500">
          Maximum file size: 50MB. Supported formats: PDF, DOC, DOCX, JPG, PNG, TXT
        </p>
      </div>
    </div>
  );
};

export default FileUpload;