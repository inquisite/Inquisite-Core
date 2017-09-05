import magic

#
# Detect format of file based upon content
# Return mimetype if file is recognized, None if file is unrecognized.
#
def getMimetypeForFile(path):
    try:
        f = magic.Magic(mime=True)
        return f.from_file(path)
    except magic.MagicException as e:
        return None
