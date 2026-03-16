#!/usr/bin/env python3
"""
MCP Server for Algorithmic Art Generation.

This server provides tools to generate algorithmic art SVG code using MiniMax API,
supporting various styles like tech, fractal, and particle effects.
"""

import os
import json
import hashlib
import asyncio
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any

import httpx
from pydantic import BaseModel, Field, field_validator, ConfigDict
from mcp.server.fastmcp import FastMCP

# Initialize the MCP server
mcp = FastMCP("algorithmic_art_mcp")

# Constants
MINIMAX_API_BASE_URL = "https://api.minimax.chat/v1"
DEFAULT_OUTPUT_DIR = Path("./output")
DEFAULT_WIDTH = 500
DEFAULT_HEIGHT = 500

# Supported art styles
class ArtStyle(str, Enum):
    """Supported algorithmic art styles."""
    TECH = "科技风"      # Tech/cyberpunk style with grid and glow effects
    FRACTAL = "分形"     # Fractal/spiral patterns with golden colors
    PARTICLE = "粒子"    # Soft ethereal particle effects


# ==================== Pydantic Models ====================

class GenerateArtInput(BaseModel):
    """Input model for algorithmic art generation."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    style: ArtStyle = Field(
        default=ArtStyle.TECH,
        description="Art style: '科技风' (tech/cyberpunk), '分形' (fractal/spiral), '粒子' (particle effects)"
    )
    width: int = Field(
        default=DEFAULT_WIDTH,
        description="SVG canvas width in pixels",
        ge=100,
        le=2000
    )
    height: int = Field(
        default=DEFAULT_HEIGHT,
        description="SVG canvas height in pixels",
        ge=100,
        le=2000
    )
    output_dir: Optional[str] = Field(
        default=None,
        description="Output directory path for saving SVG file (default: ./output)"
    )
    filename: Optional[str] = Field(
        default=None,
        description="Output filename without extension (default: auto-generated from style and timestamp)"
    )

    @field_validator('width', 'height')
    @classmethod
    def validate_dimensions(cls, v: int) -> int:
        if v < 100 or v > 2000:
            raise ValueError("Dimensions must be between 100 and 2000 pixels")
        return v


# ==================== Utility Functions ====================

def _generate_prompt(style: ArtStyle, width: int, height: int) -> str:
    """Generate the appropriate prompt for the requested art style."""
    style_prompts = {
        ArtStyle.TECH: f"""Generate a dark tech style SVG ({width}x{height}) with blue gradient grid pattern.

