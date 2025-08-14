import React, { useState } from 'react';
import { ArrowLeft, Upload, FileText, Wand2, Download, Check } from 'lucide-react';
import { Link } from 'react-router-dom';
import { toast } from 'react-toastify';
import FileUpload from '../components/FileUpload';
import TextEditor from '../components/TextEditor';
import XMLEditor from '../components/XMLEditor';
import ExportOptions from '../components/ExportOptions';
import { getUpload } from '../services/api';

interface ExtractedImage {
  url: string;
  alt?: string;
}

interface ExtractedContent {
  text: string;
  images: ExtractedImage[];
}

// Using the same interface as in api.ts
import { UploadResponse } from '../services/api';

type WorkflowStep = 'upload' | 'extract' | 'edit' | 'validate' | 'export';

const ConversionWorkflow: React.FC = () => {
  const [currentStep, setCurrentStep] = useState<WorkflowStep>('upload');
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [extractedContent, setExtractedContent] = useState<ExtractedContent>({ 
    text: '', 
    images: [] 
  });
  const [editedText, setEditedText] = useState('');
  const [xmlContent, setXmlContent] = useState('');
  const [processingStatus, setProcessingStatus] = useState('');

  const steps = [
    { id: 'upload', name: 'Upload', icon: Upload, description: 'Upload your document' },
    { id: 'extract', name: 'Extract', icon: FileText, description: 'Extract and preview text' },
    { id: 'edit', name: 'Edit', icon: Wand2, description: 'Edit and spell check' },
    { id: 'validate', name: 'Validate', icon: Check, description: 'XML validation' },
    { id: 'export', name: 'Export', icon: Download, description: 'Choose output format' }
  ];

  const getStepIndex = (step: WorkflowStep) => steps.findIndex(s => s.id === step);
  const currentStepIndex = getStepIndex(currentStep);

  const handleFileUpload = async (file: File, uploadId?: string, jatsXml?: string) => {
    setUploadedFile(file);
    
    if (jatsXml) {
      // If we have JATS XML, use it directly
      setXmlContent(jatsXml);
      setProcessingStatus('Processing JATS XML...');
      
      // Extract text content from JATS XML for editing
      try {
        // Simple extraction of text content from JATS XML
        const parser = new DOMParser();
        const xmlDoc = parser.parseFromString(jatsXml, 'text/xml');
        const textContent = Array.from(xmlDoc.getElementsByTagName('p'))
          .map(p => p.textContent)
          .join('\n\n');
          
        setExtractedContent({
          text: textContent || 'No text content extracted from JATS XML.',
          images: [] // You can extract images from JATS XML if needed
        });
        setEditedText(textContent);
        setCurrentStep('extract');
      } catch (error) {
        console.error('Error parsing JATS XML:', error);
        toast.error('Error processing JATS XML content');
        setCurrentStep('upload');
      } finally {
        setProcessingStatus('');
      }
    } else if (uploadId) {
      // Fallback to the original behavior if no JATS XML is provided
      setProcessingStatus('Uploading file...');
      await checkUploadStatus(uploadId);
    }
  };

  const checkUploadStatus = async (id: string): Promise<void> => {
    try {
      setProcessingStatus('Processing your document...');
      
      const response = await getUpload(id);
      
      // Log the full response for debugging
      console.log('Upload status response:', response);
      
      // Map the response status to our workflow states
      if (response.status === 'completed' || response.status === 'processed' || response.status === 'COMPLETED') {
        // Try to get JATS XML if available
        if (response.jats_xml) {
          setXmlContent(response.jats_xml);
          
          // Extract text content from JATS XML for editing
          try {
            const parser = new DOMParser();
            const xmlDoc = parser.parseFromString(response.jats_xml, 'text/xml');
            const textContent = Array.from(xmlDoc.getElementsByTagName('p'))
              .map(p => p.textContent)
              .join('\n\n');
              
            setExtractedContent({
              text: textContent || 'No text content extracted from JATS XML.',
              images: []
            });
            setEditedText(textContent);
          } catch (error) {
            console.error('Error parsing JATS XML:', error);
            // Fall back to extracted text if available
            const fallbackText = response.extracted_text || 'No text content available.';
            setExtractedContent({
              text: fallbackText,
              images: []
            });
            setEditedText(fallbackText);
          }
        } else {
          // Fallback to extracted text if no JATS XML is available
          const extractedText = response.extracted_text || 'No text content extracted.';
          const extractedImages: ExtractedImage[] = response.extracted_images?.map((img, index) => ({
            url: img.url,
            alt: img.alt || `Extracted image ${index + 1}`
          })) || [];
          
          setExtractedContent({
            text: extractedText,
            images: extractedImages
          });
          setEditedText(extractedText);
        }
        
        setCurrentStep('extract');
      } 
      else if (response.status === 'processing' || response.status === 'pending') {
        // Check again after a delay with exponential backoff
        const delay = Math.min(2000 * (1 + Math.random()), 10000); // Random delay between 2-10 seconds
        console.log(`Upload still processing, checking again in ${delay}ms...`);
        setTimeout(() => checkUploadStatus(id), delay);
      }
      else if (response.status === 'failed' || response.status === 'FAILED') {
        const errorMsg = response.error_message || 'File processing failed';
        console.error('Upload processing failed:', errorMsg);
        throw new Error(errorMsg);
      }
      else if (response.status === 'processing' || response.status === 'pending' || response.status === 'PROCESSING' || response.status === 'PENDING') {
        // Check again after a delay with exponential backoff
        const delay = Math.min(2000 * (1 + Math.random()), 10000); // Random delay between 2-10 seconds
        console.log(`Upload still processing (${response.status}), checking again in ${delay}ms...`);
        setTimeout(() => checkUploadStatus(id), delay);
      }
      else {
        // Handle any error or unknown status
        console.warn('Unknown upload status:', response.status);
        throw new Error(`Unexpected status: ${response.status}`);
      }
    } catch (error) {
      console.error('Error checking upload status:', error);
      toast.error(`Error processing file: ${error instanceof Error ? error.message : 'Unknown error'}`);
      setCurrentStep('upload');
    } finally {
      setProcessingStatus('');
    }
  };

  const handleTextEdit = (text: string) => {
    setEditedText(text);
  };

  const proceedToValidation = () => {
    // Convert text to basic XML structure
    const xmlStructure = `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE book PUBLIC "-//OASIS//DTD DocBook XML V4.5//EN" 
"http://www.oasis-open.org/docbook/xml/4.5/docbookx.dtd">
<book>
  <title>${uploadedFile?.name || 'Document'}</title>
  <chapter>
    <title>Chapter 1</title>
    <para>${editedText.replace(/\n\n/g, '</para>\n    <para>')}</para>
  </chapter>
</book>`;
    setXmlContent(xmlStructure);
    setCurrentStep('validate');
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 'upload':
        return <FileUpload onFileUpload={handleFileUpload} />;
      
      case 'extract':
        return (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-lg font-semibold mb-4">Text Extraction Complete</h3>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Left side: Original Document */}
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Original Document</h4>
                  <div className="bg-gray-100 p-4 rounded-lg h-96 overflow-auto">
                    {uploadedFile?.type.startsWith('image/') ? (
                      <img 
                        src={URL.createObjectURL(uploadedFile)} 
                        alt="Uploaded document"
                        className="max-w-full h-auto max-h-80 mx-auto"
                      />
                    ) : (
                      <div className="h-full flex flex-col items-center justify-center text-center text-gray-500">
                        <FileText className="h-12 w-12 mx-auto mb-2" />
                        <p className="truncate max-w-full">{uploadedFile?.name}</p>
                        <p className="text-sm mt-2">
                          {uploadedFile?.type === 'application/pdf' 
                            ? 'PDF document' 
                            : 'Document preview not available'}
                        </p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Right side: Extracted Content */}
                <div className="space-y-4">
                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">Extracted Text</h4>
                    <div className="border border-gray-200 rounded-lg p-4 h-64 overflow-auto bg-gray-50">
                      {extractedContent.text || 'No text content was extracted from the document.'}
                    </div>
                  </div>

                  {extractedContent.images.length > 0 && (
                    <div>
                      <h4 className="font-medium text-gray-900 mb-2">Extracted Images</h4>
                      <div className="grid grid-cols-2 gap-2 max-h-40 overflow-y-auto p-2 border border-gray-200 rounded-lg">
                        {extractedContent.images.map((img, index) => (
                          <div key={index} className="relative group">
                            <img 
                              src={img.url} 
                              alt={img.alt || `Extracted image ${index + 1}`}
                              className="w-full h-20 object-cover rounded border border-gray-200"
                            />
                            <div className="absolute inset-0 bg-black bg-opacity-50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                              <a 
                                href={img.url} 
                                target="_blank" 
                                rel="noopener noreferrer"
                                className="text-white text-sm bg-blue-600 rounded p-1"
                                onClick={(e) => e.stopPropagation()}
                              >
                                View
                              </a>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
              
              <div className="mt-6 flex justify-end space-x-3">
                <button
                  onClick={() => setCurrentStep('upload')}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  Back
                </button>
                <button
                  onClick={() => {
                    setEditedText(extractedContent.text);
                    setCurrentStep('edit');
                  }}
                  className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
                  disabled={!extractedContent.text}
                >
                  Continue to Editing
                </button>
              </div>
            </div>
          </div>
        );
      
      case 'edit':
        return (
          <TextEditor
            initialText={extractedContent.text}
            onTextChange={handleTextEdit}
            onNext={proceedToValidation}
          />
        );
      
      case 'validate':
        return (
          <XMLEditor
            content={xmlContent}
            onContentChange={setXmlContent}
            onNext={() => setCurrentStep('export')}
          />
        );
      
      case 'export':
        return <ExportOptions xmlContent={xmlContent} fileName={uploadedFile?.name || 'document'} />;
      
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center space-x-4 mb-4">
            <Link
              to="/dashboard"
              className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
            >
              <ArrowLeft className="h-5 w-5" />
            </Link>
            <h1 className="text-3xl font-bold text-gray-900">E-Book Conversion</h1>
          </div>
        </div>

        {/* Progress Steps */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            {steps.map((step, index) => {
              const isActive = index === currentStepIndex;
              const isCompleted = index < currentStepIndex;
              const Icon = step.icon;

              return (
                <div key={step.id} className="flex items-center">
                  <div className="flex flex-col items-center">
                    <div
                      className={`w-12 h-12 rounded-full flex items-center justify-center border-2 transition-all ${
                        isActive
                          ? 'bg-blue-600 border-blue-600 text-white'
                          : isCompleted
                          ? 'bg-green-600 border-green-600 text-white'
                          : 'bg-white border-gray-300 text-gray-400'
                      }`}
                    >
                      {isCompleted ? (
                        <Check className="h-6 w-6" />
                      ) : (
                        <Icon className="h-6 w-6" />
                      )}
                    </div>
                    <div className="mt-2 text-center">
                      <p className={`text-sm font-medium ${
                        isActive ? 'text-blue-600' : isCompleted ? 'text-green-600' : 'text-gray-500'
                      }`}>
                        {step.name}
                      </p>
                      <p className="text-xs text-gray-400">{step.description}</p>
                    </div>
                  </div>
                  
                  {index < steps.length - 1 && (
                    <div
                      className={`flex-1 h-0.5 mx-4 ${
                        index < currentStepIndex ? 'bg-green-600' : 'bg-gray-300'
                      }`}
                    />
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Step Content */}
        <div className="bg-white rounded-lg shadow-sm min-h-96">
          {renderStepContent()}
        </div>
      </div>
    </div>
  );
};

export default ConversionWorkflow;