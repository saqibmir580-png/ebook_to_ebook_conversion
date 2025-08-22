/**
 * Formula Converter Utility
 * Converts LaTeX mathematical expressions to human-readable Unicode format
 */

interface SymbolMappings {
  [key: string]: string;
}

class FormulaConverter {
  private greekLetters: SymbolMappings;
  private mathSymbols: SymbolMappings;
  private functions: SymbolMappings;
  private superscripts: SymbolMappings;
  private subscripts: SymbolMappings;
  private simpleFractions: SymbolMappings;

  constructor() {
    // Greek letters mapping
    this.greekLetters = {
      'alpha': 'α', 'beta': 'β', 'gamma': 'γ', 'delta': 'δ',
      'epsilon': 'ε', 'zeta': 'ζ', 'eta': 'η', 'theta': 'θ',
      'iota': 'ι', 'kappa': 'κ', 'lambda': 'λ', 'mu': 'μ',
      'nu': 'ν', 'xi': 'ξ', 'omicron': 'ο', 'pi': 'π',
      'rho': 'ρ', 'sigma': 'σ', 'tau': 'τ', 'upsilon': 'υ',
      'phi': 'φ', 'chi': 'χ', 'psi': 'ψ', 'omega': 'ω',
      'Alpha': 'Α', 'Beta': 'Β', 'Gamma': 'Γ', 'Delta': 'Δ',
      'Epsilon': 'Ε', 'Zeta': 'Ζ', 'Eta': 'Η', 'Theta': 'Θ',
      'Iota': 'Ι', 'Kappa': 'Κ', 'Lambda': 'Λ', 'Mu': 'Μ',
      'Nu': 'Ν', 'Xi': 'Ξ', 'Omicron': 'Ο', 'Pi': 'Π',
      'Rho': 'Ρ', 'Sigma': 'Σ', 'Tau': 'Τ', 'Upsilon': 'Υ',
      'Phi': 'Φ', 'Chi': 'Χ', 'Psi': 'Ψ', 'Omega': 'Ω'
    };

    // Mathematical symbols mapping
    this.mathSymbols = {
      'infty': '∞', 'partial': '∂', 'nabla': '∇', 'sum': '∑',
      'prod': '∏', 'int': '∫', 'oint': '∮', 'pm': '±', 'mp': '∓',
      'times': '×', 'div': '÷', 'cdot': '·', 'bullet': '•',
      'cap': '∩', 'cup': '∪', 'subset': '⊂', 'supset': '⊃',
      'subseteq': '⊆', 'supseteq': '⊇', 'in': '∈', 'notin': '∉',
      'emptyset': '∅', 'forall': '∀', 'exists': '∃', 'neg': '¬',
      'land': '∧', 'lor': '∨', 'rightarrow': '→', 'leftarrow': '←',
      'leftrightarrow': '↔', 'Rightarrow': '⇒', 'Leftarrow': '⇐',
      'Leftrightarrow': '⇔', 'approx': '≈', 'neq': '≠', 'leq': '≤',
      'geq': '≥', 'll': '≪', 'gg': '≫', 'equiv': '≡', 'sim': '∼',
      'simeq': '≃', 'cong': '≅', 'propto': '∝'
    };

    // Function names mapping
    this.functions = {
      'sin': 'sin', 'cos': 'cos', 'tan': 'tan', 'cot': 'cot',
      'sec': 'sec', 'csc': 'csc', 'sinh': 'sinh', 'cosh': 'cosh',
      'tanh': 'tanh', 'log': 'log', 'ln': 'ln', 'exp': 'exp',
      'sqrt': '√', 'lim': 'lim', 'max': 'max', 'min': 'min',
      'sup': 'sup', 'inf': 'inf', 'det': 'det', 'dim': 'dim'
    };

    // Superscript mapping
    this.superscripts = {
      '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
      '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',
      '+': '⁺', '-': '⁻', '=': '⁼', '(': '⁽', ')': '⁾',
      'n': 'ⁿ', 'i': 'ⁱ'
    };

    // Subscript mapping
    this.subscripts = {
      '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄',
      '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉',
      '+': '₊', '-': '₋', '=': '₌', '(': '₍', ')': '₎',
      'a': 'ₐ', 'e': 'ₑ', 'h': 'ₕ', 'i': 'ᵢ', 'j': 'ⱼ',
      'k': 'ₖ', 'l': 'ₗ', 'm': 'ₘ', 'n': 'ₙ', 'o': 'ₒ',
      'p': 'ₚ', 'r': 'ᵣ', 's': 'ₛ', 't': 'ₜ', 'u': 'ᵤ',
      'v': 'ᵥ', 'x': 'ₓ'
    };

    // Simple fractions mapping
    this.simpleFractions = {
      '1/2': '½', '1/3': '⅓', '2/3': '⅔', '1/4': '¼',
      '3/4': '¾', '1/5': '⅕', '2/5': '⅖', '3/5': '⅗',
      '4/5': '⅘', '1/6': '⅙', '5/6': '⅚', '1/7': '⅐',
      '1/8': '⅛', '3/8': '⅜', '5/8': '⅝', '7/8': '⅞',
      '1/9': '⅑', '1/10': '⅒'
    };
  }

