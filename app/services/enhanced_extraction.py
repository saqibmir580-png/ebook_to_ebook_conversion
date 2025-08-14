import os
import time
import logging
from typing import Dict, List, Tuple, Optional, Any
import pytesseract
from PIL import Image
import re
import fitz  # PyMuPDF
import pytesseract
import spacy
import cv2
import numpy as np
from langdetect import detect
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from datetime import datetime
import logging
import xml.etree.ElementTree as ET
from xml.dom import minidom
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Dict, Optional, Any
import json
import re

# Configure logging
logger = logging.getLogger(__name__)

class JATSGenerator:
    """Class for generating JATS XML from document content"""
    
    def __init__(self):
        self.namespaces = {
            'xlink': 'http://www.w3.org/1999/xlink',
            'mml': 'http://www.w3.org/1998/Math/MathML'
        }
        self._register_namespaces()
    
    def _register_namespaces(self):
        """Register XML namespaces for proper output"""
        for prefix, uri in self.namespaces.items():
            ET.register_namespace(prefix, uri)
    
    def generate_jats(self, metadata: Dict[str, Any]) -> str:
        """
        Generate JATS XML from document metadata
        
        Args:
            metadata: Dictionary containing document metadata
            
        Returns:
            str: JATS XML as string
        """
        # Create root element
        article_attrs = {
            'article-type': metadata.get('article_type', 'research-article'),
            'dtd-version': '1.1',
            'xml:lang': metadata.get('language', 'en'),
            'xmlns:xlink': self.namespaces['xlink'],
            'xmlns:mml': self.namespaces['mml']
        }
        article = ET.Element('article', article_attrs)
        
        # Add front matter
        front = self._create_front(metadata)
        article.append(front)
        
        # Add body
        body = self._create_body(metadata)
        if body is not None:
            article.append(body)
        
        # Add back matter
        back = self._create_back(metadata)
        if back is not None:
            article.append(back)
        
        # Convert to string with pretty printing
        return self._prettify(article)
    
    def _create_front(self, metadata: Dict[str, Any]) -> ET.Element:
        """Create front matter section"""
        front = ET.Element('front')
        
        # Journal metadata
        journal_meta = ET.SubElement(front, 'journal-meta')
        ET.SubElement(journal_meta, 'journal-id', {
            'journal-id-type': 'publisher-id'
        }).text = metadata.get('journal_id', 'REVISIAMATERIA')
        ET.SubElement(journal_meta, 'journal-title').text = metadata.get('journal_title', 'REVISIAMATERIA')
        ET.SubElement(journal_meta, 'issn', {'pub-type': 'epub'}).text = '1517-7076'
        
        # Article metadata
        article_meta = ET.SubElement(front, 'article-meta')
        
        # Article ID (DOI)
        ET.SubElement(article_meta, 'article-id', {
            'pub-id-type': 'doi'
        }).text = metadata.get('doi', '10.1590/1517-7076-RMAT-2024-XXXX')
        
        # Article categories
        article_categories = ET.SubElement(article_meta, 'article-categories')
        subj_group = ET.SubElement(article_categories, 'subj-group', {'subj-group-type': 'heading'})
        ET.SubElement(subj_group, 'subject').text = 'Research Article'
        
        # Title group
        title_group = ET.SubElement(article_meta, 'title-group')
        ET.SubElement(title_group, 'article-title').text = metadata.get('title', 'Untitled Document')
        
        # Authors and affiliations
        self._add_authors(article_meta, metadata.get('authors', []))
        
        # Publication dates
        pub_dates = metadata.get('dates', {})
        pub_date = ET.SubElement(article_meta, 'pub-date', {'pub-type': 'epub'})
        pub_date.extend([
            self._create_element('day', pub_dates.get('published', {}).get('day', '24')),
            self._create_element('month', pub_dates.get('published', {}).get('month', '10')),
            self._create_element('year', pub_dates.get('published', {}).get('year', '2024'))
        ])
        
        # Volume, issue, fpage
        ET.SubElement(article_meta, 'volume').text = metadata.get('volume', '29')
        ET.SubElement(article_meta, 'issue').text = metadata.get('issue', '4')
        ET.SubElement(article_meta, 'fpage').text = metadata.get('fpage', 'e20240534')
        
        # History
        history = ET.SubElement(article_meta, 'history')
        self._add_history_date(history, 'received', '14', '08', '2024')
        self._add_history_date(history, 'accepted', '24', '10', '2024')
        
        # Permissions
        permissions = ET.SubElement(article_meta, 'permissions')
        ET.SubElement(permissions, 'copyright-statement').text = 'Copyright: 2024 Author et al.'
        license_elem = ET.SubElement(permissions, 'license', {
            'xlink:href': 'https://creativecommons.org/licenses/by/4.0/'
        })
        ET.SubElement(license_elem, 'license-p').text = (
            'This is an open access article distributed under the terms of the '
            'Creative Commons Attribution License (CC BY 4.0)'
        )
        
        # Abstract
        if 'abstract' in metadata:
            abstract = ET.SubElement(article_meta, 'abstract')
            if isinstance(metadata['abstract'], list):
                for para in metadata['abstract']:
                    ET.SubElement(abstract, 'p').text = para
            else:
                ET.SubElement(abstract, 'p').text = metadata['abstract']
        
        # Keywords
        if 'keywords' in metadata and metadata['keywords']:
            kwd_group = ET.SubElement(article_meta, 'kwd-group', {'kwd-group-type': 'author'})
            ET.SubElement(kwd_group, 'title').text = 'Keywords:'
            for kw in metadata['keywords']:
                ET.SubElement(kwd_group, 'kwd').text = kw
        
        return front
    
    def _create_body(self, metadata: Dict[str, Any]) -> Optional[ET.Element]:
        """Create body section from document content"""
        if not metadata.get('sections'):
            return None
            
        body = ET.Element('body')
        
        for section in metadata['sections']:
            sec = ET.SubElement(body, 'sec', {'sec-type': section.get('type', 'other')})
            if 'title' in section:
                ET.SubElement(sec, 'title').text = section['title']
            
            # Add paragraphs
            if 'content' in section:
                if isinstance(section['content'], list):
                    for para in section['content']:
                        if para.strip():
                            ET.SubElement(sec, 'p').text = para.strip()
                elif section['content'].strip():
                    ET.SubElement(sec, 'p').text = section['content'].strip()
            
            # Add figures
            if 'figures' in section:
                for fig in section['figures']:
                    self._add_figure(sec, fig)
            
            # Add tables
            if 'tables' in section:
                for table in section['tables']:
                    self._add_table(sec, table)
        
        return body
    
    def _create_back(self, metadata: Dict[str, Any]) -> Optional[ET.Element]:
        """Create back matter section"""
        has_acknowledgments = any(
            sec.get('type') == 'acknowledgments' 
            for sec in metadata.get('sections', [])
        )
        
        has_references = bool(metadata.get('references'))
        
        if not (has_acknowledgments or has_references):
            return None
            
        back = ET.Element('back')
        
        # Add acknowledgments
        if has_acknowledgments:
            ack_sec = next(
                sec for sec in metadata['sections'] 
                if sec.get('type') == 'acknowledgments'
            )
            ack = ET.SubElement(back, 'ack')
            ET.SubElement(ack, 'title').text = 'ACKNOWLEDGMENTS'
            ET.SubElement(ack, 'p').text = ack_sec.get('content', '')
        
        # Add author contributions and other footnotes
        fn_group = ET.SubElement(back, 'fn-group')
        
        # Author contributions
        # Author contributions
        contrib = ET.SubElement(fn_group, 'fn', {'fn-type': 'con'})
        ET.SubElement(contrib, 'label').text = 'AUTHOR CONTRIBUTIONS'
        ET.SubElement(contrib, 'p').text = metadata.get(
            'author_contributions',
            'All authors contributed to the study conception and design. '
            'The first draft of the manuscript was written by the first author '
            'and all authors commented on previous versions of the manuscript. '
            'All authors read and approved the final manuscript.'
        )
        
        # Conflicts of interest
        conflict_fn = ET.SubElement(fn_group, "fn")
        conflict_fn.set("fn-type", "conflict")
        conflict_label = ET.SubElement(conflict_fn, "label")
        conflict_label.text = "CONFLICTS OF INTEREST"
        conflict_p = ET.SubElement(conflict_fn, "p")
        conflict_p.text = metadata.get("conflicts_of_interest", 
                                     "The authors declare no conflict of interest.")
        
        # Acknowledgments
        ack = ET.SubElement(back, "ack")
        ack_title = ET.SubElement(ack, "title")
        ack_title.text = "ACKNOWLEDGMENTS"
        ack_p = ET.SubElement(ack, "p")
        ack_p.text = metadata.get("acknowledgments", 
                                "The authors would like to acknowledge the support received for this research.")
        
        # References
        if "references" in metadata and metadata["references"]:
            ref_list = ET.SubElement(back, "ref-list")
            ref_title = ET.SubElement(ref_list, "title")
            ref_title.text = "REFERENCES"
            
            for i, ref in enumerate(metadata["references"], 1):
                ref_elem = ET.SubElement(ref_list, "ref")
                ref_elem.set("id", f"r{i}")
                
                label = ET.SubElement(ref_elem, "label")
                label.text = str(i)
                
                mixed_citation = ET.SubElement(ref_elem, "mixed-citation")
                mixed_citation.set("publication-type", ref.get("type", "journal"))
                
                # Add authors
                if "authors" in ref:
                    for author in ref["authors"]:
                        string_name = ET.SubElement(mixed_citation, "string-name")
                        
                        if "last_name" in author:
                            surname = ET.SubElement(string_name, "surname")
                            surname.text = author["last_name"]
                        
                        if "first_name" in author:
                            given_names = ET.SubElement(string_name, "given-names")
                            given_names.text = author["first_name"]
                        
                        # Add comma after author names
                        if author != ref["authors"][-1]:
                            mixed_citation.text = ", "
                        else:
                            mixed_citation.text = ". "
                
                # Add article title
                if "title" in ref:
                    article_title = ET.SubElement(mixed_citation, "article-title")
                    article_title.text = ref["title"]
                    mixed_citation.text = ". "
                
                # Add source (journal name)
                if "source" in ref:
                    source = ET.SubElement(mixed_citation, "source")
                    source.text = ref["source"]
                    mixed_citation.text = ". "
                
                # Add year
                if "year" in ref:
                    year = ET.SubElement(mixed_citation, "year")
                    year.text = str(ref["year"])
                    mixed_citation.text = "; "
                
                # Add volume and issue
                if "volume" in ref:
                    volume = ET.SubElement(mixed_citation, "volume")
                    volume.text = str(ref["volume"])
                    
                    if "issue" in ref:
                        volume.text = f"{volume.text}({ref['issue']})"
                    
                    mixed_citation.text = ": "
                
                # Add page numbers
                if "fpage" in ref and "lpage" in ref:
                    fpage = ET.SubElement(mixed_citation, "fpage")
                    fpage.text = str(ref["fpage"])
                    
                    lpage = ET.SubElement(mixed_citation, "lpage")
                    lpage.text = str(ref["lpage"])
                    
                    mixed_citation.text = ". "
                
                # Add DOI if available
                if "doi" in ref:
                    pub_id = ET.SubElement(mixed_citation, "pub-id")
                    pub_id.set("pub-id-type", "doi")
                    pub_id.text = ref["doi"]
                    mixed_citation.text = ". "
        
        # Generate XML string with proper formatting
        xml_str = ET.tostring(article, encoding="unicode", method="xml")
        
        # Add XML declaration and DOCTYPE
        return (
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<!DOCTYPE article PUBLIC "-//NLM//DTD JATS (Z39.96) Journal Publishing DTD v1.1 20151215//EN" '
            '"JATS-journalpublishing1.dtd">\n'
            f"{xml_str}"
        )
        date_elem.extend([
            self._create_element('day', day),
            self._create_element('month', month),
            self._create_element('year', year)
        ])
    
    def _add_figure(self, parent: ET.Element, figure: Dict[str, Any]) -> None:
        """Add a figure to the document"""
        fig = ET.SubElement(parent, 'fig', {
            'id': figure.get('id', f'f{len(parent.findall(".//fig")) + 1}'),
            'position': 'float',
            'fig-type': 'figure'
        })
        
        ET.SubElement(fig, 'label').text = f'Figure {len(parent.findall(".//fig"))}'
        
        caption = ET.SubElement(fig, 'caption')
        ET.SubElement(caption, 'p').text = figure.get('caption', '')
        
        if 'graphic' in figure:
            ET.SubElement(fig, 'graphic', {
                'xlink:href': figure['graphic']
            })
    
    def _add_table(self, parent: ET.Element, table_data: Dict[str, Any]) -> None:
        """Add a table to the document"""
        table_wrap = ET.SubElement(parent, 'table-wrap', {
            'id': table_data.get('id', f't{len(parent.findall(".//table-wrap")) + 1}'),
            'position': 'float'
        })
        
        ET.SubElement(table_wrap, 'label').text = f'Table {len(parent.findall(".//table-wrap"))}'
        
        caption = ET.SubElement(table_wrap, 'caption')
        ET.SubElement(caption, 'p').text = table_data.get('caption', '')
        
        table = ET.SubElement(table_wrap, 'table', {
            'frame': 'hsides',
            'rules': 'groups'
        })
        
        # Add table content
        if 'headers' in table_data and table_data['headers']:
            thead = ET.SubElement(table, 'thead')
            tr = ET.SubElement(thead, 'tr')
            for header in table_data['headers']:
                ET.SubElement(tr, 'th').text = str(header)
        
        if 'rows' in table_data and table_data['rows']:
            tbody = ET.SubElement(table, 'tbody')
            for row in table_data['rows']:
                tr = ET.SubElement(tbody, 'tr')
                for cell in row:
                    ET.SubElement(tr, 'td').text = str(cell)
    
    def _add_journal_citation(self, parent: ET.Element, ref: Dict[str, Any], ref_num: int) -> None:
        """Add a journal article citation"""
        citation = ET.SubElement(parent, 'mixed-citation', {
            'publication-type': 'journal',
            'id': f'bib{ref_num}'
        })
        
        # Add authors
        if 'authors' in ref and ref['authors']:
            authors = []
            for i, author in enumerate(ref['authors']):
                name_parts = author.split()
                if len(name_parts) >= 2:
                    surname = name_parts[-1]
                    given_names = ' '.join(name_parts[:-1])
                    authors.append(f'<string-name><surname>{surname}</surname> <given-names>{given_names}</given-names></string-name>')
                else:
                    authors.append(f'<string-name><surname>{author}</surname></string-name>')
            
            citation.text = ', '.join(authors) + '. '
        
        # Add article title
        if 'title' in ref:
            title_elem = ET.SubElement(citation, 'article-title')
            title_elem.text = ref['title']
            citation.text = (citation.text or '') + ' '
        
        # Add journal title
        if 'journal' in ref:
            source_elem = ET.SubElement(citation, 'source')
            source_elem.text = ref['journal']
            citation.text = (citation.text or '') + '. '
        
        # Add year
        if 'year' in ref:
            year_elem = ET.SubElement(citation, 'year')
            year_elem.text = str(ref['year'])
            citation.text = (citation.text or '') + '; '
        
        # Add volume and issue
        if 'volume' in ref:
            vol_elem = ET.SubElement(citation, 'volume')
            vol_elem.text = str(ref['volume'])
            citation.text = (citation.text or '') + '(' + str(ref.get('issue', '')) + '):' if 'issue' in ref else ': '
        
        # Add pages
        if 'pages' in ref:
            fpage, lpage = ref['pages'].split('-') if '-' in ref['pages'] else (ref['pages'], '')
            fpage_elem = ET.SubElement(citation, 'fpage')
            fpage_elem.text = fpage
            if lpage:
                lpage_elem = ET.SubElement(citation, 'lpage')
                lpage_elem.text = lpage
        
        # Add DOI
        if 'doi' in ref:
            doi_elem = ET.SubElement(citation, 'pub-id', {'pub-id-type': 'doi'})
            doi_elem.text = ref['doi']
            citation.text = (citation.text or '') + '.'
    
    def _add_generic_citation(self, parent: ET.Element, ref: Dict[str, Any], ref_num: int) -> None:
        """Add a generic citation"""
        citation = ET.SubElement(parent, 'mixed-citation', {
            'id': f'bib{ref_num}'
        })
        
        # Build citation string
        parts = []
        
        # Add authors
        if 'authors' in ref and ref['authors']:
            authors = []
            for author in ref['authors']:
                name_parts = author.split()
                if len(name_parts) >= 2:
                    authors.append(f'{name_parts[-1]}, {" ".join(name_parts[:-1])}')
                else:
                    authors.append(author)
            parts.append(', '.join(authors) + '.')
        
        # Add year
        if 'year' in ref:
            parts[0] = parts[0] + f' ({ref["year"]}).' if parts else f'({ref["year"]}).'
        
        # Add title
        if 'title' in ref:
            title = ref['title']
            if not title.endswith(('.', '!', '?')):
                title += '.'
            parts.append(title)
        
        # Add source/publication info
        if 'source' in ref:
            parts.append(f'<i>{ref["source"]}</i>.')
        
        # Add DOI/URL if available
        if 'doi' in ref:
            parts.append(f'https://doi.org/{ref["doi"]}')
        elif 'url' in ref:
            parts.append(ref['url'])
        
        # Join all parts with spaces
        citation.text = ' '.join(parts)
    
    def _create_element(self, tag: str, text: str = '', **attrs) -> ET.Element:
        """Helper to create an XML element with text and attributes"""
        elem = ET.Element(tag, **attrs)
        if text:
            elem.text = str(text)
        return elem
    
    def _prettify(self, elem: ET.Element) -> str:
        """Return a pretty-printed XML string for the Element"""
        rough_string = ET.tostring(elem, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent='  ')


