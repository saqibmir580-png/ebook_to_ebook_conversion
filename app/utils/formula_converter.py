#!/usr/bin/env python
"""
LaTeX to human-readable formula converter
"""

import re
from typing import Dict, List

class FormulaConverter:
    """Convert LaTeX formulas to human-readable format"""
    
    def __init__(self):
        # Greek letters mapping
        self.greek_letters = {
            r'\\alpha': 'α', r'\\beta': 'β', r'\\gamma': 'γ', r'\\delta': 'δ',
            r'\\epsilon': 'ε', r'\\zeta': 'ζ', r'\\eta': 'η', r'\\theta': 'θ',
            r'\\iota': 'ι', r'\\kappa': 'κ', r'\\lambda': 'λ', r'\\mu': 'μ',
            r'\\nu': 'ν', r'\\xi': 'ξ', r'\\omicron': 'ο', r'\\pi': 'π',
            r'\\rho': 'ρ', r'\\sigma': 'σ', r'\\tau': 'τ', r'\\upsilon': 'υ',
            r'\\phi': 'φ', r'\\chi': 'χ', r'\\psi': 'ψ', r'\\omega': 'ω',
            # Capital Greek letters
            r'\\Alpha': 'Α', r'\\Beta': 'Β', r'\\Gamma': 'Γ', r'\\Delta': 'Δ',
            r'\\Epsilon': 'Ε', r'\\Zeta': 'Ζ', r'\\Eta': 'Η', r'\\Theta': 'Θ',
            r'\\Iota': 'Ι', r'\\Kappa': 'Κ', r'\\Lambda': 'Λ', r'\\Mu': 'Μ',
            r'\\Nu': 'Ν', r'\\Xi': 'Ξ', r'\\Omicron': 'Ο', r'\\Pi': 'Π',
            r'\\Rho': 'Ρ', r'\\Sigma': 'Σ', r'\\Tau': 'Τ', r'\\Upsilon': 'Υ',
            r'\\Phi': 'Φ', r'\\Chi': 'Χ', r'\\Psi': 'Ψ', r'\\Omega': 'Ω'
        }
        
        # Mathematical symbols
        self.math_symbols = {
            r'\\infty': '∞', r'\\partial': '∂', r'\\nabla': '∇',
            r'\\pm': '±', r'\\mp': '∓', r'\\times': '×', r'\\div': '÷',
            r'\\cdot': '·', r'\\bullet': '•', r'\\circ': '∘',
            r'\\leq': '≤', r'\\geq': '≥', r'\\neq': '≠', r'\\approx': '≈',
            r'\\equiv': '≡', r'\\propto': '∝', r'\\sim': '∼',
            r'\\in': '∈', r'\\notin': '∉', r'\\subset': '⊂', r'\\supset': '⊃',
            r'\\subseteq': '⊆', r'\\supseteq': '⊇', r'\\cup': '∪', r'\\cap': '∩',
            r'\\emptyset': '∅', r'\\forall': '∀', r'\\exists': '∃',
            r'\\rightarrow': '→', r'\\leftarrow': '←', r'\\leftrightarrow': '↔',
            r'\\Rightarrow': '⇒', r'\\Leftarrow': '⇐', r'\\Leftrightarrow': '⇔'
        }
        
        # Function names
        self.functions = {
            r'\\sin': 'sin', r'\\cos': 'cos', r'\\tan': 'tan',
            r'\\sec': 'sec', r'\\csc': 'csc', r'\\cot': 'cot',
            r'\\sinh': 'sinh', r'\\cosh': 'cosh', r'\\tanh': 'tanh',
            r'\\log': 'log', r'\\ln': 'ln', r'\\exp': 'exp',
            r'\\sqrt': '√', r'\\lim': 'lim', r'\\max': 'max', r'\\min': 'min'
        }
        
        # Unicode fractions for simple cases
        self.simple_fractions = {
            '1/2': '½', '1/3': '⅓', '2/3': '⅔', '1/4': '¼', '3/4': '¾',
            '1/5': '⅕', '2/5': '⅖', '3/5': '⅗', '4/5': '⅘', '1/6': '⅙',
            '5/6': '⅚', '1/7': '⅐', '1/8': '⅛', '3/8': '⅜', '5/8': '⅝',
            '7/8': '⅞', '1/9': '⅑', '1/10': '⅒'
        }
        
        # Superscript and subscript mappings
        self.superscript_map = str.maketrans('0123456789+-=()abcdefghijklmnopqrstuvwxyz',
                                           '⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ᵃᵇᶜᵈᵉᶠᵍʰⁱʲᵏˡᵐⁿᵒᵖᵠʳˢᵗᵘᵛʷˣʸᶻ')
        self.subscript_map = str.maketrans('0123456789+-=()abcdefghijklmnopqrstuvwxyz',
                                         '₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎ₐᵦᶜᵈₑᶠᵍₕᵢⱼₖₗₘₙₒₚᵩᵣₛₜᵤᵥwₓᵧᵤ')
    
    def convert_to_readable(self, latex_formula: str) -> str:
        """Convert LaTeX formula to human-readable format"""
        if not latex_formula or not latex_formula.strip():
            return latex_formula
            
        formula = latex_formula.strip()
        
        try:
            # Remove common LaTeX delimiters
            formula = re.sub(r'^\$+|\$+$', '', formula)
            formula = re.sub(r'^\\begin\{equation\}|\\end\{equation\}$', '', formula)
            formula = re.sub(r'^\\begin\{align\}|\\end\{align\}$', '', formula)
            
            # Convert fractions
            formula = self._convert_fractions(formula)
            
            # Convert integrals, sums, products
            formula = self._convert_integrals(formula)
            formula = self._convert_sums(formula)
            formula = self._convert_products(formula)
            
            # Convert matrices
            formula = self._convert_matrices(formula)
            
            # Convert binomial coefficients
            formula = self._convert_binomials(formula)
            
            # Convert superscripts and subscripts
            formula = self._convert_superscripts(formula)
            formula = self._convert_subscripts(formula)
            
            # Convert Greek letters
            for latex, unicode_char in self.greek_letters.items():
                formula = re.sub(latex + r'\b', unicode_char, formula)
            
            # Convert mathematical symbols
            for latex, unicode_char in self.math_symbols.items():
                formula = formula.replace(latex, unicode_char)
            
            # Convert function names
            for latex, readable in self.functions.items():
                formula = re.sub(latex + r'\b', readable, formula)
            
            # Convert delimiters
            formula = self._convert_delimiters(formula)
            
            # Clean up extra spaces and formatting
            formula = self._clean_formula(formula)
            
            return formula
            
        except Exception as e:
            print(f"Error converting formula: {e}")
            return latex_formula
    
    def _convert_fractions(self, formula: str) -> str:
        """Convert LaTeX fractions to readable format"""
        # Handle simple fractions first
        for frac, unicode_frac in self.simple_fractions.items():
            pattern = r'\\frac\{' + re.escape(frac.split('/')[0]) + r'\}\{' + re.escape(frac.split('/')[1]) + r'\}'
            formula = re.sub(pattern, unicode_frac, formula)
        
        # Handle complex fractions
        def replace_frac(match):
            numerator = match.group(1)
            denominator = match.group(2)
            return f"({numerator})/({denominator})"
        
        formula = re.sub(r'\\frac\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}', 
                        replace_frac, formula)
        
        return formula
    
    def _convert_integrals(self, formula: str) -> str:
        """Convert integrals to readable format"""
        # Definite integrals with limits
        formula = re.sub(r'\\int_\{([^}]+)\}\^\{([^}]+)\}', r'∫[from \1 to \2]', formula)
        # Indefinite integrals
        formula = re.sub(r'\\int', '∫', formula)
        return formula
    
    def _convert_sums(self, formula: str) -> str:
        """Convert summations to readable format"""
        formula = re.sub(r'\\sum_\{([^}]+)\}\^\{([^}]+)\}', r'Σ[from \1 to \2]', formula)
        formula = re.sub(r'\\sum', 'Σ', formula)
        return formula
    
    def _convert_products(self, formula: str) -> str:
        """Convert products to readable format"""
        formula = re.sub(r'\\prod_\{([^}]+)\}\^\{([^}]+)\}', r'Π[from \1 to \2]', formula)
        formula = re.sub(r'\\prod', 'Π', formula)
        return formula
    
    def _convert_matrices(self, formula: str) -> str:
        """Convert matrices to readable format"""
        # Simple matrix conversion
        formula = re.sub(r'\\begin\{matrix\}(.*?)\\end\{matrix\}', 
                        lambda m: '[' + m.group(1).replace('\\\\', '; ').replace('&', ', ') + ']', 
                        formula, flags=re.DOTALL)
        return formula
    
    def _convert_binomials(self, formula: str) -> str:
        """Convert binomial coefficients"""
        formula = re.sub(r'\\binom\{([^}]+)\}\{([^}]+)\}', r'C(\1,\2)', formula)
        return formula
    
    def _convert_superscripts(self, formula: str) -> str:
        """Convert superscripts to Unicode"""
        def replace_sup(match):
            content = match.group(1)
            if len(content) == 1 and content in '0123456789+-=()abcdefghijklmnopqrstuvwxyz':
                return content.translate(self.superscript_map)
            else:
                return f"^({content})"
        
        formula = re.sub(r'\^{([^}]+)}', replace_sup, formula)
        formula = re.sub(r'\^([0-9a-zA-Z])', lambda m: m.group(1).translate(self.superscript_map), formula)
        return formula
    
    def _convert_subscripts(self, formula: str) -> str:
        """Convert subscripts to Unicode"""
        def replace_sub(match):
            content = match.group(1)
            if len(content) == 1 and content in '0123456789+-=()abcdefghijklmnopqrstuvwxyz':
                return content.translate(self.subscript_map)
            else:
                return f"_({content})"
        
        formula = re.sub(r'_{([^}]+)}', replace_sub, formula)
        formula = re.sub(r'_([0-9a-zA-Z])', lambda m: m.group(1).translate(self.subscript_map), formula)
        return formula
    
    def _convert_delimiters(self, formula: str) -> str:
        """Convert LaTeX delimiters"""
        formula = re.sub(r'\\left\(', '(', formula)
        formula = re.sub(r'\\right\)', ')', formula)
        formula = re.sub(r'\\left\[', '[', formula)
        formula = re.sub(r'\\right\]', ']', formula)
        formula = re.sub(r'\\left\{', '{', formula)
        formula = re.sub(r'\\right\}', '}', formula)
        formula = re.sub(r'\\left\|', '|', formula)
        formula = re.sub(r'\\right\|', '|', formula)
        return formula
    
    def _clean_formula(self, formula: str) -> str:
        """Clean up the formula"""
        # Remove extra spaces
        formula = re.sub(r'\s+', ' ', formula)
        # Remove empty braces
        formula = re.sub(r'\{\}', '', formula)
        # Clean up spacing around operators
        formula = re.sub(r'\s*([+\-*/=<>])\s*', r' \1 ', formula)
        return formula.strip()

# Global instance
formula_converter = FormulaConverter()
