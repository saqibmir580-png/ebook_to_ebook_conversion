import React, { useState } from 'react';
import { Download, FileText, Globe, BookOpen, File, CheckCircle, Settings } from 'lucide-react';

interface ExportOptionsProps {
  xmlContent: string;
  fileName: string;
}

interface ExportFormat {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  extension: string;
  popular?: boolean;
}

const ExportOptions: React.FC<ExportOptionsProps> = ({ xmlContent, fileName }) => {
  const [selectedFormat, setSelectedFormat] = useState<string>('epub');
  const [isExporting, setIsExporting] = useState(false);
  const [exportComplete, setExportComplete] = useState(false);
  const [customSettings, setCustomSettings] = useState({
    includeImages: true,
    optimizeForMobile: true,
    includeTableOfContents: true,
    compressionLevel: 'medium'
  });

  const exportFormats: ExportFormat[] = [
    {
      id: 'epub',
      name: 'EPUB',
      description: 'Standard e-book format compatible with most e-readers',
      icon: <BookOpen className="h-6 w-6" />,
      extension: '.epub',
      popular: true
    },
    {
      id: 'html',
      name: 'HTML',
      description: 'Web-ready HTML format with CSS styling',
      icon: <Globe className="h-6 w-6" />,
      extension: '.html',
      popular: true
    },
    {
      id: 'pdf',
      name: 'PDF',
      description: 'Portable document format for printing and sharing',
      icon: <FileText className="h-6 w-6" />,
      extension: '.pdf'
    },
    {
      id: 'mobi',
      name: 'MOBI',
      description: 'Amazon Kindle compatible format',
      icon: <BookOpen className="h-6 w-6" />,
      extension: '.mobi'
    },
    {
      id: 'docx',
      name: 'DOCX',
      description: 'Microsoft Word document format',
      icon: <File className="h-6 w-6" />,
      extension: '.docx'
    },
    {
      id: 'txt',
      name: 'Plain Text',
      description: 'Simple text format without formatting',
      icon: <FileText className="h-6 w-6" />,
      extension: '.txt'
    }
  ];

  const handleExport = () => {
    setIsExporting(true);
    
    // Simulate export process
    setTimeout(() => {
      setIsExporting(false);
      setExportComplete(true);
      
      // Create and download file
      const selectedFormatData = exportFormats.find(f => f.id === selectedFormat);
      const blob = new Blob([xmlContent], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${fileName.replace(/\.[^/.]+$/, '')}${selectedFormatData?.extension || '.txt'}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }, 3000);
  };

  if (exportComplete) {
    return (
      <div className="p-6 text-center space-y-6">
        <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto">
          <CheckCircle className="h-10 w-10 text-green-600" />
        </div>
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Export Complete!</h2>
          <p className="text-gray-600">
            Your e-book has been successfully converted and downloaded.
          </p>
        </div>
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <p className="text-green-800 font-medium">
            File: {fileName.replace(/\.[^/.]+$/, '')}{exportFormats.find(f => f.id === selectedFormat)?.extension}
          </p>
          <p className="text-green-700 text-sm mt-1">
            Check your downloads folder for the converted file.
          </p>
        </div>
        <div className="flex justify-center space-x-4">
          <button
            onClick={() => window.location.href = '/dashboard'}
            className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Back to Dashboard
          </button>
          <button
            onClick={() => {
              setExportComplete(false);
              setSelectedFormat('epub');
            }}
            className="border border-gray-300 text-gray-700 px-6 py-3 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Export Another Format
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Choose Export Format</h2>
        <p className="text-gray-600">
          Select your preferred output format and customize export settings
        </p>
      </div>

      {/* Format Selection */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {exportFormats.map((format) => (
          <div
            key={format.id}
            className={`relative border-2 rounded-lg p-4 cursor-pointer transition-all hover:shadow-md ${
              selectedFormat === format.id
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
            onClick={() => setSelectedFormat(format.id)}
          >
            {format.popular && (
              <div className="absolute -top-2 -right-2 bg-blue-600 text-white text-xs px-2 py-1 rounded-full">
                Popular
              </div>
            )}
            <div className="flex items-center space-x-3 mb-2">
              <div className={`p-2 rounded-lg ${
                selectedFormat === format.id ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-600'
              }`}>
                {format.icon}
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">{format.name}</h3>
                <p className="text-sm text-gray-500">{format.extension}</p>
              </div>
            </div>
            <p className="text-sm text-gray-600">{format.description}</p>
          </div>
        ))}
      </div>

      {/* Export Settings */}
      <div className="bg-gray-50 rounded-lg p-6">
        <div className="flex items-center space-x-2 mb-4">
          <Settings className="h-5 w-5 text-gray-600" />
          <h3 className="font-semibold text-gray-900">Export Settings</h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={customSettings.includeImages}
              onChange={(e) => setCustomSettings(prev => ({ ...prev, includeImages: e.target.checked }))}
              className="rounded"
            />
            <span className="text-sm text-gray-700">Include images</span>
          </label>
          
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={customSettings.optimizeForMobile}
              onChange={(e) => setCustomSettings(prev => ({ ...prev, optimizeForMobile: e.target.checked }))}
              className="rounded"
            />
            <span className="text-sm text-gray-700">Optimize for mobile</span>
          </label>
          
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={customSettings.includeTableOfContents}
              onChange={(e) => setCustomSettings(prev => ({ ...prev, includeTableOfContents: e.target.checked }))}
              className="rounded"
            />
            <span className="text-sm text-gray-700">Include table of contents</span>
          </label>
          
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-700">Compression:</span>
            <select
              value={customSettings.compressionLevel}
              onChange={(e) => setCustomSettings(prev => ({ ...prev, compressionLevel: e.target.value }))}
              className="text-sm border border-gray-300 rounded px-2 py-1"
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </div>
        </div>
      </div>

      {/* File Preview */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h3 className="font-semibold text-gray-900 mb-2">Export Preview</h3>
        <div className="flex items-center justify-between text-sm text-gray-600">
          <span>File name: {fileName.replace(/\.[^/.]+$/, '')}{exportFormats.find(f => f.id === selectedFormat)?.extension}</span>
          <span>Estimated size: ~{Math.round(xmlContent.length / 1024)}KB</span>
        </div>
      </div>

      {/* Export Button */}
      <div className="flex justify-center">
        <button
          onClick={handleExport}
          disabled={isExporting}
          className="bg-gradient-to-r from-green-600 to-emerald-600 text-white px-8 py-4 rounded-lg hover:from-green-700 hover:to-emerald-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-3 text-lg font-semibold"
        >
          {isExporting ? (
            <>
              <div className="w-6 h-6 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              <span>Exporting...</span>
            </>
          ) : (
            <>
              <Download className="h-6 w-6" />
              <span>Export E-Book</span>
            </>
          )}
        </button>
      </div>

      {isExporting && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-center">
          <p className="text-blue-800 font-medium">Converting to {exportFormats.find(f => f.id === selectedFormat)?.name}...</p>
          <p className="text-blue-700 text-sm mt-1">This may take a few moments depending on file size.</p>
        </div>
      )}
    </div>
  );
};

export default ExportOptions;