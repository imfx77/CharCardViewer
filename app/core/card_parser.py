"""Parse character card data from Base64 encoded JSON."""

import base64
import json
from typing import Optional, Dict, Any

from app.models.character_card import CharacterCard


class CardParser:
    """Parse character card data from EXIF metadata."""
    
    def __init__(self):
        """Initialize card parser."""
        self.cache: Dict[str, Optional[CharacterCard]] = {}
    
    def parseBase64(self, base64Data: str, filePath: str) -> Optional[CharacterCard]:
        """
        Parse Base64 encoded JSON into CharacterCard.
        
        Args:
            base64Data: Base64 encoded JSON string
            filePath: Path to the source PNG file
            
        Returns:
            CharacterCard instance or None if parsing fails
        """
        # Check cache
        if filePath in self.cache:
            return self.cache[filePath]
        
        try:
            # Clean up base64 data (remove any whitespace/newlines)
            cleanBase64 = base64Data.strip().replace("\n", "").replace("\r", "")
            
            # Add padding if needed
            padding = 4 - (len(cleanBase64) % 4)
            if padding != 4:
                cleanBase64 += "=" * padding

            # Decode Base64
            try:
                jsonBytes = base64.b64decode(cleanBase64)
            except Exception:
                # Try without padding fix
                jsonBytes = base64.b64decode(base64Data.strip())

            # Try UTF-8 first, then other encodings
            jsonStr = None
            for encoding in ["utf-8", "utf-8-sig", "latin-1"]:
                try:
                    jsonStr = jsonBytes.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if jsonStr is None:
                print(f"[WARNING] Could not decode {filePath}: encoding error")
                self.cache[filePath] = None
                return None

            # Parse JSON - handle "Extra data" errors by finding valid JSON
            data = None
            try:
                data = json.loads(jsonStr)
            except json.JSONDecodeError as e:
                if "Extra data" in str(e):
                    # Try to find where valid JSON ends
                    # The error gives us the position of extra data
                    try:
                        # Parse up to the error position
                        validJson = jsonStr[:e.pos]
                        # Find the last complete JSON object
                        braceCount = 0
                        lastValidEnd = 0
                        for i, char in enumerate(validJson):
                            if char == '{':
                                braceCount += 1
                            elif char == '}':
                                braceCount -= 1
                                if braceCount == 0:
                                    lastValidEnd = i + 1
                        if lastValidEnd > 0:
                            data = json.loads(jsonStr[:lastValidEnd])
                    except Exception:
                        pass
                
                if data is None:
                    raise e
            
            # Validate structure
            if not isinstance(data, dict):
                print(f"[WARNING] Invalid JSON structure in {filePath}: not a dict")
                self.cache[filePath] = None
                return None
            
            # Create CharacterCard (accept any valid structure)
            card = CharacterCard.fromJson(data, filePath)
            self.cache[filePath] = card
            return card
        
        except json.JSONDecodeError as e:
            print(f"[WARNING] JSON decode error in {filePath}: {e}")
            self.cache[filePath] = None
            return None
        except Exception as e:
            print(f"[WARNING] Failed to parse {filePath}: {e}")
            self.cache[filePath] = None
            return None
    
    def parseFile(self, filePath: str, base64Data: Optional[str] = None) -> Optional[CharacterCard]:
        """
        Parse character card from file path.
        
        Args:
            filePath: Path to PNG file
            base64Data: Optional pre-extracted Base64 data
            
        Returns:
            CharacterCard instance or None if parsing fails
        """
        if base64Data is None:
            from app.core.custom_png_exif_extractor import CustomPngExifExtractor
            extractor = CustomPngExifExtractor()
            base64Data = extractor.extractFromFile(filePath)
        
        if base64Data is None:
            return None
        
        return self.parseBase64(base64Data, filePath)
    
    def clearCache(self):
        """Clear the parsing cache."""
        self.cache.clear()

