from lib.exceptions.SettingsValidationError import SettingsValidationError
class Settings:

    settings = {}
    settingsValues = {}

    #
    #
    #
    def __init__(self, settings):
        self.setSettings(settings)

    #
    # Initialize object with settings specification
    # Spec is a dictionary with two keys:
    #       "order" => list of settings codes in preferred order of display
    #       "settings" => a dictionary of settings, keys are setting codes, values are info dictionaries (see https://github.com/inquisite/Inquisite-Core/wiki/Data-type-settings-types)
    #
    def setSettings(self, settingsSpec):
        # validate spec
        errors = self.validateSettingsSpec(settingsSpec)
        if errors is not True:
            raise SettingsValidationError(message="; ".join(errors), errors=errors, context="Settings.setSettings()")

        # Add "code" attribute by copying key
        for k, v in settingsSpec['settings'].iteritems():
            settingsSpec['settings'][k]['code'] = k
        self.settings = settingsSpec

    #
    # Return configured settings as a dictionary
    #
    def getSettings(self):
        return self.settings["settings"]

    #
    # Return list of settings codes in preferred order of display
    #
    def getSettingsOrder(self):
        return self.settings["order"]

    #
    # Return information dictionary for a setting or False is setting is not defined
    #
    def getSetting(self, setting):
        if setting in self.settings["settings"]:
            return self.settings["settings"][setting]
        return False

    #
    # Validate a dictionary of settings values against settings specification
    # Return dictionary of errors; keys are settings codes, values are lists of errors
    # Keys are set only for settings with errors. If there are no errors returns True
    #
    def validate(self, settingsValues):
        errors_by_setting = {}
        for k, v in settingsValues.items():
            errs = []
            s = self.getSetting(k)
            if s is False:
                continue

            if (s['type'] == "integer"):
                try:
                    v = int(v)
                    if ("min" in s) and (v < s["min"]):
                        errs.append("Value must be greater than " + str(s["min"]))
                    if ("max" in s) and (v > s["max"]):
                        errs.append("Value must be less than " + str(s["max"]))
                except Exception as e:
                    errs.append("Value is not an integer")
            elif (s['type'] == "float"):
                try:
                    v = float(v)
                    if ("min" in s) and (v < s["min"]):
                        errs.append("Value must be greater than " + str(s["min"]))
                    if ("max" in s) and (v > s["max"]):
                        errs.append("Value must be less than " + str(s["max"]))
                except Exception as e:
                    errs.append("Value is not a float")
            elif (s['type'] == "text"):
                if ("min" in s) and (len(v) < s["min"]):
                    errs.append("Value must be less than " + str(s["min"]) + " characters")
                if ("max" in s) and (len(v) > s["max"]):
                    errs.append("Value must be more than " + str(s["max"]) + " characters")
            elif (s['type'] == "boolean"):
                if (int(v) != 1) and (int(v) != 0) and (int(v) is not True) and (int(v) is not False):
                    errs.append("Value be a true/false value")
            else:
                # TODO: handle list type
                pass


            if len(errs) > 0:
                errors_by_setting[k] = errs

        if len(errors_by_setting) > 0:
            return errors_by_setting
        return True

    #
    #
    #
    def validateSettingsSpec(self, settingsSpec):
        errors = []
        if "order" not in settingsSpec:
            errors.append("No settings order list defined")
        if "settings" not in settingsSpec:
            errors.append("No settings dictionary defined")

        if len(errors) > 0:
            return errors
        return True

    #
    #
    #
    def setValues(self, values):
        self.settingsValues = values

    #
    #
    #
    def getValues(self):
        return self.settingsValues

    #
    # Set vale f
    #
    def getValue(self, setting):
        s = self.getSetting(setting)
        if s is None:
            return None

        if setting in self.settingsValues:
            v = self.settingsValues[setting]
            if s["type"] == "integer":
                v = int(v)
            elif s["type"] == "text":
                v = str(v)
            elif s["type"] == "float":
                v = float(v)
            elif s["type"] == "boolean":
                v = bool(v)
            elif s["type"] == "list":
                pass # TODO
            return v

        if "default" not in s:
            return None

        return s["default"]