class EnhancedDocumentExtractor:
    """Enhanced document extractor with JATS XML generation capabilities"""
    
    def __init__(self, file_path: str, file_type: str):
        self.file_path = file_path
        self.file_type = file_type
        self.metadata = {
            "title": "",
            "authors": [],
            "abstract": "",
            "keywords": [],
            "sections": [],
            "references": [],
            "figures": [],
            "tables": [],
            "equations": [],
            "article_type": "research-article",
            "language": "en",
            "dates": {
                "received": {"day": "14", "month": "08", "year": "2024"},
                "accepted": {"day": "24", "month": "10", "year": "2024"},
                "published": {"day": "24", "month": "10", "year": "2024"}
            },
            "journal_meta": {
                "journal_id": "REVISIAMATERIA",
                "journal_title": "REVISIAMATERIA",
                "issn": "1517-7076"
            },
            "article_meta": {
                "doi": "10.1590/1517-7076-RMAT-2024-XXXX",
                "volume": "29",
                "issue": "4",
                "fpage": "e20240534"
            },
            "processing_metadata": {
                "page_count": 0,
                "word_count": 0,
                "character_count": 0,
                "image_count": 0,
                "table_count": 0,
                "formula_count": 0
            }
        }
        self.nlp = None
        self.jats_generator = JATSGenerator()
        self._load_nlp_model()
        
    def _load_nlp_model(self):
        """Load the spaCy NLP model"""
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except Exception as e:
            logger.warning(f"Could not load spaCy model: {str(e)}. Some NLP features will be disabled.")
            # Create a dummy NLP object with minimal functionality
            self.nlp = type('DummyNLP', (), {
                'pipe_names': [],
                'add_pipe': lambda *args, **kwargs: None,
                'pipe': lambda *args, **kwargs: [{'text': 'NLP processing disabled'}] if not args else None,
                '__call__': lambda self, text: type('Doc', (), {'sents': [type('Span', (), {'text': text, 'sentiment': 0.0})]})()
            })()
    
    def extract(self) -> str:
        """
        Extract content from the document and generate JATS XML
        """
        start_time = time.time()
        xml_path = ""
        
        try:
            logger.info(f"Starting extraction for file: {self.file_path} (type: {self.file_type})")
            
            # Process the document based on file type
            if self.file_type == 'application/pdf':
                logger.info("Processing PDF file")
                self._process_pdf()
            elif 'word' in self.file_type or 'officedocument' in self.file_type:
                logger.info("Processing Word document")
                self._process_docx()
            else:
                error_msg = f"Unsupported file type: {self.file_type}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            logger.info("Document processed successfully, generating JATS XML")
            
            # Generate JATS XML
            try:
                jats_xml = self.jats_generator.generate_jats(self.metadata)
                logger.info("JATS XML generated successfully")
            except Exception as e:
                logger.error(f"Error generating JATS XML: {str(e)}", exc_info=True)
                raise RuntimeError(f"Failed to generate JATS XML: {str(e)}")
            
            # Save the XML to a file
            base_path = os.path.splitext(self.file_path)[0]
            xml_path = f"{base_path}.xml"
            
            try:
                # Ensure the directory exists
                os.makedirs(os.path.dirname(os.path.abspath(xml_path)), exist_ok=True)
                logger.info(f"Saving XML to: {xml_path}")
                
                with open(xml_path, 'w', encoding='utf-8') as f:
                    f.write(jats_xml)
                
                # Update metadata
                self.metadata['processing_metadata']['processing_time'] = time.time() - start_time
                self.metadata['xml_path'] = xml_path
                
                logger.info(f"Successfully generated JATS XML at: {xml_path}")
                return xml_path
                
            except Exception as file_error:
                logger.error(f"Failed to save XML file: {str(file_error)}")
                raise
            
        except Exception as e:
            logger.error(f"Error during extraction: {str(e)}", exc_info=True)
            raise
            
    def _process_pdf(self) -> None:
        """
        Process a PDF document and extract content
        """
        try:
            # Open the PDF file
            doc = fitz.open(self.file_path)
            self.metadata['processing_metadata']['page_count'] = len(doc)
            
            # Extract text and metadata
            full_text = ""
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                full_text += f"\n\n{text}"
                
                # Extract images (placeholder for actual image extraction)
                images = page.get_images(full=True)
                if images:
                    self.metadata['processing_metadata']['image_count'] += len(images)
            
            # Process the extracted text
            self._process_text(full_text)
            
            # Extract metadata if available
            if doc.metadata:
                self._extract_metadata_from_dict(doc.metadata)
                
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}", exc_info=True)
            raise
    
    def _process_docx(self) -> None:
        """
        Process a DOCX document and extract content
        """
        try:
            import docx2txt
            
            # Extract text from DOCX
            text = docx2txt.process(self.file_path)
            
            # Process the extracted text
            self._process_text(text)
            
            # Extract metadata if available
            try:
                from docx import Document
                doc = Document(self.file_path)
                self.metadata['processing_metadata']['page_count'] = len(doc.paragraphs) // 50 + 1  # Estimate
                
                # Extract core properties if available
                if hasattr(doc, 'core_properties'):
                    props = {
                        'title': doc.core_properties.title,
                        'author': doc.core_properties.author,
                        'created': str(doc.core_properties.created),
                        'modified': str(doc.core_properties.modified),
                        'subject': doc.core_properties.subject,
                        'keywords': doc.core_properties.keywords,
                        'category': doc.core_properties.category,
                        'comments': doc.core_properties.comments
                    }
                    self._extract_metadata_from_dict(props)
                    
            except Exception as e:
                logger.warning(f"Could not extract DOCX metadata: {str(e)}")
                
        except Exception as e:
            logger.error(f"Error processing DOCX: {str(e)}", exc_info=True)
            raise
    
    def _process_text(self, text: str) -> None:
        """
        Process extracted text to identify document structure and metadata
        """
        if not text.strip():
            return
        
        # Update word and character counts
        words = text.split()
        self.metadata['processing_metadata']['word_count'] = len(words)
        self.metadata['processing_metadata']['character_count'] = len(text)
        
        # Detect language if not already set
        if not self.metadata.get('language'):
            try:
                self.metadata['language'] = detect(text[:5000])
            except:
                self.metadata['language'] = 'en'  # Default to English
        
        # Process with spaCy for better text analysis
        doc = self.nlp(text)
        
        # Extract title if not already set
        if not self.metadata.get('title'):
            # Use the first non-empty line as title
            for line in text.split('\n'):
                line = line.strip()
                if line and len(line) > 10:  # Basic heuristic for title
                    self.metadata['title'] = line
                    break
        
        # Extract abstract (first paragraph after title)
        if not self.metadata.get('abstract'):
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            if len(paragraphs) > 1 and len(paragraphs[1]) > 50:  # Heuristic for abstract
                self.metadata['abstract'] = paragraphs[1]
        
        # Extract sections (simplified)
        self._extract_sections(text)
    
    def _extract_sections(self, text: str) -> None:
        """
        Extract document sections based on headings
        """
        sections = []
        current_section = None
        
        # Split text into lines and process each line
        lines = text.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Check for section headers (simplified)
            if (line.isupper() and len(line) < 100 and 
                not any(c.isdigit() for c in line) and 
                line.endswith(('.', ':', ''))):
                
                # Save previous section if exists
                if current_section:
                    sections.append(current_section)
                
                # Start new section
                current_section = {
                    'type': self._classify_section(line),
                    'title': line,
                    'content': ''
                }
            elif current_section:
                # Add content to current section
                if line.strip():
                    if current_section['content']:
                        current_section['content'] += '\n' + line
                    else:
                        current_section['content'] = line
            
            i += 1
        
        # Add the last section
        if current_section:
            sections.append(current_section)
        
        # If no sections found, create a single section with all content
        if not sections and text.strip():
            sections = [{
                'type': 'other',
                'title': 'Content',
                'content': text.strip()
            }]
        
        self.metadata['sections'] = sections
    
    def _classify_section(self, title: str) -> str:
        """Classify section based on its title"""
        title_lower = title.lower()
        
        if 'abstract' in title_lower:
            return 'abstract'
        elif 'introduction' in title_lower:
            return 'introduction'
        elif 'method' in title_lower or 'experiment' in title_lower:
            return 'methodology'
        elif 'result' in title_lower or 'finding' in title_lower:
            return 'results'
        elif 'discussion' in title_lower:
            return 'discussion'
        elif 'conclusion' in title_lower or 'summary' in title_lower:
            return 'conclusion'
        elif 'reference' in title_lower or 'bibliography' in title_lower:
            return 'references'
        elif 'acknowledg' in title_lower:
            return 'acknowledgments'
        else:
            return 'other'
    
    def _extract_metadata_from_dict(self, metadata: Dict[str, Any]) -> None:
        """Extract metadata from a dictionary (e.g., PDF info or DOCX properties)"""
        if not metadata:
            return
        
        # Map common metadata fields
        field_mapping = {
            'title': 'title',
            'subject': 'subject',
            'author': 'authors',
            'keywords': 'keywords',
            'creator': 'creator',
            'producer': 'producer',
            'creationdate': 'created',
            'moddate': 'modified'
        }
        
        for src_field, target_field in field_mapping.items():
            if src_field not in metadata or not metadata[src_field]:
                continue
                
            try:
                # Handle IndirectObject and other special types by converting to string
                field_value = metadata[src_field]
                
                # Handle PyMuPDF IndirectObject and other special types
                if hasattr(field_value, '__class__') and 'IndirectObject' in str(field_value.__class__):
                    # For IndirectObject, try to resolve it first
                    try:
                        resolved = field_value.resolve()
                        field_value = str(resolved) if resolved is not None else ''
                    except Exception:
                        field_value = str(field_value)
                elif hasattr(field_value, 'get'):  # Check if it's a dictionary-like object
                    field_value = str(field_value.get('', field_value))
                else:
                    field_value = str(field_value)
                
                if not field_value:
                    continue
                    
                if target_field == 'authors':
                    if isinstance(field_value, str):
                        self.metadata['authors'] = [{'name': a.strip()} for a in field_value.split(';') if a.strip()]
                elif target_field == 'keywords' and isinstance(field_value, str):
                    self.metadata['keywords'] = [k.strip() for k in field_value.split(';') if k.strip()]
                else:
                    # Only set if we have a non-empty value
                    self.metadata[target_field] = field_value
                    
            except Exception as e:
                logger.warning(f"Error processing metadata field '{src_field}': {str(e)}")
                continue
    
    def _extract_from_pdf(self) -> Tuple[str, List[Dict], List[Dict], Dict]:
        """Enhanced PDF extraction with layout analysis"""
        import fitz  # PyMuPDF
        
        text = ""
        images = []
        formulas = []
        structure = {"sections": [], "tables": [], "figures": []}
        
        try:
            doc = fitz.open(self.file_path)
            self.metadata["page_count"] = len(doc)
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # Extract text with layout preservation
                text_dict = page.get_text("dict")
                
                # Process blocks (paragraphs, headers, etc.)
                for block in text_dict.get("blocks", []):
                    if "lines" in block:
                        block_text = ""
                        for line in block["lines"]:
                            for span in line["spans"]:
                                block_text += span["text"] + " "
                        
                        # Basic section detection
                        if self._is_heading(block_text):
                            structure["sections"].append({
                                "text": block_text.strip(),
                                "level": self._get_heading_level(block_text),
                                "page": page_num + 1
                            })
                        
                        text += block_text + "\n\n"
                
                # Extract images
                image_list = page.get_images(full=True)
                for img_index, img in enumerate(image_list):
                    image = self._extract_image(doc, img)
                    if image:
                        images.append({
                            "data": image,
                            "page": page_num + 1,
                            "index": img_index
                        })
                        self.metadata["image_count"] += 1
            
            # Detect document language
            self._detect_language(text)
            
            return text, images, formulas, structure
            
        except Exception as e:
            logger.error(f"Error extracting from PDF: {str(e)}")
            raise
    
    def _process_with_nlp(self, text: str) -> Dict:
        """Process extracted text with NLP for better structure"""
        doc = self.nlp(text)
        
        # Extract named entities
        entities = [{"text": ent.text, "label": ent.label_, "start": ent.start_char, "end": ent.end_char} 
                   for ent in doc.ents]
        
        # Extract key phrases (simple implementation)
        key_phrases = [chunk.text for chunk in doc.noun_chunks]
        
        return {
            "raw_text": text,
            "entities": entities,
            "key_phrases": key_phrases,
            "sentences": [sent.text for sent in doc.sents]
        }
    
    def _create_enhanced_xml(self, content: Dict, images: List, formulas: List, structure: Dict) -> str:
        """Create enhanced XML with semantic markup"""
        # Implementation for creating enhanced XML
        # This would include the document structure, entities, etc.
        pass
    
    def _is_heading(self, text: str) -> bool:
        """Determine if a text block is a heading"""
        # Simple heuristic - can be enhanced with ML
        text = text.strip()
        if not text:
            return False
        
        # Check if text is all uppercase and not too long
        if text.isupper() and len(text) < 100:
            return True
            
        # Check if text ends with a colon and is not too long
        if text.endswith(':') and len(text) < 100:
            return True
            
        return False
    
    def _get_heading_level(self, text: str) -> int:
        """Determine heading level (1-6)"""
        # Simple heuristic - can be enhanced
        text = text.strip()
        if text.isupper() and len(text) < 50:
            return 1
        if text.isupper() and len(text) < 100:
            return 2
        if text.endswith(':'):
            return 3
        return 4
    
    def _detect_language(self, text: str) -> None:
        """Detect language of the document"""
        try:
            # Use first 1000 chars for language detection
            sample = text[:1000]
            if sample.strip():
                lang = detect(sample)
                self.metadata["languages"].append(lang)
        except LangDetectException as e:
            logger.warning(f"Language detection failed: {str(e)}")
        except Exception as e:
            logger.warning(f"Error in language detection: {str(e)}")

# Example usage:
if __name__ == "__main__":
    # Example usage
    extractor = EnhancedDocumentExtractor("example.pdf", "application/pdf")
    xml_path = extractor.extract()
    print(f"Extraction complete. XML saved to: {xml_path}")
    print(f"Metadata: {extractor.metadata}")
