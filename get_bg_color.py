from PIL import Image
import os

path = r"c:\Users\sky.lo\Desktop\CDU程式碼\CDU\250303\webUI\frontend\public\img\diagram\CDU底圖_灰.png"

try:
    img = Image.open(path)
    # Sample a few pixels from the top-left corner to be sure, assuming it's uniform background there
    # The user screenshot shows the mismatch at the edge. 
    # Let's sample coordinate (5, 5)
    pixel = img.getpixel((5, 5))
    print(f"Pixel at (5,5): {pixel}")
    
    # Convert to Hex
    # Handle if pixel has alpha channel
    if len(pixel) == 4:
        r, g, b, a = pixel
    else:
        r, g, b = pixel
        
    hex_color = "#{:02x}{:02x}{:02x}".format(r, g, b)
    print(f"Hex Color: {hex_color}")

except Exception as e:
    print(f"Error: {e}")
