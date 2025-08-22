import React, { useState, useEffect } from 'react';
import { Wand2, RotateCcw, Edit } from 'lucide-react';

interface EditTextProps {
  initialText: string;
  onTextChange: (newText: string) => void;
  onNext: () => void;
}

const EditText: React.FC<EditTextProps> = ({ initialText, onTextChange, onNext }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [currentText, setCurrentText] = useState(initialText);

  // Update internal state when initialText changes
  useEffect(() => {
    setCurrentText(initialText);
  }, [initialText]);

  const handleReset = () => {
    setCurrentText(initialText);
    onTextChange(initialText);
  };

  const handleSpellCheck = () => {
    // Placeholder for AI spell check functionality
    console.log('AI Spell Check clicked');
  };

  const handleTextChange = (newText: string) => {
    setCurrentText(newText);
    onTextChange(newText);
  };

  const toggleEditing = () => {
    setIsEditing(!isEditing);
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Edit and Validate Text</h2>
          <p className="text-gray-600">Review and edit the extracted text, then run AI spell checking</p>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={toggleEditing}
            className={`text-white px-4 py-2 rounded-lg transition-colors inline-flex items-center space-x-2 ${isEditing ? 'bg-red-500 hover:bg-red-600' : 'bg-blue-600 hover:bg-blue-700'}`}
          >
            <Edit className="h-5 w-5" />
            <span>{isEditing ? 'Lock Text' : 'Edit Text'}</span>
          </button>
          <button
            onClick={handleSpellCheck}
            className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors inline-flex items-center space-x-2"
          >
            <Wand2 className="h-5 w-5" />
            <span>AI Spell Check</span>
          </button>
          <button
            onClick={handleReset}
            className="text-gray-500 hover:text-gray-700 transition-colors inline-flex items-center space-x-2 p-2"
          >
            <RotateCcw className="h-5 w-5" />
            <span>Reset</span>
          </button>
        </div>
      </div>

      <div>
        <h3 className="font-semibold text-gray-900 mb-2">Extracted Text</h3>
        <textarea
          value={currentText}
          readOnly={!isEditing}
          onChange={(e) => handleTextChange(e.target.value)}
          className={`w-full h-96 p-4 border rounded-lg text-sm resize-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
            !isEditing ? 'bg-gray-50 border-gray-200' : 'border-gray-300'
          }`}
        />
      </div>

      <div className="mt-6 flex justify-end">
        <button
          onClick={onNext}
          className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
        >
          Continue to Validation
        </button>
      </div>
    </div>
  );
};

export default EditText;
