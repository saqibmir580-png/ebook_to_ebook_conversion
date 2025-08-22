import React, { useState, useEffect } from 'react';
import { Wand2, AlertCircle, CheckCircle, RotateCcw } from 'lucide-react';
import formulaConverter from '../utils/formulaConverter';

// Add CSS for mathematical fonts
const mathFontStyles = `
  @import url('https://fonts.googleapis.com/css2?family=STIX+Two+Math&display=swap');
  
  .math-text {
    font-family: 'STIX Two Math', 'Times New Roman', 'Cambria Math', serif;
    font-feature-settings: 'kern' 1, 'liga' 1, 'calt' 1;
    font-variant-numeric: normal;
    line-height: 1.6;
  }
  
  .formula-highlight {
    background-color: #f0f9ff;
    padding: 2px 4px;
    border-radius: 3px;
    border-left: 3px solid #3b82f6;
    display: inline-block;
    margin: 1px 0;
  }
`;

// Inject styles into document head
if (typeof document !== 'undefined') {
  const styleElement = document.createElement('style');
  styleElement.textContent = mathFontStyles;
  document.head.appendChild(styleElement);
}

interface TextEditorProps {
  initialText: string;
  onTextChange: (text: string) => void;
  onNext: () => void;
}

interface SpellingError {
  word: string;
  position: number;
  suggestions: string[];
}

