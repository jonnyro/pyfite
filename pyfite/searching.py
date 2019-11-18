"""Utility classes for searching directories and archives.
"""

import os
import re
import zipfile
from typing import Generator, List, Pattern, Tuple

class ArchiveSearcher:
    """Searches through archive contents without extracting any data.

    Note:
        It is assumed that the archive located at ``path`` exists
        and is of the ZIP format, but the file extension need not
        be ".zip".

        Values returned are, unless otherwise stated, full paths
        to the relevant file relative to the archive root.

    Args:
        path (str): The path to an archive to search

    Raises:
        zipfile.BadZipFile: If ``path`` isn't a ZIP file (regardless of extension)
    """
    def __init__(self, path: str):
        self._archive = zipfile.ZipFile(path, 'r')

    def __del__(self):
        self._archive.close()

    def _findAll(self, pattern: Pattern[str], requireMatch=False) -> Generator[str, None, None]:
        """Finds all files in the archive that match ``pattern``.

        Args:
            pattern (Pattern[str]): The pattern to use for matching
            requireMatch (bool): Whether matches must begin at the beginning of the string

        Returns:
            Generator[str]: A generator that yields matched paths
        """
        predFunc = re.match if requireMatch else re.search
        return (entry.filename for entry in self._archive.infolist() if predFunc(pattern, entry.filename) and entry.file_size > 0)

    def findAll(self, pattern: Pattern[str], requireMatch=False) -> List[str]:
        """Finds all files in the archive that match ``pattern``.

        Args:
            pattern (Pattern[str]): The pattern to use for matching
            requireMatch (bool): Whether matches must begin at the beginning of the string

        Returns:
            List[str]: The list of all files that matched ``pattern``
        """
        return list(self._findAll(pattern, requireMatch))

    def findFirst(self, pattern: Pattern[str], requireMatch=False) -> str:
        """Finds the first file in the archive that matches ``pattern``.

        Args:
            pattern (Pattern[str]): The pattern to use for matching
            requireMatch (bool): Whether matches must begin at the beginning of the string

        Returns:
            None: If no files matched Pattern[str]
            str: The first file that matched ``pattern``
        """
        return next(self._findAll(pattern, requireMatch), None)

class StplsBundleSearcher(ArchiveSearcher):
    """Intelligently searches through STPLS Bundles.

    STPLS Bundles have a known structure and known contents. This class
    can leverage that knowledge and provide convenience methods that leverage
    that information for simpler patterns and fewer function calls.

    See documentation for ``ArchiveSearcher`` for construction information.
    """
    def findMetadata(self) -> str:
        """Locates the metadata.xml in the bundle.

        Returns:
            None: If there is no metadata.xml
            str: The location of the metadata.xml file in the archive
        """
        return self.findFirst(re.compile('.*metadata.xml$', re.IGNORECASE), requireMatch=True)

    def findObjsAndSupplements(self, pattern: Pattern[str]) -> Tuple[str, List[str]]:
        """Finds the metadata.xml and matching Objs.

        All files adjacent to or in sibling/sub-sibling directories of a metadata.xml
        are assumed to be supplemental and will all be checked for match with ``pattern``

        Args:
            pattern (Pattern[str]): The pattern to use for matching

        Returns:
            (None, []): If a metadata.xml wasn't found
            Tuple[str,List[str]]: A metadata.xml and all supplemental Objs/textures/materials
                                  that matched ``pattern``
        """
        metadataPath = self.findMetadata()
        if not metadataPath:
            return (None, [])

        # Constructing a new pattern for supplements so need string form of pattern
        if not isinstance(pattern, str):
            pattern = pattern.pattern

        metadataDir = metadataPath[:metadataPath.rfind('/') + 1]
        return (metadataPath, self.findAll(re.compile(f'^{metadataDir}.*{pattern}.*')))

class DirectorySearcher:
    """Searches recursively through directories for files matching a pattern.

    Note:
        Values returned are, unless otherwise stated, absolute paths.

    Args:
        root (str): The root path in which to search for files

    Raises:
        NotADirectoryError: If ``root`` is not an existing directory
    """
    def __init__(self, root: str):
        self._root = root
        if not os.path.isdir(self._root):
            raise NotADirectoryError()

    def _findAll(self, pattern: Pattern[str], requireMatch=False) -> Generator[str, None, None]:
        """Finds all files in the root directory that match ``pattern``.

        Args:
            pattern (Pattern[str]): The pattern to use for matching
            requireMatch (bool): Whether matches must begin at the beginning of the string

        Returns:
            Generator[str]: A generator that yields matched paths
        """
        predFunc = re.match if requireMatch else re.search
        def gen():
            for root, _, files in os.walk(self._root):
                for file in files:
                    path = os.path.join(root, file)
                    if predFunc(pattern, path):
                        yield path
        return gen()

    def findAll(self, pattern: Pattern[str], requireMatch=False) -> List[str]:
        """Finds all files in the root directory that match ``pattern``.

        Args:
            pattern (Pattern[str]): The pattern to use for matching
            requireMatch (bool): Whether matches must begin at the beginning of the string

        Returns:
            List[str]: The list of all files that matched ``pattern``
        """
        return list(self._findAll(pattern, requireMatch))

    def findFirst(self, pattern: Pattern[str], requireMatch=False) -> str:
        """Finds the first file in the root directory that matches ``pattern``.

        Args:
            pattern (Pattern[str]): The pattern to use for matching
            requireMatch (bool): Whether matches must begin at the beginning of the string

        Returns:
            None: If no files matched ``pattern``
            str: The first file that matched ``pattern``
        """
        return next(self._findAll(pattern, requireMatch))
