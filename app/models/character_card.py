"""Character card data model."""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass
class CharacterCard:
    """Character card data structure."""
    
    spec: str
    spec_version: str
    character_version: str
    avatar: str
    creator: str
    creator_notes: str

    tags: List[str]
    name: str
    description: str
    personality: str
    scenario: str
    first_mes: str
    alternate_greetings: List[str]
    mes_example: str

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
            
            spec = getField("spec", "")
            spec_version = getField("spec_version", "")
            character_version = getField("character_version", "")
            avatar = getField("avatar", "")
            creator = getField("creator", "")
            creator_notes = getField("creator_notes", "")

            tags = getField("tags", [])
            name = getField("name", "Unknown")
            description = getField("description", "")
            personality = getField("personality", "")
            scenario = getField("scenario", "")
            first_mes = getField("first_mes", "")
            alternate_greetings = getField("alternate_greetings", [])
            mes_example = getField("mes_example", "")

            # Ensure tags is a list
            if not isinstance(tags, list):
                tags = []

            # Ensure alternateGreetings is a list
            if not isinstance(alternate_greetings, list):
                alternate_greetings = []

            return cls(
                spec=spec if spec else "",
                spec_version=spec_version if spec_version else "",
                character_version=character_version if character_version else "",
                avatar=avatar if avatar else "",
                creator=creator if creator else "",
                creator_notes=creator_notes if creator_notes else "",

                tags=tags,
                name=name if name else "Unknown",
                description=description if description else "",
                personality=personality if personality else "",
                scenario=scenario if scenario else "",
                first_mes=first_mes if first_mes else "",
                alternate_greetings=alternate_greetings,
                mes_example=mes_example if mes_example else "",

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
            return self.first_mes
        
        altIndex = index - 1
        if 0 <= altIndex < len(self.alternate_greetings):
            return self.alternate_greetings[altIndex]
        
        return self.first_mes
    
    def getGreetingsCount(self) -> int:
        """Get total number of greetings (first_mes + alternate_greetings)."""
        return 1 + len(self.alternate_greetings)

    def evaluateFilters(self, filterName: str, filterCreator: str, filterTags: str, filterDescr: str):
        if filterName and (filterName.lower().strip() not in self.name.lower()):
            self.isFiltered = True
            return

        if filterCreator and (filterCreator.lower().strip() not in self.creator.lower()):
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