const TextEditor: React.FC<TextEditorProps> = ({ initialText, onTextChange, onNext }) => {
  const [text, setText] = useState(initialText);
  const [isSpellChecking, setIsSpellChecking] = useState(false);
  const [spellingErrors, setSpellingErrors] = useState<SpellingError[]>([]);
  const [selectedError, setSelectedError] = useState<SpellingError | null>(null);

  const convertFormulaSymbols = (inputText: string): string => {
    if (!inputText) return inputText;
    
    let convertedText = inputText;
    
    // First, apply the comprehensive formula converter to any LaTeX patterns
    convertedText = formulaConverter.convertToReadable(convertedText);
    
    // Then apply specific diamond symbol mappings for OCR artifacts
    const symbolMappings = {
      '◆': '', // Remove diamond symbols
      '| z |': '|z|',
      '| z d | |': '|εz|',
      '◆ L |': 'ΔL',
      'd dl ◆': 'dL/dl',
      '◆ ◆': '',
      '( ) ( )': '',
      'exp [ ]': 'exp',
      '◆ | z ◆ ◆ | L z ( ) ( ) 0 exp [ ] ◆': '|εz| = L₀ exp(εz)',
      '( ) ( ) ( ) ◆ ◆': 'θ',
      '◆ L': 'ΔL',
      '0 exp [ L(z) ]': '₀ exp[L(z)]'
    };
    
    // Apply symbol mappings
    for (const [symbol, replacement] of Object.entries(symbolMappings)) {
      convertedText = convertedText.replace(new RegExp(symbol.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'), replacement);
    }
    
    // Clean up extra spaces
    convertedText = convertedText.replace(/\s+/g, ' ');
    convertedText = convertedText.replace(/\n\s*\n/g, '\n\n');
    
    return convertedText.trim();
  };

  useEffect(() => {
    onTextChange(text);
  }, [text, onTextChange]);

  const runSpellCheck = () => {
    setIsSpellChecking(true);
    
    // Simulate AI spell checking
    setTimeout(() => {
      const commonMisspellings = [
        { word: 'recieve', suggestions: ['receive'] },
        { word: 'seperate', suggestions: ['separate'] },
        { word: 'occured', suggestions: ['occurred'] },
        { word: 'definately', suggestions: ['definitely'] },
        { word: 'accomodate', suggestions: ['accommodate'] },
        { word: 'neccessary', suggestions: ['necessary'] }
      ];

      const errors: SpellingError[] = [];
      commonMisspellings.forEach(misspelling => {
        const regex = new RegExp(`\\b${misspelling.word}\\b`, 'gi');
        let match;
        while ((match = regex.exec(text)) !== null) {
          errors.push({
            word: misspelling.word,
            position: match.index,
            suggestions: misspelling.suggestions
          });
        }
      });

      setSpellingErrors(errors);
      setIsSpellChecking(false);
    }, 2000);
  };

  const applySuggestion = (error: SpellingError, suggestion: string) => {
    const newText = text.substring(0, error.position) + 
                   suggestion + 
                   text.substring(error.position + error.word.length);
    setText(newText);
    
    // Remove the corrected error
    setSpellingErrors(prev => prev.filter(e => e !== error));
    setSelectedError(null);
  };

  const highlightErrors = (text: string) => {
    if (spellingErrors.length === 0) return text;

    let highlightedText = text;
    spellingErrors.forEach(error => {
      const regex = new RegExp(`\\b${error.word}\\b`, 'gi');
      highlightedText = highlightedText.replace(regex, `<mark class="bg-red-200 cursor-pointer">${error.word}</mark>`);
    });

    return highlightedText;
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Edit and Validate Text</h2>
          <p className="text-gray-600">Review and edit the extracted text, then run AI spell checking</p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={runSpellCheck}
            disabled={isSpellChecking}
            className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50 flex items-center space-x-2"
          >
            {isSpellChecking ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            ) : (
              <Wand2 className="h-4 w-4" />
            )}
            <span>{isSpellChecking ? 'Checking...' : 'AI Spell Check'}</span>
          </button>
          <button
            onClick={() => setText(initialText)}
            className="text-gray-600 hover:text-gray-800 transition-colors flex items-center space-x-1"
          >
            <RotateCcw className="h-4 w-4" />
            <span>Reset</span>
          </button>
        </div>
      </div>

      {spellingErrors.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-2">
            <AlertCircle className="h-5 w-5 text-yellow-600" />
            <span className="font-medium text-yellow-800">
              {spellingErrors.length} spelling error{spellingErrors.length !== 1 ? 's' : ''} found
            </span>
          </div>
          <p className="text-yellow-700 text-sm">
            Click on highlighted words in the text to see suggestions
          </p>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Original Text */}
        <div>
          <h3 className="font-semibold text-gray-900 mb-3">Original Extracted Text</h3>
          <div className="bg-gray-50 p-4 rounded-lg h-96 overflow-y-auto">
            <div 
              className="text-sm text-gray-700 whitespace-pre-wrap math-text"
            >
              {convertFormulaSymbols(initialText)}
            </div>
          </div>
        </div>

        {/* Editable Text */}
        <div>
          <h3 className="font-semibold text-gray-900 mb-3">Edited Text</h3>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            className="w-full h-96 p-4 border border-gray-200 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent math-text"
            style={{ fontSize: '14px' }}
            placeholder="Edit your text here..."
          />
        </div>
      </div>

      {/* Spelling Suggestions */}
      {selectedError && (
        <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
          <h4 className="font-medium text-gray-900 mb-2">
            Suggestions for "{selectedError.word}":
          </h4>
          <div className="flex flex-wrap gap-2">
            {selectedError.suggestions.map((suggestion, index) => (
              <button
                key={index}
                onClick={() => applySuggestion(selectedError, suggestion)}
                className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm hover:bg-blue-200 transition-colors"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white p-4 rounded-lg border border-gray-200 text-center">
          <div className="text-2xl font-bold text-gray-900">{text.split(' ').length}</div>
          <div className="text-sm text-gray-600">Words</div>
        </div>
        <div className="bg-white p-4 rounded-lg border border-gray-200 text-center">
          <div className="text-2xl font-bold text-gray-900">{text.length}</div>
          <div className="text-sm text-gray-600">Characters</div>
        </div>
        <div className="bg-white p-4 rounded-lg border border-gray-200 text-center">
          <div className={`text-2xl font-bold ${spellingErrors.length > 0 ? 'text-red-600' : 'text-green-600'}`}>
            {spellingErrors.length}
          </div>
          <div className="text-sm text-gray-600">Errors</div>
        </div>
      </div>

      <div className="flex justify-end">
        <button
          onClick={onNext}
          className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2"
        >
          <span>Continue to XML Validation</span>
          <CheckCircle className="h-5 w-5" />
        </button>
      </div>
    </div>
  );
};

export default TextEditor;