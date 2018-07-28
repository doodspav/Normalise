# Normalise
normalise_monospace.py only works on monospace fonts but it is significantly faster

The only bit you might need to change is the ascii characters bit in the generate_chars function.

For the image comparison stuff to work, you need ttf font files that support all the unicode character points you want to support. Put all your font files in the fonts directory.
