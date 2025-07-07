import re
from pathlib import Path
import json
import os

import PyPDF2
from PIL import Image, ImageDraw, ImageFont


def parse_quantity_and_food(item):
    """Extract quantity and food item from a string like '3 tacos' or '2 slices of pizza'."""
    # Common quantity patterns at the beginning
    quantity_patterns = [
        r'^(\d+)\s+(.+)$',  # "3 tacos"
        r'^(\d+)\s+(?:slices?\s+of\s+)?(.+)$',  # "2 slices of pizza"
        r'^(\d+)\s+(?:pieces?\s+of\s+)?(.+)$',  # "4 pieces of chicken"
        r'^(\d+)\s+(?:cups?\s+of\s+)?(.+)$',  # "2 cups of coffee"
        r'^(\d+)\s+(?:bottles?\s+of\s+)?(.+)$',  # "3 bottles of beer"
        r'^(\d+)\s+(?:cans?\s+of\s+)?(.+)$',  # "2 cans of soda"
        r'^(\d+)\s+(?:glasses?\s+of\s+)?(.+)$',  # "2 glasses of wine"
    ]
    
    for pattern in quantity_patterns:
        match = re.match(pattern, item, re.IGNORECASE)
        if match:
            quantity = int(match.group(1))
            food_item = match.group(2).strip()
            return quantity, food_item
    
    # No quantity found, return 1 and the original item
    return 1, item


def consolidate_beer_entries(food_counts):
    """Consolidate all beer-related entries into a single 'beer' category."""
    beer_keywords = [
        'beer', 'guinness', 'light beer', 'dark beer', 'lager', 'ale', 'ipa', 
        'pilsner', 'stout', 'porter', 'wheat beer', 'hefeweizen', 'weissbier',
        'amber beer', 'pale ale', 'belgian beer', 'craft beer', 'draft beer',
        'bottled beer', 'canned beer', 'pint of beer', 'bottle of beer',
        'can of beer', 'glass of beer', 'hard seltzer', 'seltzer beer',
        'budweiser', 'coors', 'miller', 'heineken', 'corona', 'stella artois',
        'modelo', 'dos equis', 'tecate', 'pacifico', 'negra modelo',
        'blue moon', 'shock top', 'sam adams', 'yuengling', 'bud light',
        'coors light', 'miller lite', 'natural light', 'pbr', 'pabst',
        'rolling rock', 'keystone', 'busch', 'michelob', 'carlsberg',
        'peroni', 'moretti', 'becks', 'amstel', 'fosters', 'asahi',
        'sapporo', 'kirin', 'tsingtao', 'chang', 'singha', 'tiger',
        'red stripe', 'kingfisher', 'efes', 'brahma', 'skol'
    ]
    
    # Items that contain "beer" but are NOT actually beer
    non_beer_exclusions = [
        'ginger beer', 'root beer', 'na beer', 'ginger ale', 'root beer float',
        'na guinness', 'non-alcoholic beer', 'birch beer'
    ]
    
    total_beer_count = 0
    beer_entries_found = []
    
    # Find all beer-related entries
    for food_item, count in list(food_counts.items()):
        is_beer = False
        
        # First check if it's in the exclusion list
        is_excluded = False
        for exclusion in non_beer_exclusions:
            if exclusion in food_item.lower():
                is_excluded = True
                break
        
        if is_excluded:
            continue
            
        # Check if this item contains any beer keywords
        for keyword in beer_keywords:
            if keyword in food_item.lower():
                is_beer = True
                break
        
        if is_beer:
            total_beer_count += count
            beer_entries_found.append((food_item, count))
            del food_counts[food_item]
    
    # Add consolidated beer count
    if total_beer_count > 0:
        food_counts['beer'] = total_beer_count
    
    print(f"\nBeer consolidation:")
    print(f"Found {len(beer_entries_found)} beer-related entries")
    print(f"Total beer count: {total_beer_count}")
    print("Beer entries consolidated:")
    for item, count in beer_entries_found:
        print(f"  {item}: {count}")
    
    return food_counts


