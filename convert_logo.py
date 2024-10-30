from PIL import Image

# Load and display logo in the top left

logo = Image.open("icons/no_bg.png")

logo.save("favicon.ico", format="ICO")