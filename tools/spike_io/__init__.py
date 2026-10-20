"""WP2.1S transport and photo I/O spike: evidence for WP2.1's transport and photo libraries.

``transport`` times decoding GX011627 to NumPy through each candidate frame transport, with
byte identity and exact pts against the prototype's raw pipe; ``photo`` checks the HEIC read
and the 16-bit PNG write (ICC profile and EXIF) on synthetic images. Evidence only: nothing
here is product code, and ``tools/prototype`` is consumed by import, never modified.
"""
