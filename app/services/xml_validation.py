import os
import re
import logging
import xml.etree.ElementTree as ET
from typing import Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class XMLValidator:
    def __init__(self, xml_path: str):
        self.xml_path = xml_path
    
    def validate(self) -> Tuple[bool, str]:
        """
        Validate XML file against the required rules
        Returns tuple of (is_valid, message)
        """
        try:
            # Parse XML file
            tree = ET.parse(self.xml_path)
            root = tree.getroot()
            
            # Check for required root element
            if root.tag != "ebook":
                return False, "Root element must be 'ebook'"
            
            # Check for required metadata
            metadata = root.find("metadata")
            if metadata is None:
                return False, "Missing 'metadata' element"
            
            # Check for required content
            content = root.find("content")
            if content is None:
                return False, "Missing 'content' element"
            
            # Validate <ddt> tags
            ddt_elements = root.findall(".//ddt")
            if not ddt_elements:
                return False, "Missing <ddt> tags for date/time entries"
            
            for ddt in ddt_elements:
                if ddt.text is None or not self._is_valid_datetime(ddt.text):
                    return False, f"Invalid date/time format in <ddt>: {ddt.text}"
            
            # Validate <ent> tags
            ent_elements = root.findall(".//ent")
            if not ent_elements:
                return False, "Missing <ent> tags for entity entries"
            
            for ent in ent_elements:
                if "type" not in ent.attrib:
                    return False, "Each <ent> tag must have a 'type' attribute"
                if ent.text is None or len(ent.text.strip()) == 0:
                    return False, f"Empty content in <ent> tag with type '{ent.attrib['type']}'"
            
            return True, "XML is valid"
            
        except ET.ParseError as e:
            return False, f"XML parsing error: {str(e)}"
        except Exception as e:
            logger.error(f"Error validating XML: {str(e)}")
            return False, f"Error validating XML: {str(e)}"
    
    def _is_valid_datetime(self, dt_str: str) -> bool:
        """
        Check if string is a valid datetime format
        """
        try:
            # Try various datetime formats
            formats = [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d",
                "%d/%m/%Y",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%SZ"
            ]
            
            for fmt in formats:
                try:
                    datetime.strptime(dt_str.strip(), fmt)
                    return True
                except ValueError:
                    continue
            
            return False
        except Exception:
            return False