def parse_entire_pdf(pdf_path, start_page=7):
    """Parse the entire PDF starting from a specific page and count food items."""
    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    food_counts = {}
    
    with open(pdf_path, "rb") as file:
        pdf_reader = PyPDF2.PdfReader(file)
        total_pages = len(pdf_reader.pages)
        
        print(f"Total pages in PDF: {total_pages}")
        print(f"Starting from page {start_page}")
        print(f"Processing {total_pages - start_page + 1} pages...")

        for page_num in range(start_page - 1, total_pages):
            page = pdf_reader.pages[page_num]
            text = page.extract_text()
            
            # Process this page's food items
            food_items = extract_food_items(text, page_num + 1)
            
            # Count the food items with quantities
            for item in food_items:
                quantity, food_item = parse_quantity_and_food(item)
                food_item_lower = food_item.lower()
                food_counts[food_item_lower] = food_counts.get(food_item_lower, 0) + quantity
            
            # Progress indicator
            if (page_num + 1) % 50 == 0:
                print(f"Processed {page_num + 1} pages... Found {len(food_counts)} unique items so far")

    # Consolidate beer entries
    food_counts = consolidate_beer_entries(food_counts)
    
    return food_counts


def extract_food_items(text, page_num):
    """Extract food items from a page's text, filtering out dates and page numbers."""
    if not text.strip():
        return []
    
    lines = text.split('\n')
    food_items = []
    
    # Days of the week
    days_of_week = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    
    # Common patterns to skip
    skip_patterns = [
        r'^\d+$',  # Just a number (page number)
        r'^\d+\s*$',  # Just a number with whitespace
        r'^[A-Za-z]+day\s*$',  # Just weekday name
        r'^[A-Za-z]+day\s+[A-Za-z]+\s+\d{1,2},\s+\d{4}$',  # Date line like "Tuesday May 14, 2024"
        r'^\d{4}\s*-\s*\d{4}$',  # Year range
        r'^[A-Z]{3}\s+\d+.*$',  # Month abbreviation with numbers (calendar)
        r'^Title Page Content.*$',  # Title page content
        r'^Charlie Sosnick$',  # Author name
        r'^FOOD DIARY$',  # Title
        r'^Year Two$',  # Subtitle
        r'^Or, Everything.*$',  # Subtitle continuation
        r'^Recorded Accurately.*$',  # Subtitle continuation
        r'^\d{1,2}/\d{1,2}/\d{2,4}$',  # Date formats like 5/14/2024
        r'^\d{1,2}-\d{1,2}-\d{2,4}$',  # Date formats like 5-14-2024
        r'^[A-Za-z]+\s+\d{1,2},\s+\d{4}$',  # Date formats like "May 14, 2024"
        r'^\d{1,2}\s+[A-Za-z]+\s+\d{4}$',  # Date formats like "14 May 2024"
    ]
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Skip if line matches any skip pattern
        should_skip = False
        for pattern in skip_patterns:
            if re.match(pattern, line):
                should_skip = True
                break
        
        if should_skip:
            continue
            
        # Skip very short lines that are likely page numbers or artifacts
        if len(line) <= 2:
            continue
            
        # Skip if line is just a number (including multi-digit numbers)
        if re.match(r'^\d+$', line):
            continue
            
        # Skip if line contains any day of the week
        line_lower = line.lower()
        if any(day in line_lower for day in days_of_week):
            continue
            
        # Skip if line looks like a date pattern (more flexible matching)
        if re.search(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', line):
            continue
            
        # Skip if line is mostly numbers and punctuation
        if re.match(r'^[\d\s\-/,]+$', line):
            continue
            
        # This looks like a food item
        food_items.append(line)
    
    return food_items


def save_food_counts(food_counts, filename="food_counts.json"):
    """Save food counts to a JSON file."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(food_counts, f, indent=2, ensure_ascii=False)
    
    print(f"Food counts saved to {filename}")


def print_top_foods(food_counts, top_n=20):
    """Print the top N most common foods."""
    sorted_foods = sorted(food_counts.items(), key=lambda x: x[1], reverse=True)
    
    print(f"\n=== TOP {top_n} MOST COMMON FOODS ===")
    for i, (food, count) in enumerate(sorted_foods[:top_n], 1):
        print(f"{i:2d}. {food:<30} {count:>3} times")
    
    print(f"\nTotal unique food items: {len(food_counts)}")
    print(f"Total food entries: {sum(food_counts.values())}")


def save_top_foods(food_counts, top_n=50, filename="top_50_foods.txt"):
    """Save the top N most common foods to a text file."""
    sorted_foods = sorted(food_counts.items(), key=lambda x: x[1], reverse=True)
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"TOP {top_n} MOST EATEN FOODS\n")
        f.write("=" * 40 + "\n\n")
        
        for i, (food, count) in enumerate(sorted_foods[:top_n], 1):
            f.write(f"{i:2d}. {food:<40} {count:>4} times\n")
        
        f.write(f"\n" + "=" * 40 + "\n")
        f.write(f"Total unique food items: {len(food_counts)}\n")
        f.write(f"Total food entries: {sum(food_counts.values())}\n")
    
    print(f"Top {top_n} foods saved to {filename}")


def create_gradient_background(width, height, color1, color2):
    """Create a gradient background from color1 to color2."""
    gradient = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(gradient)
    
    for y in range(height):
        # Linear interpolation between colors
        ratio = y / height
        r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
        g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
        b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    return gradient


def get_font(size, style="regular"):
    """Get a modern, wide font for contemporary design."""
    try:
        # Try to find the widest, boldest, most modern fonts available
        if style == "ultra_bold":
            font_paths = [
                "/System/Library/Fonts/Helvetica-Bold.ttc",
                "/System/Library/Fonts/Arial-BoldMT.ttf", 
                "/System/Library/Fonts/Impact.ttf",
                "/System/Library/Fonts/Arial Black.ttf",
                "/System/Library/Fonts/Trebuchet MS Bold.ttf",
                "/System/Library/Fonts/Helvetica.ttc"
            ]
        elif style == "bold":
            font_paths = [
                "/System/Library/Fonts/Helvetica-Bold.ttc",
                "/System/Library/Fonts/Arial-BoldMT.ttf",
                "/System/Library/Fonts/Helvetica.ttc",
                "/System/Library/Fonts/Arial.ttf"
            ]
        else:
            font_paths = [
                "/System/Library/Fonts/Helvetica.ttc",
                "/System/Library/Fonts/Arial.ttf"
            ]
            
        for font_path in font_paths:
            try:
                return ImageFont.truetype(font_path, size)
            except:
                continue
                
    except:
        pass
    
    return ImageFont.load_default()




def generate_food_wrapped_graphics(food_counts, top_n=15, output_dir="food_wrapped_graphics"):
    """Generate Spotify Wrapped-style graphics for top foods."""
    sorted_foods = sorted(food_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Spotify-inspired gradient colors
    gradients = [
        ((255, 99, 132), (255, 159, 64)),   # Pink to Orange
        ((54, 162, 235), (153, 102, 255)),  # Blue to Purple
        ((255, 206, 86), (75, 192, 192)),   # Yellow to Teal
        ((153, 102, 255), (255, 99, 132)),  # Purple to Pink
        ((255, 159, 64), (255, 99, 132)),   # Orange to Pink
    ]
    
    # Image dimensions - square format
    width, height = 1080, 1080  # Square format
    
    total_entries = sum(food_counts.values())
    
    for i, (food, count) in enumerate(sorted_foods[:top_n], 1):
        # Choose gradient
        gradient_idx = (i - 1) % len(gradients)
        color1, color2 = gradients[gradient_idx]
        
        # Create image with gradient background
        img = create_gradient_background(width, height, color1, color2)
        draw = ImageDraw.Draw(img)
        
        # Calculate daily average
        daily_avg = count / 365
        
        # Fonts - MASSIVE sizes to fill square space
        rank_font = get_font(450, style="ultra_bold")  # Huge rank number
        food_font = get_font(120, style="ultra_bold")  # Massive food name
        count_font = get_font(80, style="bold")        # Large count
        daily_font = get_font(50, style="bold")        # Smaller daily stats
        header_font = get_font(40, style="ultra_bold") # Compact header
        
        # Draw small header at top
        header_text = "FOOD DIARY WRAPPED 24-25"
        header_bbox = draw.textbbox((0, 0), header_text, font=header_font)
        header_width = header_bbox[2] - header_bbox[0]
        draw.text(((width - header_width) // 2, 40), header_text, 
                 fill=(255, 255, 255), font=header_font)
        
        # Draw massive rank number
        rank_text = f"#{i}"
        rank_bbox = draw.textbbox((0, 0), rank_text, font=rank_font)
        rank_width = rank_bbox[2] - rank_bbox[0]
        rank_height = rank_bbox[3] - rank_bbox[1]
        draw.text(((width - rank_width) // 2, 120), rank_text, 
                 fill=(255, 255, 255), font=rank_font)
        
        # Calculate position for food name (much further below the rank number)
        food_start_y = 120 + rank_height + 150  # 150px gap below rank number for much more space
        
        # Draw massive food name - positioned below rank number
        food_display = food.title()
        if len(food_display) > 12:  # Split even shorter names for bigger font
            # Split long food names
            words = food_display.split()
            if len(words) > 1:
                mid = len(words) // 2
                line1 = " ".join(words[:mid])
                line2 = " ".join(words[mid:])
                
                line1_bbox = draw.textbbox((0, 0), line1, font=food_font)
                line1_width = line1_bbox[2] - line1_bbox[0]
                line1_height = line1_bbox[3] - line1_bbox[1]
                draw.text(((width - line1_width) // 2, food_start_y), line1, 
                         fill=(255, 255, 255), font=food_font)
                
                line2_bbox = draw.textbbox((0, 0), line2, font=food_font)
                line2_width = line2_bbox[2] - line2_bbox[0]
                draw.text(((width - line2_width) // 2, food_start_y + line1_height + 20), line2, 
                         fill=(255, 255, 255), font=food_font)
                y_offset = food_start_y + line1_height + 20 + (line2_bbox[3] - line2_bbox[1]) + 60
            else:
                # Single long word, center it
                food_bbox = draw.textbbox((0, 0), food_display, font=food_font)
                food_width = food_bbox[2] - food_bbox[0]
                food_height = food_bbox[3] - food_bbox[1]
                draw.text(((width - food_width) // 2, food_start_y), food_display, 
                         fill=(255, 255, 255), font=food_font)
                y_offset = food_start_y + food_height + 60
        else:
            # Short name, center it
            food_bbox = draw.textbbox((0, 0), food_display, font=food_font)
            food_width = food_bbox[2] - food_bbox[0]
            food_height = food_bbox[3] - food_bbox[1]
            draw.text(((width - food_width) // 2, food_start_y), food_display, 
                     fill=(255, 255, 255), font=food_font)
            y_offset = food_start_y + food_height + 60
        
        # Draw large count
        count_text = f"{count} TIMES"
        count_bbox = draw.textbbox((0, 0), count_text, font=count_font)
        count_width = count_bbox[2] - count_bbox[0]
        draw.text(((width - count_width) // 2, y_offset), count_text, 
                 fill=(255, 255, 255), font=count_font)
        
        # Draw compact stats at bottom
        daily_text = f"{daily_avg:.1f}/DAY • {(count / total_entries) * 100:.1f}%"
        daily_bbox = draw.textbbox((0, 0), daily_text, font=daily_font)
        daily_width = daily_bbox[2] - daily_bbox[0]
        draw.text(((width - daily_width) // 2, y_offset + 120), daily_text, 
                 fill=(255, 255, 255), font=daily_font)
        
        # Save image
        filename = f"{output_dir}/food_wrapped_{i:02d}_{food.replace(' ', '_').replace('/', '_')}.png"
        img.save(filename)
        print(f"Generated: {filename}")
    
    print(f"\nGenerated {top_n} Food Wrapped graphics in '{output_dir}' directory!")


def main():
    pdf_path = "Food Diary II.pdf"

    try:
        print("Parsing entire PDF to count food items...")
        food_counts = parse_entire_pdf(pdf_path, start_page=7)  # Skip first 6 pages
        
        print("\nParsing complete!")
        
        # Save results
        save_food_counts(food_counts)
        
        # Save top 50 foods to file
        save_top_foods(food_counts, top_n=50)
        
        # Generate Food Wrapped graphics
        print("\nGenerating Food Wrapped graphics...")
        generate_food_wrapped_graphics(food_counts, top_n=15)
        
        # Show top foods
        print_top_foods(food_counts, top_n=30)
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
