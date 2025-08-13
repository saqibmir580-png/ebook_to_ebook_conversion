import React, { useState, useRef } from 'react';
import { ArrowLeft, Upload, FileText, Wand2, Download, Check, AlertCircle } from 'lucide-react';
import { Link } from 'react-router-dom';
import FileUpload from '../components/FileUpload';
import TextEditor from '../components/TextEditor';
import XMLEditor from '../components/XMLEditor';
import ExportOptions from '../components/ExportOptions';

type WorkflowStep = 'upload' | 'extract' | 'edit' | 'validate' | 'export';

const ConversionWorkflow: React.FC = () => {
  const [currentStep, setCurrentStep] = useState<WorkflowStep>('upload');
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [extractedText, setExtractedText] = useState('');
  const [editedText, setEditedText] = useState('');
  const [xmlContent, setXmlContent] = useState('');

  const steps = [
    { id: 'upload', name: 'Upload', icon: Upload, description: 'Upload your document' },
    { id: 'extract', name: 'Extract', icon: FileText, description: 'Extract and preview text' },
    { id: 'edit', name: 'Edit', icon: Wand2, description: 'Edit and spell check' },
    { id: 'validate', name: 'Validate', icon: Check, description: 'XML validation' },
    { id: 'export', name: 'Export', icon: Download, description: 'Choose output format' }
  ];

  const getStepIndex = (step: WorkflowStep) => steps.findIndex(s => s.id === step);
  const currentStepIndex = getStepIndex(currentStep);

  const handleFileUpload = (file: File) => {
    setUploadedFile(file);
    // Simulate text extraction
    setTimeout(() => {
      setExtractedText(`This is extracted text from ${file.name}. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.

Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Here are some intentional mispellings for testing: recieve, seperate, occured, definately.`);
      setCurrentStep('extract');
    }, 2000);
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
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Original Document</h4>
                  <div className="bg-gray-100 p-4 rounded-lg h-64 flex items-center justify-center">
                    <div className="text-center text-gray-500">
                      <FileText className="h-12 w-12 mx-auto mb-2" />
                      <p>{uploadedFile?.name}</p>
                      <p className="text-sm">Preview not available</p>
                    </div>
                  </div>
                </div>
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Extracted Text</h4>
                  <textarea
                    value={extractedText}
                    readOnly
                    className="w-full h-64 p-4 border border-gray-200 rounded-lg bg-gray-50 text-sm resize-none"
                  />
                </div>
              </div>
              <div className="mt-6 flex justify-end">
                <button
                  onClick={() => {
                    setEditedText(extractedText);
                    setCurrentStep('edit');
                  }}
                  className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
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
            initialText={extractedText}
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