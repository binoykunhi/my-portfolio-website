import os
with open("test.mp3", "wb") as f:
    # Write some dummy bytes, enough to look like a file but invalid audio
    # This will likely cause an API error, but it proves execution
    f.write(b'\xFF\xFB' * 1000)
