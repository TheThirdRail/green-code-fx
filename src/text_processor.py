"""
Smart Text Processing Service for Green-Code FX.

This module provides automatic programming language detection, syntax highlighting,
and enhanced text processing for better typing effect visualization with support
for multiple file formats and markdown processing.
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, NamedTuple
from dataclasses import dataclass
from enum import Enum
import structlog

try:
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name, get_lexer_for_filename, guess_lexer
    from pygments.formatters import get_formatter_by_name
    from pygments.token import Token
    from pygments.util import ClassNotFound
    PYGMENTS_AVAILABLE = True
except ImportError:
    PYGMENTS_AVAILABLE = False

try:
    from .config import config
except ImportError:
    # Handle direct execution
    from config import config


logger = structlog.get_logger()


class SyntaxToken(NamedTuple):
    """Represents a syntax token with color information."""
    text: str
    token_type: str
    color: str
    start_pos: int
    end_pos: int


@dataclass
class LanguageInfo:
    """Information about detected language."""
    name: str
    aliases: List[str]
    file_extensions: List[str]
    confidence: float
    detection_method: str


@dataclass
class ProcessedText:
    """Processed text with syntax highlighting information."""
    original_text: str
    language_info: LanguageInfo
    tokens: List[SyntaxToken]
    lines: List[str]
    total_characters: int
    estimated_typing_time: float


class TextProcessor:
    """
    Smart text processing service with language detection and syntax highlighting.
    """
    
    def __init__(self):
        """Initialize the text processor."""
        self.supported_extensions = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.hpp': 'cpp',
            '.cs': 'csharp',
            '.php': 'php',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.html': 'html',
            '.htm': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.sass': 'sass',
            '.less': 'less',
            '.json': 'json',
            '.xml': 'xml',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.toml': 'toml',
            '.ini': 'ini',
            '.cfg': 'ini',
            '.conf': 'ini',
            '.md': 'markdown',
            '.markdown': 'markdown',
            '.rst': 'rst',
            '.txt': 'text',
            '.sql': 'sql',
            '.sh': 'bash',
            '.bash': 'bash',
            '.zsh': 'zsh',
            '.fish': 'fish',
            '.ps1': 'powershell',
            '.bat': 'batch',
            '.cmd': 'batch'
        }
        
        # Video-optimized color scheme
        self.color_scheme = {
            Token.Keyword: '#FF6B6B',           # Red for keywords
            Token.Keyword.Constant: '#FF8E53',  # Orange for constants
            Token.Keyword.Declaration: '#FF6B6B',
            Token.Keyword.Namespace: '#4ECDC4',
            Token.Keyword.Pseudo: '#FF6B6B',
            Token.Keyword.Reserved: '#FF6B6B',
            Token.Keyword.Type: '#45B7D1',
            
            Token.Name: '#FFFFFF',              # White for names
            Token.Name.Attribute: '#FFD93D',   # Yellow for attributes
            Token.Name.Builtin: '#6BCF7F',     # Green for builtins
            Token.Name.Builtin.Pseudo: '#6BCF7F',
            Token.Name.Class: '#45B7D1',       # Blue for classes
            Token.Name.Constant: '#FF8E53',    # Orange for constants
            Token.Name.Decorator: '#DDA0DD',   # Purple for decorators
            Token.Name.Entity: '#FFD93D',
            Token.Name.Exception: '#FF6B6B',   # Red for exceptions
            Token.Name.Function: '#FFD93D',    # Yellow for functions
            Token.Name.Property: '#FFD93D',
            Token.Name.Label: '#FFD93D',
            Token.Name.Namespace: '#4ECDC4',   # Cyan for namespaces
            Token.Name.Other: '#FFFFFF',
            Token.Name.Tag: '#FF6B6B',         # Red for tags
            Token.Name.Variable: '#FFFFFF',
            Token.Name.Variable.Class: '#FFFFFF',
            Token.Name.Variable.Global: '#FFFFFF',
            Token.Name.Variable.Instance: '#FFFFFF',
            
            Token.Literal: '#96CEB4',          # Light green for literals
            Token.Literal.Date: '#96CEB4',
            Token.Literal.String: '#96CEB4',   # Light green for strings
            Token.Literal.String.Affix: '#96CEB4',
            Token.Literal.String.Backtick: '#96CEB4',
            Token.Literal.String.Char: '#96CEB4',
            Token.Literal.String.Delimiter: '#96CEB4',
            Token.Literal.String.Doc: '#96CEB4',
            Token.Literal.String.Double: '#96CEB4',
            Token.Literal.String.Escape: '#FFD93D',
            Token.Literal.String.Heredoc: '#96CEB4',
            Token.Literal.String.Interpol: '#FFD93D',
            Token.Literal.String.Other: '#96CEB4',
            Token.Literal.String.Regex: '#FF8E53',
            Token.Literal.String.Single: '#96CEB4',
            Token.Literal.String.Symbol: '#96CEB4',
            Token.Literal.Number: '#DDA0DD',   # Purple for numbers
            Token.Literal.Number.Bin: '#DDA0DD',
            Token.Literal.Number.Float: '#DDA0DD',
            Token.Literal.Number.Hex: '#DDA0DD',
            Token.Literal.Number.Integer: '#DDA0DD',
            Token.Literal.Number.Long: '#DDA0DD',
            Token.Literal.Number.Oct: '#DDA0DD',
            
            Token.Operator: '#FF8E53',         # Orange for operators
            Token.Operator.Word: '#FF6B6B',
            
            Token.Punctuation: '#FFFFFF',     # White for punctuation
            
            Token.Comment: '#7F8C8D',         # Gray for comments
            Token.Comment.Hashbang: '#7F8C8D',
            Token.Comment.Multiline: '#7F8C8D',
            Token.Comment.Preproc: '#4ECDC4',
            Token.Comment.PreprocFile: '#4ECDC4',
            Token.Comment.Single: '#7F8C8D',
            Token.Comment.Special: '#7F8C8D',
            
            Token.Generic: '#FFFFFF',
            Token.Generic.Deleted: '#FF6B6B',
            Token.Generic.Emph: '#FFFFFF',
            Token.Generic.Error: '#FF6B6B',
            Token.Generic.Heading: '#45B7D1',
            Token.Generic.Inserted: '#6BCF7F',
            Token.Generic.Output: '#FFFFFF',
            Token.Generic.Prompt: '#FFD93D',
            Token.Generic.Strong: '#FFFFFF',
            Token.Generic.Subheading: '#45B7D1',
            Token.Generic.Traceback: '#FF6B6B',
            
            Token.Error: '#FF6B6B',           # Red for errors
            Token.Other: '#FFFFFF',          # White for other tokens
            Token.Whitespace: '#FFFFFF',     # White for whitespace
        }
        
        # Default fallback color
        self.default_color = '#00FF00'  # Classic green
        
        logger.info("Text processor initialized", 
                   pygments_available=PYGMENTS_AVAILABLE,
                   supported_extensions=len(self.supported_extensions))
    
    def detect_language(self, text: str, filename: Optional[str] = None) -> LanguageInfo:
        """
        Detect the programming language of the given text.
        
        Args:
            text: Text content to analyze
            filename: Optional filename for extension-based detection
            
        Returns:
            LanguageInfo with detection results
        """
        if not PYGMENTS_AVAILABLE:
            return self._fallback_language_detection(text, filename)
        
        try:
            lexer = None
            detection_method = "unknown"
            confidence = 0.0
            
            # Try filename-based detection first
            if filename:
                try:
                    lexer = get_lexer_for_filename(filename)
                    detection_method = "filename"
                    confidence = 0.9
                except ClassNotFound:
                    pass
            
            # Try extension-based detection
            if not lexer and filename:
                ext = Path(filename).suffix.lower()
                if ext in self.supported_extensions:
                    try:
                        lexer = get_lexer_by_name(self.supported_extensions[ext])
                        detection_method = "extension"
                        confidence = 0.8
                    except ClassNotFound:
                        pass
            
            # Try content-based detection
            if not lexer and text.strip():
                try:
                    lexer = guess_lexer(text)
                    detection_method = "content"
                    confidence = 0.7
                except ClassNotFound:
                    pass
            
            # Fallback to text
            if not lexer:
                lexer = get_lexer_by_name('text')
                detection_method = "fallback"
                confidence = 0.1
            
            return LanguageInfo(
                name=lexer.name,
                aliases=lexer.aliases,
                file_extensions=lexer.filenames,
                confidence=confidence,
                detection_method=detection_method
            )
            
        except Exception as e:
            logger.warning("Language detection failed", error=str(e))
            return self._fallback_language_detection(text, filename)
    
    def _fallback_language_detection(self, text: str, filename: Optional[str] = None) -> LanguageInfo:
        """Fallback language detection when Pygments is not available."""
        if filename:
            ext = Path(filename).suffix.lower()
            if ext in self.supported_extensions:
                lang_name = self.supported_extensions[ext]
                return LanguageInfo(
                    name=lang_name.title(),
                    aliases=[lang_name],
                    file_extensions=[ext],
                    confidence=0.6,
                    detection_method="extension_fallback"
                )
        
        # Simple heuristic detection
        if re.search(r'\bdef\s+\w+\s*\(', text) and re.search(r':\s*$', text, re.MULTILINE):
            return LanguageInfo(
                name="Python",
                aliases=["python"],
                file_extensions=[".py"],
                confidence=0.5,
                detection_method="heuristic"
            )
        elif re.search(r'\bfunction\s+\w+\s*\(', text) or re.search(r'=>', text):
            return LanguageInfo(
                name="JavaScript",
                aliases=["javascript"],
                file_extensions=[".js"],
                confidence=0.5,
                detection_method="heuristic"
            )
        elif re.search(r'\bclass\s+\w+\s*{', text) and re.search(r'\bpublic\s+', text):
            return LanguageInfo(
                name="Java",
                aliases=["java"],
                file_extensions=[".java"],
                confidence=0.5,
                detection_method="heuristic"
            )
        
        return LanguageInfo(
            name="Text",
            aliases=["text"],
            file_extensions=[".txt"],
            confidence=0.1,
            detection_method="fallback"
        )

    def process_text(self, text: str, filename: Optional[str] = None,
                    typing_speed: int = 150) -> ProcessedText:
        """
        Process text with language detection and syntax highlighting.

        Args:
            text: Text content to process
            filename: Optional filename for language detection
            typing_speed: Typing speed in WPM for time estimation

        Returns:
            ProcessedText with syntax highlighting information
        """
        # Detect language
        language_info = self.detect_language(text, filename)

        # Tokenize text for syntax highlighting
        tokens = self._tokenize_text(text, language_info)

        # Split into lines
        lines = text.splitlines()

        # Calculate estimated typing time
        char_count = len(text)
        chars_per_minute = typing_speed * 5  # Average 5 chars per word
        estimated_time = (char_count / chars_per_minute) * 60 if chars_per_minute > 0 else 0

        return ProcessedText(
            original_text=text,
            language_info=language_info,
            tokens=tokens,
            lines=lines,
            total_characters=char_count,
            estimated_typing_time=estimated_time
        )

    def _tokenize_text(self, text: str, language_info: LanguageInfo) -> List[SyntaxToken]:
        """Tokenize text for syntax highlighting."""
        if not PYGMENTS_AVAILABLE or language_info.name.lower() == 'text':
            return self._create_plain_tokens(text)

        try:
            # Get lexer for the detected language
            lexer = None
            for alias in language_info.aliases:
                try:
                    lexer = get_lexer_by_name(alias)
                    break
                except ClassNotFound:
                    continue

            if not lexer:
                return self._create_plain_tokens(text)

            # Tokenize the text
            tokens = []
            current_pos = 0

            for token_type, token_text in lexer.get_tokens(text):
                if token_text:  # Skip empty tokens
                    color = self._get_token_color(token_type)

                    tokens.append(SyntaxToken(
                        text=token_text,
                        token_type=str(token_type),
                        color=color,
                        start_pos=current_pos,
                        end_pos=current_pos + len(token_text)
                    ))

                    current_pos += len(token_text)

            return tokens

        except Exception as e:
            logger.warning("Tokenization failed, using plain text", error=str(e))
            return self._create_plain_tokens(text)

    def _create_plain_tokens(self, text: str) -> List[SyntaxToken]:
        """Create plain text tokens without syntax highlighting."""
        return [SyntaxToken(
            text=text,
            token_type="Text",
            color=self.default_color,
            start_pos=0,
            end_pos=len(text)
        )]

    def _get_token_color(self, token_type) -> str:
        """Get color for a specific token type."""
        # Try exact match first
        if token_type in self.color_scheme:
            return self.color_scheme[token_type]

        # Try parent token types
        current_type = token_type
        while current_type.parent:
            current_type = current_type.parent
            if current_type in self.color_scheme:
                return self.color_scheme[current_type]

        # Return default color
        return self.default_color

    def get_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions."""
        return list(self.supported_extensions.keys())

    def is_supported_file(self, filename: str) -> bool:
        """Check if a file is supported for syntax highlighting."""
        ext = Path(filename).suffix.lower()
        return ext in self.supported_extensions

    def get_language_by_extension(self, extension: str) -> Optional[str]:
        """Get language name by file extension."""
        return self.supported_extensions.get(extension.lower())

    def process_markdown(self, text: str) -> ProcessedText:
        """
        Process markdown text with special handling for code blocks.

        Args:
            text: Markdown text content

        Returns:
            ProcessedText with markdown-aware syntax highlighting
        """
        # For now, treat as plain markdown
        # Future enhancement: Parse code blocks and apply language-specific highlighting
        language_info = LanguageInfo(
            name="Markdown",
            aliases=["markdown", "md"],
            file_extensions=[".md", ".markdown"],
            confidence=1.0,
            detection_method="explicit"
        )

        # Apply markdown-specific tokenization
        tokens = self._tokenize_markdown(text)

        lines = text.splitlines()
        char_count = len(text)
        estimated_time = (char_count / 750) * 60  # Slower for markdown (150 WPM)

        return ProcessedText(
            original_text=text,
            language_info=language_info,
            tokens=tokens,
            lines=lines,
            total_characters=char_count,
            estimated_typing_time=estimated_time
        )

    def _tokenize_markdown(self, text: str) -> List[SyntaxToken]:
        """Tokenize markdown text with basic syntax highlighting."""
        if PYGMENTS_AVAILABLE:
            try:
                lexer = get_lexer_by_name('markdown')
                tokens = []
                current_pos = 0

                for token_type, token_text in lexer.get_tokens(text):
                    if token_text:
                        color = self._get_markdown_color(token_type)

                        tokens.append(SyntaxToken(
                            text=token_text,
                            token_type=str(token_type),
                            color=color,
                            start_pos=current_pos,
                            end_pos=current_pos + len(token_text)
                        ))

                        current_pos += len(token_text)

                return tokens

            except Exception as e:
                logger.warning("Markdown tokenization failed", error=str(e))

        # Fallback to simple markdown highlighting
        return self._simple_markdown_tokens(text)

    def _get_markdown_color(self, token_type) -> str:
        """Get color for markdown token types."""
        markdown_colors = {
            Token.Generic.Heading: '#45B7D1',      # Blue for headers
            Token.Generic.Strong: '#FFD93D',       # Yellow for bold
            Token.Generic.Emph: '#96CEB4',         # Light green for italic
            Token.Literal.String: '#96CEB4',       # Light green for code
            Token.Name.Tag: '#FF6B6B',             # Red for HTML tags
            Token.Comment: '#7F8C8D',              # Gray for comments
        }

        return markdown_colors.get(token_type, self._get_token_color(token_type))

    def _simple_markdown_tokens(self, text: str) -> List[SyntaxToken]:
        """Simple markdown tokenization fallback."""
        # Basic markdown patterns
        patterns = [
            (r'^#{1,6}\s.*$', '#45B7D1'),          # Headers
            (r'\*\*.*?\*\*', '#FFD93D'),           # Bold
            (r'\*.*?\*', '#96CEB4'),               # Italic
            (r'`.*?`', '#96CEB4'),                 # Inline code
            (r'```[\s\S]*?```', '#96CEB4'),        # Code blocks
            (r'\[.*?\]\(.*?\)', '#4ECDC4'),        # Links
        ]

        tokens = []
        current_pos = 0
        processed_ranges = set()

        for pattern, color in patterns:
            for match in re.finditer(pattern, text, re.MULTILINE):
                start, end = match.span()
                if not any(start < r_end and end > r_start for r_start, r_end in processed_ranges):
                    tokens.append(SyntaxToken(
                        text=match.group(),
                        token_type="Markdown",
                        color=color,
                        start_pos=start,
                        end_pos=end
                    ))
                    processed_ranges.add((start, end))

        # Fill in remaining text with default color
        tokens.sort(key=lambda t: t.start_pos)

        # Add unmatched text as default tokens
        last_end = 0
        final_tokens = []

        for token in tokens:
            if token.start_pos > last_end:
                # Add default text before this token
                default_text = text[last_end:token.start_pos]
                if default_text:
                    final_tokens.append(SyntaxToken(
                        text=default_text,
                        token_type="Text",
                        color=self.default_color,
                        start_pos=last_end,
                        end_pos=token.start_pos
                    ))

            final_tokens.append(token)
            last_end = token.end_pos

        # Add any remaining text
        if last_end < len(text):
            remaining_text = text[last_end:]
            if remaining_text:
                final_tokens.append(SyntaxToken(
                    text=remaining_text,
                    token_type="Text",
                    color=self.default_color,
                    start_pos=last_end,
                    end_pos=len(text)
                ))

        return final_tokens


# Global text processor instance
text_processor = TextProcessor()
