import os, re, hashlib, magic, requests, json, numbers, PIL
from lib.plugins.dataTypes.BaseDataType import BaseDataType
from lib.utils.Settings import Settings
from PIL import Image

class MediaDataType(BaseDataType):
    name = "Media"
    description = "Media value"

    settings_spec = {
        "order": ["search_display", "max_size"],
        "settings": {
            "max_size": {
                 "type": "integer",
                 "label": "Maximum size in bytes",
                 "description": "Maximum file size, in bytes",
                 "min": 0,
                 "default": 0,
                 "render": "field",
                 "width": "200px"
            },
             "search_display": {
                "type": "boolean",
                "label": "Search display",
                "description": "Toggle to set if this field should be displayed in search results.",
                "render": "select",
             }
        }
    }

    priority = 1211

    settings = Settings(settings_spec)

    def __init__(self, value=None):
        super(MediaDataType, self).__init__(value)
        self.config = json.load(open('./config.json'));

    #
    # Validate a value for the data type subject to settings. Return True on success, list of errors on failure.
    #
    def validate(self, value):
        errors = []

        self.parsed_value = None
        finfo = MediaDataType.is_downloadable(value)
        if finfo is False:
            errors.append("URL is not downloadable")

        content_length = finfo.get('content-length', None)
        max_size = int(self.settings.getValue("max_size"))
        if max_size is None or max_size < 1000:
            max_size = 10000000  # default to 10megs for now if no setting is present

        if content_length and int(content_length) > max_size:
            errors.append("File is too large: must be less than " + str(max_size) + " bytes")

        if (len(errors) > 0):
            return errors

        return True

    #
    #
    #
    def parse(self, value):
        media_path = "media/"
        if self.config and "media_path" in self.config:
            media_path = self.config['media_path']

        if self.validate(value) is False:
            return False

        f = requests.get(value, allow_redirects=True)
        basename = hashlib.md5(value).hexdigest()
        fname = basename + ".bin"
        open(media_path + fname, 'wb').write(f.content)
        filesize = os.path.getsize(media_path + fname)
        mime = magic.Magic(mime=True)
        mimetype = mime.from_file(media_path + fname)

        original_filename = os.path.basename(value)

        finfo = {
            "filename": fname,
            "length": filesize,
            "mimetype": mimetype,
            "original_filename": original_filename,
            "preview_path": "",
            "preview_url": "",
            "preview_width": "",
            "preview_height": ""
        }

        im = Image.open(media_path + fname)
        if im:
            # TODO: should make thumbnail naming unique to repository
            size = 300, 300
            im.thumbnail(size)
            im.save(media_path + "thumbnails/" +basename + ".thumbnail.jpg", "JPEG")

            finfo['preview_path'] = media_path + "thumbnails/" + basename + ".thumbnail.jpg"
            finfo['preview_url'] = media_path + "thumbnails/" + basename + ".thumbnail.jpg"
            finfo['preview_width'] = 300
            finfo['preview_height'] = 300
        return finfo
        
    #
    # Media-specific settings validation
    #
    def validateSettings(self, settingsValues):
        errs = super(MediaDataType, self).validateSettings(settingsValues)
        if errs is not True:
            return errs

        errs = []

        #if (int(settingsValues.get('min_length', self.settings.getValue("min_length"))) > int(settingsValues.get('max_length', self.settings.getValue("max_length")))):
        #    errs.append("Minimum length must be less than maximum length")

        if len(errs) > 0:
            return errs
        return True

    #
    # Utilities
    #
    @classmethod
    def getMedia(cls, l):
        return False

    @classmethod
    def is_downloadable(cls, url):
        # Does this look like downloadable media?
        h = requests.head(url, allow_redirects=True)
        headers = h.headers
        content_type = headers.get('content-type')
        if 'text' in content_type.lower():
            return False
        if 'html' in content_type.lower():
            return False
        return headers

