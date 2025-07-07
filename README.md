# Food Diary Wrapped

A Python script that parses a PDF food diary and generates Spotify Wrapped-style graphics showing the most consumed foods and drinks.

## Features

- Parses PDF food diaries and extracts food items
- Consolidates beer types (light beer, dark beer, guinness beer)
- Handles quantities (e.g., "3 tacos" � adds 3 to tacos count)
- Generates top 50 foods list
- Creates 15 beautiful square graphics in Spotify Wrapped style
- Perfect for social media sharing (1080x1080)

## Requirements

- Python 3.13+
- uv (for dependency management)
- A PDF file named "Food Diary II.pdf" in the project directory

## Installation

1. Clone or download this repository
2. Navigate to the project directory
3. Install dependencies:
   ```bash
   uv sync
   ```

## Setup

**⚠️ Important: Add Your PDF File**

Before running the script, you need to add your food diary PDF:

1. **Place your PDF** in the project root directory
2. **Name it exactly**: `Food Diary II.pdf`
3. The file should be at the same level as `main.py`

```
charlie-script/
├── main.py
├── Food Diary II.pdf  ← Your PDF goes here
└── ...
```

> **Note**: The PDF file is automatically ignored by git (see `.gitignore`) so it won't be committed to version control.

## Usage

Once your PDF is in place:

```bash
uv run python main.py
```

The script will:
- Parse your PDF starting from page 7 (skipping title pages)
- Extract and count all food items
- Generate graphics and summary files

## Output

The script generates several outputs:

### Files Created
- `food_counts.json` - Complete food count data in JSON format
- `top_50_foods.txt` - Top 50 most consumed foods in text format
- `food_wrapped_graphics/` - Directory containing 15 square graphics

### Graphics Generated
- 15 square images (1080x1080) featuring the top 15 foods
- Spotify Wrapped-style design with colorful gradients
- Bold typography with massive fonts
- Format: `food_wrapped_XX_[food_name].png`

### Sample Output
```
=== TOP 15 MOST COMMON FOODS ===
 1. beer                           749 times
 2. coffee                         549 times
 3. red wine                        98 times
 4. white wine                      68 times
 5. iced coffee                     54 times
 ...
```

## Customization

### Modify Food Categories
Edit the `consolidate_beer_entries()` function to add more food consolidation rules.

### Change Graphics Count
Modify the `top_n=15` parameter in `main.py` to generate more or fewer graphics.

### Adjust Fonts and Colors
Update the font paths in `get_font()` and gradient colors in `generate_food_wrapped_graphics()`.

### Skip Pages
Modify `start_page=7` in `main.py` to skip more or fewer pages from the beginning of the PDF.

## Data Processing

The script performs several data cleaning steps:

1. **Filters out non-food items**: Removes dates, page numbers, days of the week
2. **Quantity extraction**: "3 tacos" becomes 3 entries for "tacos"  
3. **Beer consolidation**: Groups all beer types into a single "beer" category
4. **Case normalization**: All items converted to lowercase for consistency

## File Structure

```
charlie-script/
├── main.py                    # Main script
├── Food Diary II.pdf         # Your PDF input (YOU ADD THIS)
├── food_counts.json          # Generated JSON data (ignored by git)
├── top_50_foods.txt          # Generated text summary (ignored by git)
├── food_wrapped_graphics/    # Generated graphics directory (ignored by git)
├── pyproject.toml           # Dependencies
├── .gitignore               # Git ignore rules
└── README.md               # This file
```

## Dependencies

- **PyPDF2**: PDF text extraction
- **Pillow**: Image generation for graphics

## Notes

- **PDF File**: The input PDF is ignored by git for privacy - you must add your own `Food Diary II.pdf`
- The script assumes the PDF starts with actual food data around page 7
- Long food names are automatically split across multiple lines in graphics
- Graphics use a modern, bold typography style with massive fonts
- All beer variants (light beer, dark beer, guinness) are consolidated into "beer"
- All generated output files are also ignored by git to keep the repo clean