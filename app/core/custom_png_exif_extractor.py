"""EXIF data extraction using custom parsing."""

import struct
from typing import Dict, Optional, List, Callable
from pathlib import Path

class CustomPngExifExtractor:
    """Extract EXIF data from PNG files using custom parsing."""
    
    BATCH_SIZE = 100  # Process files in batches
    
    def __init__(self):
        """
        Initialize EXIF extractor.
        """

    def _extract_chunks(self, filePath: Path, tag: str):
        with open(filePath, "rb") as f:
            data = f.read()

        # PNG signature
        if data[:8] != b"\x89PNG\r\n\x1a\n":
            raise ValueError("Not a PNG file")

        pos = 8
        chunks = []

        while pos < len(data):
            if pos + 8 > len(data):
                break

            length = struct.unpack(">I", data[pos:pos + 4])[0]
            chunk_type = data[pos + 4:pos + 8]
            chunk_data_start = pos + 8
            chunk_data_end = chunk_data_start + length
            chunk_data = data[chunk_data_start:chunk_data_end]

            # tEXt: keyword\0text
            if chunk_type == b"tEXt":
                # keyword is up to first null byte
                if b"\x00" in chunk_data:
                    keyword, text = chunk_data.split(b"\x00", 1)
                    if keyword.decode("latin-1", errors="ignore") == tag:
                        chunks.append(text)

            # iTXt: keyword\0compression_flag\0compression_method\0lang\0translated\0text
            elif chunk_type == b"iTXt":
                parts = chunk_data.split(b"\x00", 5)
                if len(parts) == 6:
                    keyword = parts[0]
                    # compression_flag = parts[1]
                    # compression_method = parts[2]
                    # lang = parts[3]
                    # translated = parts[4]
                    text = parts[5]

                    if keyword.decode("latin-1", errors="ignore") == tag:
                        # if compressed, you’d need to decompress here; most cards are uncompressed
                        chunks.append(text)

            # advance to next chunk (data + CRC)
            pos = chunk_data_end + 4

        return chunks

    def _get_first_chunk(self, filePath: Path, tag: str):
        chunks = self._extract_chunks(filePath, tag)
        if not chunks:
            return None
        return chunks[0].decode("utf-8", errors="replace")

    def _get_largest_chunk(self, filePath: Path, tag: str):
        chunks = self._extract_chunks(filePath, tag)
        if not chunks:
            return None
        largest = max(chunks, key=len)
        return largest.decode("utf-8", errors="replace")

    def _extractBatch(self, files: List[Path], tag: str) -> Dict[str, str]:
        """
        Extract EXIF data from a batch of files using JSON output.
        
        Args:
            files: List of file paths
            tag: EXIF tag to extract (e.g., "chara" or "Ccv3")
            
        Returns:
            Dictionary mapping file paths to base64 data
        """
        if not files:
            return {}
        
        result = {}
        
        for file in files:
            data = self._extractSingleFile(file, tag)
            if data:
                result[str(file.resolve())] = data

        return result
    
    def _extractSingleFile(self, filePath: Path, tag: str) -> Optional[str]:
        """
        Extract EXIF data from a single file.

        Args:
            filePath: Path to file
            tag: EXIF tag to extract

        Returns:
            Base64 data or None
        """

        return self._get_first_chunk(filePath, tag)
        # return self._get_largest_chunk(filePath, tag)

    def extractFromDirectory(
        self,
        directoryPath: str,
        recursive: bool = False,
        progressCallback: Optional[Callable[[int, int], None]] = None
    ) -> Dict[str, Optional[str]]:
        """
        Extract EXIF data from all PNG files in a directory.

        Args:
            directoryPath: Path to directory containing PNG files
            progressCallback: Optional callback(current, total) for progress updates
            recursive: Whether to search subdirectories

        Returns:
            Dictionary mapping file paths to Base64 encoded EXIF data
        """
        result = {}
        directory = Path(directoryPath)

        if not directory.exists() or not directory.is_dir():
            return result

        # Get PNG files
        if recursive:
            pngFiles = list(directory.rglob("*.png"))
        else:
            pngFiles = list(directory.glob("*.png"))

        if not pngFiles:
            return result

        totalFiles = len(pngFiles)
        processedFiles = 0

        # Process files in batches using JSON output
        for i in range(0, totalFiles, self.BATCH_SIZE):
            batch = pngFiles[i:i + self.BATCH_SIZE]

            # Try primary tag (chara)
            batchResult = self._extractBatch(batch, "chara")
            result.update(batchResult)

            # Try fallback tag (Ccv3) for files without data
            missingFiles = [f for f in batch if str(f.resolve()) not in result]
            if missingFiles:
                fallbackResult = self._extractBatch(missingFiles, "Ccv3")
                for path, data in fallbackResult.items():
                    if path not in result:
                        result[path] = data

            # For any still missing, try individual extraction
            stillMissing = [f for f in batch if str(f.resolve()) not in result]
            for f in stillMissing:
                data = self._extractSingleFile(f, "chara")
                if not data:
                    data = self._extractSingleFile(f, "Ccv3")
                if data:
                    result[str(f.resolve())] = data

            processedFiles += len(batch)
            if progressCallback:
                progressCallback(processedFiles, totalFiles)

        return result
    
    def extractFromFile(self, filePath: str) -> Optional[str]:
        """
        Extract EXIF data from a single PNG file.
        
        Args:
            filePath: Path to PNG file
            
        Returns:
            Base64 encoded EXIF data or None if not found
        """
        file = Path(filePath)
        if not file.exists() or not file.suffix.lower() == ".png":
            return None
        
        # Try primary tag
        data = self._extractSingleFile(file, "chara")
        if data:
            return data
        
        # Try fallback tag
        data = self._extractSingleFile(file, "Ccv3")
        return data
