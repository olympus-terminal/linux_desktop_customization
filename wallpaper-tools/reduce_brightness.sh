#\!/bin/bash

# Reduce brightness of wallpapers by 5%
INPUT_DIR="/home/drn2/Documents/desktops/MJ7-Topaz/light-processed"
OUTPUT_DIR="/home/drn2/Documents/desktops/MJ7-Topaz/brightness-reduced"

echo "Reducing brightness by 5% for all images..."
echo "Input: $INPUT_DIR"
echo "Output: $OUTPUT_DIR"
echo ""

count=0
total=$(find "$INPUT_DIR" -type f \( -iname "*.png" -o -iname "*.jpg" \) | wc -l)

for file in "$INPUT_DIR"/*.{png,jpg,jpeg}; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        output_file="$OUTPUT_DIR/$filename"
        
        echo "Processing ($((++count))/$total): $filename"
        
        # Reduce brightness by 5% (95% of original brightness)
        convert "$file" -brightness-contrast -5x0 "$output_file"
        
        if [ $? -eq 0 ]; then
            echo "✓ Completed: $filename"
        else
            echo "✗ Failed: $filename"
        fi
    fi
done

echo ""
echo "Brightness reduction complete\!"
echo "Files saved to: $OUTPUT_DIR"

