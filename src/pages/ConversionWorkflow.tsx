import React, { useState, useRef } from 'react';
import { ArrowLeft, Upload, FileText, Wand2, Download, Check, AlertCircle } from 'lucide-react';
import { Link } from 'react-router-dom';
import FileUpload from '../components/FileUpload';
import TextEditor from '../components/EditText';
import XMLEditor from '../components/XMLEditor';
import ExportOptions from '../components/ExportOptions';

type WorkflowStep = 'upload' | 'extract' | 'edit' | 'validate' | 'export';

const ConversionWorkflow: React.FC = () => {
  const [currentStep, setCurrentStep] = useState<WorkflowStep>('upload');
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [extractedText, setExtractedText] = useState('');
  const [editedText, setEditedText] = useState('');
  const [xmlContent, setXmlContent] = useState('');
  const [extractedImages, setExtractedImages] = useState<string[]>([]);
  const [jsonData, setJsonData] = useState<any[]>([]);

  const steps = [
    { id: 'upload', name: 'Upload', icon: Upload, description: 'Upload your document' },
    { id: 'extract', name: 'Extract', icon: FileText, description: 'Extract and preview text' },
    { id: 'edit', name: 'Edit', icon: Wand2, description: 'Edit and spell check' },
    { id: 'validate', name: 'Validate', icon: Check, description: 'XML validation' },
    { id: 'export', name: 'Export', icon: Download, description: 'Choose output format' }
  ];

  const getStepIndex = (step: WorkflowStep) => steps.findIndex(s => s.id === step);
  const currentStepIndex = getStepIndex(currentStep);

  const handleFileUpload = (file: File, extractedText: string, extractedImages: string[], jsonData: any[], uploadId?: string) => {
    setUploadedFile(file);
    setExtractedText(extractedText);
    setExtractedImages(extractedImages || []);
    setJsonData(jsonData || []);
    setCurrentStep('extract');
  };

  const handleTextEdit = (text: string) => {
    setEditedText(text);
  };

  const proceedToValidation = () => {
    // Generate proper JATS XML structure
    const jatsXml = generateJATSXML(uploadedFile?.name || 'Document', editedText, extractedImages, jsonData);
    setXmlContent(jatsXml);
    setCurrentStep('validate');
  };

  const generateJATSXML = (title: string, content: string, images: string[], structureData: any[]) => {
    const currentDate = new Date().toISOString().split('T')[0];
    
    let jatsContent = `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE article PUBLIC "-//NLM//DTD JATS (Z39.96) Journal Archiving and Interchange DTD v1.2 20190208//EN" "JATS-archivearticle1.dtd">
<article xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:mml="http://www.w3.org/1998/Math/MathML" article-type="research-article">
  <front>
    <article-meta>
      <title-group>
        <article-title>${escapeXml(title.replace(/\.[^/.]+$/, ''))}</article-title>
      </title-group>
      <pub-date pub-type="epub">
        <year>${new Date().getFullYear()}</year>
        <month>${new Date().getMonth() + 1}</month>
        <day>${new Date().getDate()}</day>
      </pub-date>
    </article-meta>
  </front>
  <body>`;

    // Process structured data to include images inline
    if (structureData && structureData.length > 0) {
      let figureCounter = 0;
      
      structureData.forEach((page, pageIndex) => {
        if (page.blocks && page.blocks.length > 0) {
          jatsContent += `
    <sec id="page${pageIndex + 1}">
      <title>Page ${pageIndex + 1}</title>`;
          
          // Sort blocks by Y position to maintain reading order
          const sortedBlocks = [...page.blocks].sort((a, b) => a.y - b.y);
          
          sortedBlocks.forEach((block) => {
            if (block.type === 'text' && block.content && block.content.trim()) {
              // Split text into paragraphs
              const paragraphs = block.content.split('\n\n').filter(p => p.trim());
              paragraphs.forEach(paragraph => {
                jatsContent += `
      <p>${escapeXml(paragraph.trim())}</p>`;
              });
            } else if (block.type === 'image' && block.path) {
              figureCounter++;
              jatsContent += `
      <fig id="fig${figureCounter}">
        <label>Figure ${figureCounter}</label>
        <caption>
          <p>Extracted figure from page ${pageIndex + 1}</p>
        </caption>
        <graphic xlink:href="http://localhost:8000/static/${block.path.replace('static/', '')}" />
      </fig>`;
            } else if (block.type === 'formula' && block.content) {
              figureCounter++;
              jatsContent += `
      <disp-formula id="formula${figureCounter}">
        <label>Formula ${figureCounter}</label>
        <tex-math>${escapeXml(block.content)}</tex-math>
      </disp-formula>`;
            }
          });
          
          jatsContent += `
    </sec>`;
        }
      });
    } else {
      // Fallback to original method if no structured data
      const sections = content.split(/=== Page \d+ ===/g).filter(section => section.trim());
      
      sections.forEach((section, index) => {
        if (section.trim()) {
          const paragraphs = section.split('\n\n').filter(p => p.trim());
          jatsContent += `
    <sec id="sec${index + 1}">
      <title>Section ${index + 1}</title>`;
          
          paragraphs.forEach(paragraph => {
            if (paragraph.trim()) {
              jatsContent += `
      <p>${escapeXml(paragraph.trim())}</p>`;
            }
          });
          
          jatsContent += `
    </sec>`;
        }
      });

      // Add figures for images if no structured data
      if (images.length > 0) {
        jatsContent += `
    <sec id="figures">
      <title>Figures</title>`;
        
        images.forEach((image, index) => {
          jatsContent += `
      <fig id="fig${index + 1}">
        <label>Figure ${index + 1}</label>
        <caption>
          <p>Extracted figure from document</p>
        </caption>
        <graphic xlink:href="http://localhost:8000/${image}" />
      </fig>`;
        });
        
        jatsContent += `
    </sec>`;
      }
    }

    jatsContent += `
  </body>
</article>`;

    return jatsContent;
  };

  const escapeXml = (text: string) => {
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
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
              {extractedImages.length > 0 && (
                <div className="mt-6">
                  <h4 className="font-medium text-gray-900 mb-2">Extracted Images ({extractedImages.length})</h4>
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                    {extractedImages.map((image, index) => (
                      <div key={index} className="border rounded-lg p-2">
                        <img 
                          src={`http://localhost:8000/${image}`} 
                          alt={`Extracted image ${index + 1}`}
                          className="w-full h-24 object-cover rounded"
                          onError={(e) => {
                            (e.target as HTMLImageElement).src = '/placeholder-image.png';
                          }}
                        />
                        <p className="text-xs text-gray-500 mt-1">Image {index + 1}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
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