Requirements:
- Canvas: {width}x{height}
- Dark background (deep navy/black #0a0a1a)
- Blue gradient grid lines (#0066ff to #00ffff)
- Tech/futuristic aesthetic with glow effects
- Clean, minimalist design with grid pattern
- Include center geometric element (diamond or tech symbol)
- Add corner accents and intersection dots

Output ONLY the raw SVG code, no explanations or markdown formatting.""",

        ArtStyle.FRACTAL: f"""Generate a golden fractal SVG ({width}x{width}) with spiral structure.

Requirements:
- Canvas: {width}x{height}
- Dark background (#0a0a0a or similar)
- Golden/amber color palette (#b8860b, #d4af37, #ffd700)
- Spiral/fractal pattern emanating from center
- Elegant, luxurious aesthetic
- Include multiple spiral arms with branches
- Add decorative particles along spirals
- Center focal point with glow effect

Output ONLY the raw SVG code, no explanations or markdown formatting.""",

        ArtStyle.PARTICLE: f"""Generate a purple particle effect SVG ({width}x{height}) with soft, ethereal aesthetic.

Requirements:
- Canvas: {width}x{height}
- Dark background (#0a0a12 or similar)
- Purple/violet color palette (#8b5cf6, #a855f7, #c084fc, #e9d5ff)
- Soft, flowing, ethereal particles scattered throughout
- Gentle, dreamy feel with varying particle sizes
- Use radial gradients for soft glow effects
- Add ambient background glow
- Mix of large, medium, small, and tiny sparkle particles

Output ONLY the raw SVG code, no explanations or markdown formatting."""
    }
    return style_prompts.get(style, style_prompts[ArtStyle.TECH])


def _get_style_display_name(style: ArtStyle) -> str:
    """Get human-readable style name."""
    return {
        ArtStyle.TECH: "tech",
        ArtStyle.FRACTAL: "fractal",
        ArtStyle.PARTICLE: "particle"
    }[style]


async def _call_minimax_api(prompt: str, api_key: str) -> str:
    """Call MiniMax API to generate SVG code."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "MiniMax-M2.5",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.7,
        "max_tokens": 4000
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{MINIMAX_API_BASE_URL}/text/chatcompletion_v2",
            headers=headers,
            json=payload
        )
        response.raise_for_status()

        data = response.json()

        # Extract SVG code from response
        if "choices" in data and len(data["choices"]) > 0:
            content = data["choices"][0]["message"]["content"]
            # Extract SVG code from markdown if present
            if "```svg" in content:
                start = content.find("```svg") + 6
                end = content.find("```", start)
                if end > start:
                    return content[start:end].strip()
            elif "<svg" in content:
                start = content.find("<svg")
                end = content.find("</svg>", start) + 6
                return content[start:end]
            return content.strip()

        raise ValueError("Invalid response format from MiniMax API")


def _save_svg_file(svg_code: str, output_dir: Path, filename: str) -> Path:
    """Save SVG code to file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    filepath = output_dir / f"{filename}.svg"
    filepath.write_text(svg_code, encoding='utf-8')
    return filepath


def _generate_filename(style: ArtStyle) -> str:
    """Generate unique filename based on style and timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    style_name = _get_style_display_name(style)
    return f"{style_name}_{timestamp}"


def _handle_api_error(e: Exception) -> str:
    """Handle API errors with actionable messages."""
    if isinstance(e, httpx.HTTPStatusError):
        if e.response.status_code == 401:
            return "Error: Invalid API key. Please check your MiniMax API key."
        elif e.response.status_code == 429:
            return "Error: Rate limit exceeded. Please wait before making more requests."
        elif e.response.status_code == 500:
            return "Error: MiniMax server error. Please try again later."
        return f"Error: API request failed with status {e.response.status_code}"
    elif isinstance(e, httpx.TimeoutException):
        return "Error: Request timed out. Please try again."
    elif isinstance(e, ValueError):
        return f"Error: Invalid response - {str(e)}"
    return f"Error: Unexpected error occurred: {type(e).__name__} - {str(e)}"


# ==================== MCP Tools ====================

@mcp.tool(
    name="generate_algorithmic_art",
    annotations={
        "title": "Generate Algorithmic Art SVG",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def generate_algorithmic_art(params: GenerateArtInput) -> str:
    """Generate algorithmic art SVG code using MiniMax API.

    This tool generates SVG code for various algorithmic art styles including
    tech/cyberpunk grid patterns, golden fractal spirals, and ethereal particle effects.
    The generated SVG is saved to a local file and returned as code.

    Args:
        params (GenerateArtInput): Validated input parameters containing:
            - style (ArtStyle): Art style - '科技风' (tech), '分形' (fractal), '粒子' (particle)
            - width (int): SVG canvas width (100-2000, default 500)
            - height (int): SVG canvas height (100-2000, default 500)
            - output_dir (Optional[str]): Output directory path
            - filename (Optional[str]): Custom filename without extension

    Returns:
        str: JSON-formatted response containing:
            - success (bool): Whether generation succeeded
            - svg_code (str): Generated SVG code
            - filepath (str): Path to saved file
            - style (str): Art style used
            - dimensions (dict): Width and height

    Examples:
        - Use when: "Generate a tech-style grid SVG" -> style="科技风", width=500, height=500
        - Use when: "Create a golden fractal pattern" -> style="分形", width=800, height=800
        - Use when: "Make a purple particle effect" -> style="粒子", width=600, height=400

    Error Handling:
        - Returns error if API key is missing (MINIMAX_API_KEY environment variable)
        - Returns error if API request fails (network issues, rate limits)
        - Returns error if SVG code parsing fails
        - File write errors are caught and reported
    """
    try:
        # Get API key from environment
        api_key = os.environ.get("MINIMAX_API_KEY")
        if not api_key:
            return json.dumps({
                "success": False,
                "error": "MINIMAX_API_KEY environment variable not set. Please set your MiniMax API key."
            }, ensure_ascii=False, indent=2)

        # Generate prompt based on style
        prompt = _generate_prompt(params.style, params.width, params.height)

        # Call MiniMax API
        svg_code = await _call_minimax_api(prompt, api_key)

        # Validate SVG code
        if not svg_code or "<svg" not in svg_code:
            return json.dumps({
                "success": False,
                "error": "Invalid SVG code generated. Please try again."
            }, ensure_ascii=False, indent=2)

        # Determine output path
        output_dir = Path(params.output_dir) if params.output_dir else DEFAULT_OUTPUT_DIR
        filename = params.filename if params.filename else _generate_filename(params.style)

        # Save SVG file
        try:
            filepath = _save_svg_file(svg_code, output_dir, filename)
        except Exception as file_error:
            return json.dumps({
                "success": False,
                "error": f"Failed to save file: {str(file_error)}",
                "svg_code": svg_code[:500] + "..." if len(svg_code) > 500 else svg_code
            }, ensure_ascii=False, indent=2)

        # Return success response
        return json.dumps({
            "success": True,
            "svg_code": svg_code,
            "filepath": str(filepath),
            "style": params.style.value,
            "dimensions": {
                "width": params.width,
                "height": params.height
            }
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({
            "success": False,
            "error": _handle_api_error(e)
        }, ensure_ascii=False, indent=2)


# ==================== Server Entry Point ====================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Algorithmic Art MCP Server")
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for streamable HTTP transport (default: 8000)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./output",
        help="Default output directory for SVG files"
    )

    args = parser.parse_args()

    # Update default output directory
    DEFAULT_OUTPUT_DIR = Path(args.output_dir)

    # Run server
    print(f"Starting Algorithmic Art MCP Server...")
    print(f"Default output directory: {DEFAULT_OUTPUT_DIR.absolute()}")
    print(f"Transport: streamable-http")
    print(f"URL: http://localhost:{args.port}/mcp")

    mcp.run(transport="streamable-http")