import React, { useState, useEffect } from 'react';
import { CheckCircle, AlertTriangle, Code, Eye, Settings } from 'lucide-react';

interface XMLEditorProps {
  content: string;
  onContentChange: (content: string) => void;
  onNext: () => void;
}

interface ValidationError {
  line: number;
  column: number;
  message: string;
  type: 'error' | 'warning';
}

const XMLEditor: React.FC<XMLEditorProps> = ({ content, onContentChange, onNext }) => {
  const [xmlContent, setXmlContent] = useState(content);
  const [isValidating, setIsValidating] = useState(false);
  const [validationErrors, setValidationErrors] = useState<ValidationError[]>([]);
  const [viewMode, setViewMode] = useState<'code' | 'preview'>('code');
  const [dtdRules, setDtdRules] = useState(true);
  const [entRules, setEntRules] = useState(true);

  useEffect(() => {
    onContentChange(xmlContent);
  }, [xmlContent, onContentChange]);

  const validateXML = () => {
    setIsValidating(true);
    
    // Simulate XML validation with DTD and ENT rules
    setTimeout(() => {
      const errors: ValidationError[] = [];
      
      // Basic XML structure validation
      if (!xmlContent.includes('<?xml')) {
        errors.push({
          line: 1,
          column: 1,
          message: 'Missing XML declaration',
          type: 'error'
        });
      }

      if (!xmlContent.includes('<!DOCTYPE')) {
        errors.push({
          line: 2,
          column: 1,
          message: 'Missing DOCTYPE declaration',
          type: 'warning'
        });
      }

      // Check for unclosed tags
      const openTags = xmlContent.match(/<[^/][^>]*>/g) || [];
      const closeTags = xmlContent.match(/<\/[^>]*>/g) || [];
      
      if (openTags.length !== closeTags.length + 1) { // +1 for self-closing tags
        errors.push({
          line: 10,
          column: 5,
          message: 'Unclosed XML tag detected',
          type: 'error'
        });
      }

      // DTD validation simulation
      if (dtdRules) {
        if (!xmlContent.includes('<title>')) {
          errors.push({
            line: 5,
            column: 3,
            message: 'Required element "title" is missing according to DTD',
            type: 'error'
          });
        }
      }

      // ENT rules validation simulation
      if (entRules) {
        const entityPattern = /&[a-zA-Z][a-zA-Z0-9]*;/g;
        const entities = xmlContent.match(entityPattern);
        if (entities) {
          entities.forEach((entity, index) => {
            if (!['&lt;', '&gt;', '&amp;', '&quot;', '&apos;'].includes(entity)) {
              errors.push({
                line: 8 + index,
                column: 10,
                message: `Undefined entity "${entity}" - not declared in ENT rules`,
                type: 'warning'
              });
            }
          });
        }
      }

      setValidationErrors(errors);
      setIsValidating(false);
    }, 2000);
  };

  const getLineNumbers = () => {
    const lines = xmlContent.split('\n');
    return lines.map((_, index) => index + 1);
  };

  const renderPreview = () => {
    try {
      // Enhanced XML to HTML preview with original PDF styling
      let preview = xmlContent
        .replace(/<\?xml[^>]*\?>/g, '')
        .replace(/<!DOCTYPE[^>]*>/g, '')
        .replace(/<article[^>]*>/g, '<div class="article" style="max-width: 800px; margin: 0 auto; font-family: Arial, sans-serif; line-height: 1.6; background: white; padding: 40px;">')
        .replace(/<\/article>/g, '</div>')
        
        // Journal header styling
        .replace(/<journal-meta>([\s\S]*?)<\/journal-meta>/g, (match, content) => {
          const titleMatch = content.match(/<journal-title>(.*?)<\/journal-title>/);
          const issnMatch = content.match(/<issn>(.*?)<\/issn>/);
          
          const title = titleMatch ? titleMatch[1] : '';
          const issn = issnMatch ? issnMatch[1] : '';
          
          return `
            <div class="journal-header" style="text-align: center; margin-bottom: 30px; border-bottom: 2px solid #4A90E2; padding-bottom: 20px;">
              <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div style="flex: 1;">
                  <h1 style="font-size: 36px; font-weight: bold; color: #4A90E2; margin: 0; letter-spacing: 2px;">${title.split(' ')[0] || 'REVISTA'}</h1>
                  <h2 style="font-size: 24px; font-weight: bold; color: #4A90E2; margin: 5px 0 0 0;">${title.split(' ').slice(1).join(' ') || 'MATERIA'}</h2>
                  ${issn ? `<p style="font-size: 12px; margin: 10px 0 0 0; color: #666;">ISSN ${issn} articles e20240534, 2024</p>` : ''}
                </div>
                <div style="text-align: right; color: #4A90E2; font-size: 18px; font-weight: bold;">
                  V.29 N.4
                </div>
              </div>
            </div>
          `;
        })
        
        .replace(/<front[^>]*>[\s\S]*?<\/front>/g, '') // Remove front matter as it's handled above
        .replace(/<body[^>]*>/g, '<div class="body">')
        .replace(/<\/body>/g, '</div>')
        
        // Article title styling
        .replace(/<title-group>([\s\S]*?)<\/title-group>/g, (match, content) => {
          const titleMatch = content.match(/<article-title>(.*?)<\/article-title>/);
          const title = titleMatch ? titleMatch[1] : '';
          
          return `
            <h1 style="font-size: 24px; font-weight: bold; color: #333; margin: 30px 0 20px 0; line-height: 1.3; text-align: left;">
              ${title}
            </h1>
          `;
        })
        
        // Author styling with ORCID icons
        .replace(/<contrib-group>([\s\S]*?)<\/contrib-group>/g, (match, content) => {
          const contribs = content.match(/<contrib[^>]*>([\s\S]*?)<\/contrib>/g) || [];
          
          const authorHtml = contribs.map(contrib => {
            const nameMatch = contrib.match(/<surname>(.*?)<\/surname>[\s\S]*?<given-names>(.*?)<\/given-names>/);
            const orcidMatch = contrib.match(/<contrib-id[^>]*>(.*?)<\/contrib-id>/);
            
            const surname = nameMatch ? nameMatch[1] : '';
            const givenNames = nameMatch ? nameMatch[2] : '';
            const orcid = orcidMatch ? orcidMatch[1] : '';
            
            return `
              <span style="font-size: 16px; color: #333; margin-right: 15px;">
                ${givenNames} ${surname}<sup style="color: #4A90E2;">1,2</sup>
                ${orcid ? `<span style="display: inline-block; width: 16px; height: 16px; background: #A6CE39; border-radius: 50%; margin-left: 5px; position: relative; top: 2px;"></span>` : ''}
              </span>
            `;
          }).join('');
          
          return `
            <div style="text-align: center; margin: 20px 0 30px 0; font-size: 16px;">
              ${authorHtml}
            </div>
          `;
        })
        
        // Affiliations
        .replace(/<aff[^>]*>([\s\S]*?)<\/aff>/g, (match, content) => {
          return `
            <div style="font-size: 12px; color: #666; text-align: center; margin: 10px 0; line-height: 1.4;">
              ${content}
            </div>
          `;
        })
        
        // Abstract styling
        .replace(/<abstract[^>]*>([\s\S]*?)<\/abstract>/g, (match, content) => {
          const titleMatch = content.match(/<title>(.*?)<\/title>/);
          const textContent = content.replace(/<title>.*?<\/title>/, '').replace(/<[^>]*>/g, '');
          
          return `
            <div style="margin: 30px 0; padding: 20px 0; border-top: 1px solid #ddd;">
              <h3 style="font-size: 14px; font-weight: bold; color: #333; margin: 0 0 10px 0; text-transform: uppercase;">ABSTRACT</h3>
              <p style="font-size: 12px; color: #333; line-height: 1.6; text-align: justify; margin: 0;">
                ${textContent.trim()}
              </p>
            </div>
          `;
        })
        
        // Keywords styling
        .replace(/<kwd-group[^>]*>([\s\S]*?)<\/kwd-group>/g, (match, content) => {
          const keywords = content.match(/<kwd>(.*?)<\/kwd>/g) || [];
          const keywordText = keywords.map(kwd => kwd.replace(/<\/?kwd>/g, '')).join('; ');
          
          return `
            <div style="margin: 20px 0; font-size: 12px; color: #333;">
              <strong>Keywords:</strong> ${keywordText}.
            </div>
          `;
        })
        
        // Section styling
        .replace(/<sec[^>]*>/g, '<div class="section" style="margin: 25px 0;">')
        .replace(/<\/sec>/g, '</div>')
        .replace(/<title>/g, '<h3 style="font-size: 14px; font-weight: bold; color: #333; margin: 20px 0 10px 0; text-transform: uppercase;">')
        .replace(/<\/title>/g, '</h3>')
        .replace(/<p>/g, '<p style="font-size: 12px; color: #333; line-height: 1.6; text-align: justify; margin: 10px 0;">')
        .replace(/<\/p>/g, '</p>')
        
        // Convert figures to images with journal styling
        .replace(/<fig[^>]*>([\s\S]*?)<\/fig>/g, (match, content) => {
          const labelMatch = content.match(/<label>(.*?)<\/label>/);
          const captionMatch = content.match(/<caption>([\s\S]*?)<\/caption>/);
          const graphicMatch = content.match(/<graphic[^>]*xlink:href="([^"]*)"[^>]*\/>/);
          
          const label = labelMatch ? labelMatch[1] : '';
          const caption = captionMatch ? captionMatch[1].replace(/<[^>]*>/g, '') : '';
          const imageUrl = graphicMatch ? graphicMatch[1] : '';
          
          return `
            <div class="figure" style="margin: 30px 0; text-align: center; page-break-inside: avoid;">
              <img src="${imageUrl}" alt="${label}" style="max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 4px;" onerror="this.style.display='none'; this.nextElementSibling.style.display='block';" />
              <div style="display: none; padding: 20px; background: #f9f9f9; color: #666; border: 1px solid #ddd; border-radius: 4px; font-size: 12px;">Image not available: ${imageUrl}</div>
              <div style="margin-top: 10px; font-size: 12px; color: #333;">
                <strong>${label}</strong>
                ${caption ? `<br><span style="color: #666;">${caption}</span>` : ''}
              </div>
            </div>
          `;
        })
        
        // Convert formulas with academic styling
        .replace(/<disp-formula[^>]*>([\s\S]*?)<\/disp-formula>/g, (match, content) => {
          const labelMatch = content.match(/<label>(.*?)<\/label>/);
          const texMatch = content.match(/<tex-math>([\s\S]*?)<\/tex-math>/);
          
          const label = labelMatch ? labelMatch[1] : '';
          const formula = texMatch ? texMatch[1] : '';
          
          return `
            <div class="formula" style="margin: 25px 0; text-align: center; page-break-inside: avoid;">
              <div style="font-family: 'Times New Roman', serif; background: #fafafa; padding: 15px; border: 1px solid #ddd; border-radius: 4px; margin-bottom: 10px; font-size: 14px;">
                ${escapeHtml(formula)}
              </div>
              <div style="font-size: 12px; color: #333;"><strong>${label}</strong></div>
            </div>
          `;
        });

      return (
        <div 
          className="prose max-w-none"
          dangerouslySetInnerHTML={{ __html: preview }}
        />
      );
    } catch (error) {
      return <div className="text-red-600">Invalid XML structure</div>;
    }
  };

  const escapeHtml = (text: string) => {
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">XML Validation & Editing</h2>
          <p className="text-gray-600">Validate XML structure with DTD and ENT rules</p>
        </div>
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <label className="flex items-center space-x-1">
              <input
                type="checkbox"
                checked={dtdRules}
                onChange={(e) => setDtdRules(e.target.checked)}
                className="rounded"
              />
              <span className="text-sm">DTD Rules</span>
            </label>
            <label className="flex items-center space-x-1">
              <input
                type="checkbox"
                checked={entRules}
                onChange={(e) => setEntRules(e.target.checked)}
                className="rounded"
              />
              <span className="text-sm">ENT Rules</span>
            </label>
          </div>
          <button
            onClick={validateXML}
            disabled={isValidating}
            className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 flex items-center space-x-2"
          >
            {isValidating ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            ) : (
              <Settings className="h-4 w-4" />
            )}
            <span>{isValidating ? 'Validating...' : 'Validate XML'}</span>
          </button>
        </div>
      </div>

      {/* Validation Results */}
      {validationErrors.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-3">
            <AlertTriangle className="h-5 w-5 text-red-600" />
            <span className="font-medium text-red-800">
              {validationErrors.length} validation issue{validationErrors.length !== 1 ? 's' : ''} found
            </span>
          </div>
          <div className="space-y-2">
            {validationErrors.map((error, index) => (
              <div key={index} className="text-sm">
                <span className={`inline-block px-2 py-1 rounded text-xs font-medium mr-2 ${
                  error.type === 'error' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'
                }`}>
                  {error.type.toUpperCase()}
                </span>
                <span className="text-gray-700">
                  Line {error.line}, Column {error.column}: {error.message}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {validationErrors.length === 0 && !isValidating && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <CheckCircle className="h-5 w-5 text-green-600" />
            <span className="font-medium text-green-800">XML is valid and well-formed</span>
          </div>
        </div>
      )}

      {/* View Mode Toggle */}
      <div className="flex items-center space-x-2 bg-gray-100 p-1 rounded-lg w-fit">
        <button
          onClick={() => setViewMode('code')}
          className={`px-3 py-1 rounded-md text-sm font-medium transition-colors flex items-center space-x-1 ${
            viewMode === 'code' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600'
          }`}
        >
          <Code className="h-4 w-4" />
          <span>Code</span>
        </button>
        <button
          onClick={() => setViewMode('preview')}
          className={`px-3 py-1 rounded-md text-sm font-medium transition-colors flex items-center space-x-1 ${
            viewMode === 'preview' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600'
          }`}
        >
          <Eye className="h-4 w-4" />
          <span>Preview</span>
        </button>
      </div>

      {/* Editor/Preview */}
      <div className="grid grid-cols-1 gap-6">
        {viewMode === 'code' ? (
          <div className="relative">
            <div className="flex">
              {/* Line Numbers */}
              <div className="bg-gray-50 px-3 py-4 text-sm text-gray-500 font-mono border-r border-gray-200 select-none">
                {getLineNumbers().map(num => (
                  <div key={num} className="leading-6">{num}</div>
                ))}
              </div>
              
              {/* Code Editor */}
              <textarea
                value={xmlContent}
                onChange={(e) => setXmlContent(e.target.value)}
                className="flex-1 p-4 font-mono text-sm border border-gray-200 rounded-r-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                style={{ minHeight: '400px' }}
                spellCheck={false}
              />
            </div>
          </div>
        ) : (
          <div className="bg-white p-6 border border-gray-200 rounded-lg min-h-96">
            <h3 className="font-semibold text-gray-900 mb-4">XML Preview</h3>
            {renderPreview()}
          </div>
        )}
      </div>

      {/* XML Stats */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg border border-gray-200 text-center">
          <div className="text-2xl font-bold text-gray-900">{xmlContent.split('\n').length}</div>
          <div className="text-sm text-gray-600">Lines</div>
        </div>
        <div className="bg-white p-4 rounded-lg border border-gray-200 text-center">
          <div className="text-2xl font-bold text-gray-900">{xmlContent.length}</div>
          <div className="text-sm text-gray-600">Characters</div>
        </div>
        <div className="bg-white p-4 rounded-lg border border-gray-200 text-center">
          <div className={`text-2xl font-bold ${validationErrors.length > 0 ? 'text-red-600' : 'text-green-600'}`}>
            {validationErrors.length}
          </div>
          <div className="text-sm text-gray-600">Errors</div>
        </div>
        <div className="bg-white p-4 rounded-lg border border-gray-200 text-center">
          <div className="text-2xl font-bold text-blue-600">
            {(xmlContent.match(/<[^/][^>]*>/g) || []).length}
          </div>
          <div className="text-sm text-gray-600">Elements</div>
        </div>
      </div>

      <div className="flex justify-end">
        <button
          onClick={onNext}
          disabled={validationErrors.some(e => e.type === 'error')}
          className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
        >
          <span>Continue to Export</span>
          <CheckCircle className="h-5 w-5" />
        </button>
      </div>
    </div>
  );
};

export default XMLEditor;