  /**
   * Main conversion method
   */
  convertToReadable(latex: string): string {
    if (!latex || typeof latex !== 'string') {
      return latex || '';
    }

    try {
      let result = latex.trim();
      
      // Remove LaTeX delimiters
      result = result.replace(/^\$+|\$+$/g, '');
      result = result.replace(/^\\begin\{.*?\}|\\end\{.*?\}$/g, '');
      
      // Convert fractions
      result = this.convertFractions(result);
      
      // Convert superscripts and subscripts
      result = this.convertSuperscripts(result);
      result = this.convertSubscripts(result);
      
      // Convert Greek letters
      result = this.convertGreekLetters(result);
      
      // Convert mathematical symbols
      result = this.convertMathSymbols(result);
      
      // Convert functions
      result = this.convertFunctions(result);
      
      // Convert integrals with limits
      result = this.convertIntegrals(result);
      
      // Convert summations and products
      result = this.convertSummations(result);
      
      // Convert matrices
      result = this.convertMatrices(result);
      
      // Convert binomial coefficients
      result = this.convertBinomials(result);
      
      // Clean up extra whitespace and braces
      result = this.cleanupResult(result);
      
      return result;
    } catch (error) {
      console.warn('Formula conversion error:', error);
      return latex; // Return original if conversion fails
    }
  }

  private convertFractions(text: string): string {
    // Handle simple fractions first
    for (const [fraction, unicode] of Object.entries(this.simpleFractions)) {
      const regex = new RegExp(`\\\\frac\\{${fraction.split('/')[0]}\\}\\{${fraction.split('/')[1]}\\}`, 'g');
      text = text.replace(regex, unicode);
    }
    
    // Handle general fractions
    text = text.replace(/\\frac\{([^{}]+)\}\{([^{}]+)\}/g, (match, num, den) => {
      const cleanNum = this.convertToReadable(num);
      const cleanDen = this.convertToReadable(den);
      return `(${cleanNum})/(${cleanDen})`;
    });
    
    return text;
  }

  private convertSuperscripts(text: string): string {
    return text.replace(/\^(\{([^}]+)\}|(\w))/g, (match, full, braced, single) => {
      const content = braced || single;
      return content.split('').map(char => this.superscripts[char] || char).join('');
    });
  }

  private convertSubscripts(text: string): string {
    return text.replace(/_(\{([^}]+)\}|(\w))/g, (match, full, braced, single) => {
      const content = braced || single;
      return content.split('').map(char => this.subscripts[char] || char).join('');
    });
  }

  private convertGreekLetters(text: string): string {
    for (const [latex, unicode] of Object.entries(this.greekLetters)) {
      const regex = new RegExp(`\\\\${latex}\\b`, 'g');
      text = text.replace(regex, unicode);
    }
    return text;
  }

  private convertMathSymbols(text: string): string {
    for (const [latex, unicode] of Object.entries(this.mathSymbols)) {
      const regex = new RegExp(`\\\\${latex}\\b`, 'g');
      text = text.replace(regex, unicode);
    }
    return text;
  }

  private convertFunctions(text: string): string {
    for (const [latex, readable] of Object.entries(this.functions)) {
      const regex = new RegExp(`\\\\${latex}\\b`, 'g');
      text = text.replace(regex, readable);
    }
    return text;
  }

  private convertIntegrals(text: string): string {
    // Integral with limits
    text = text.replace(/\\int_\{([^}]+)\}\^\{([^}]+)\}/g, '∫[from $1 to $2]');
    text = text.replace(/\\int_([a-zA-Z0-9])\^([a-zA-Z0-9])/g, '∫[from $1 to $2]');
    text = text.replace(/\\int/g, '∫');
    
    return text;
  }

  private convertSummations(text: string): string {
    // Summation with limits
    text = text.replace(/\\sum_\{([^}]+)\}\^\{([^}]+)\}/g, '∑[from $1 to $2]');
    text = text.replace(/\\sum_([a-zA-Z0-9=]+)\^([a-zA-Z0-9∞]+)/g, '∑[from $1 to $2]');
    text = text.replace(/\\sum/g, '∑');
    
    // Product with limits
    text = text.replace(/\\prod_\{([^}]+)\}\^\{([^}]+)\}/g, '∏[from $1 to $2]');
    text = text.replace(/\\prod_([a-zA-Z0-9=]+)\^([a-zA-Z0-9∞]+)/g, '∏[from $1 to $2]');
    text = text.replace(/\\prod/g, '∏');
    
    return text;
  }

  private convertMatrices(text: string): string {
    // Simple matrix conversion
    text = text.replace(/\\begin\{matrix\}(.*?)\\end\{matrix\}/gs, (match, content) => {
      const rows = content.split('\\\\').map((row: string) => 
        row.trim().split('&').map((cell: string) => cell.trim()).join(' ')
      );
      return `[${rows.join('; ')}]`;
    });
    
    return text;
  }

  private convertBinomials(text: string): string {
    text = text.replace(/\\binom\{([^}]+)\}\{([^}]+)\}/g, 'C($1,$2)');
    text = text.replace(/\\choose/g, 'C');
    
    return text;
  }

  private cleanupResult(text: string): string {
    // Remove extra braces
    text = text.replace(/\{([^{}]*)\}/g, '$1');
    
    // Remove backslashes from remaining LaTeX commands
    text = text.replace(/\\([a-zA-Z]+)/g, '$1');
    
    // Clean up multiple spaces
    text = text.replace(/\s+/g, ' ');
    
    // Remove leading/trailing whitespace
    text = text.trim();
    
    return text;
  }
}

// Create and export a singleton instance
const formulaConverter = new FormulaConverter();

export default formulaConverter;
