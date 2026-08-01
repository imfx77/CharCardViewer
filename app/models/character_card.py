"""Character card data model."""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass
class CharacterCard:
    """Character card data structure."""
    
    name: str
    description: str
    personality: str
    scenario: str
    firstMes: str
    alternateGreetings: List[str]
    tags: List[str]
    filePath: str
    isFiltered : bool
    
    @classmethod
    def fromJson(cls, data: Dict[str, Any], filePath: str) -> Optional["CharacterCard"]:
        """
        Create CharacterCard from JSON data.
        
        Supports multiple formats:
        - V2/V3 with 'data' wrapper
        - Direct structure (no wrapper)
        - Mixed (both top-level and data wrapper)
        
        Args:
            data: JSON data dictionary
            filePath: Path to the source PNG file
            
        Returns:
            CharacterCard instance or None if parsing fails
        """
        try:
            # Try to get data from 'data' wrapper first (V2/V3 format)
            cardData = data.get("data", {})
            
            # Helper to get field from cardData first, then fall back to top-level
            def getField(fieldName: str, default: Any = "") -> Any:
                value = cardData.get(fieldName)
                if value is None or value == "":
                    value = data.get(fieldName, default)
                return value if value is not None else default
            
            name = getField("name", "Unknown")
            description = getField("description", "")
            personality = getField("personality", "")
            scenario = getField("scenario", "")
            firstMes = getField("first_mes", "")
            alternateGreetings = getField("alternate_greetings", [])
            tags = getField("tags", [])
            
            # Ensure alternateGreetings is a list
            if not isinstance(alternateGreetings, list):
                alternateGreetings = []
            
            # Ensure tags is a list
            if not isinstance(tags, list):
                tags = []
            
            return cls(
                name=name if name else "Unknown",
                description=description if description else "",
                personality=personality if personality else "",
                scenario=scenario if scenario else "",
                firstMes=firstMes if firstMes else "",
                alternateGreetings=alternateGreetings,
                tags=tags,
                filePath=filePath,
                isFiltered=False
            )
        except Exception as e:
            print(f"[WARNING] Failed to parse card {filePath}: {e}")
            return None
    
    def getCurrentGreeting(self, index: int = 0) -> str:
        """
        Get greeting message by index.
        
        Args:
            index: 0 for first_mes, 1+ for alternate_greetings
            
        Returns:
            Greeting message string
        """
        if index == 0:
            return self.firstMes
        
        altIndex = index - 1
        if 0 <= altIndex < len(self.alternateGreetings):
            return self.alternateGreetings[altIndex]
        
        return self.firstMes
    
    def getGreetingCount(self) -> int:
        """Get total number of greetings (first_mes + alternate_greetings)."""
        return 1 + len(self.alternateGreetings)

    def evaluateFilters(self,filterTags: str, filterName: str, filterDescr: str):
        if filterName and (filterName.lower().strip() not in self.name.lower()):
            self.isFiltered = True
            return

        if filterDescr:
            splitDescrFilters = filterDescr.split("|")
            for descrFilter in splitDescrFilters:
                if descrFilter.lower().strip() not in self.description.lower():
                    self.isFiltered = True
                    return

        if filterTags:
            splitTagFilters = filterTags.split("|")
            for tagFilter in splitTagFilters:
                if all(tagFilter.lower().strip() not in tag.lower() for tag in self.tags):
                    self.isFiltered = True
                    return

        self.isFiltered = False

