import logging
import sys, os
import json

def load_config(filepath):
    """ load json configuration file"""
    with open(filepath) as f:
        inputs = json.load(f)
    
    return inputs

def merge_configs(defaults, user, level=0):
    for k, v in user.items():
        if k not in defaults:
            if level == 0:
                print(f"WARNING: configuration parameter {k} is unknown. Check spelling and capitalization perhaps?")
            defaults[k] = v
        else:
            if isinstance(v, dict):
                merge_configs(defaults[k], v, level=level+1)
            else:
                defaults[k] = v

def merge_config_constant(defaults, user):
    pass


class Logger(logging.Logger):
    def __init__(self, name, level=logging.INFO, format=None):
        self.name = name
        self.level = level
        self.logger = logging.getLogger(name)
        ## remove any handlers
        if self.logger.hasHandlers():
            while len(self.logger.handlers) > 0:
                h = self.logger.handlers.pop(0)
                self.logger.removeHandler(h)
            self.logger.handlers = []
            # for h in self.logger.handlers:
            #     self.logger.removeHandler(h)
        if type(level) == str:
            self.logger.setLevel(level.upper())
        else:
            self.logger.setLevel(level)
        
        if format is None:
            self.formatter = logging.Formatter("{name}: {levelname}: {message}", style="{")
        else:
            self.formatter = logging.Formatter(f"{format}", style="{")
        self.formatter_plain = logging.Formatter("{message}", style="{")
        
        ### add stream handler
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(self.formatter)
        self.logger.addHandler(stream_handler)

        self.formattoggle = False
        self.currentformat = 'normal'
    
    def setlevel(self, level):
        """change the logging level"""
        if type(level) == str:
            level = level.upper()
        self.logger.setLevel(level)
        for h in self.logger.handlers:
            h.setLevel(level)

    def getlevel(self):
        """return the logging level as a string"""
        if self.level == logging.DEBUG:
            return "DEBUG"
        elif self.level == logging.INFO:
            return "INFO"
        elif self.level == logging.WARNING:
            return "WARNING"
        elif self.level == logging.ERROR:
            return "ERROR"
        elif self.level == logging.CRITICAL:
            return "CRITICAL"
        
    def set_logfile(self, file=None, path=None, mode="w"):
        if file is None:
            file = self.name + ".log"
        if path is not None:
            file = os.path.join(path, file)
        file_handler = logging.FileHandler(file, mode=mode)
        file_handler.setFormatter(self.formatter)
        self.logger.addHandler(file_handler)

    def _logprint(self, level,  *args, **kwargs):
        if "end" in kwargs:
            if self.currentformat == 'normal':
                self.formattoggle = True
            self.set_terminator(char=kwargs["end"])
            kwargs.pop("end")
        elif self.currentformat == 'plain':
            self.formattoggle = True

        self.logger.log(level, *args, **kwargs)
        
        if self.formattoggle:
            self.toggle_formatter()
            self.formattoggle = False
            self.set_terminator()

    def info(self, *args, **kwargs):
        self._logprint(logging.INFO, *args, **kwargs)

    def warn(self, *args, **kwargs):
        self._logprint(logging.WARNING, *args, **kwargs)

    def debug(self, *args, **kwargs):
        self._logprint(logging.DEBUG, *args, **kwargs)

    def error(self, *args, **kwargs):
        self._logprint(logging.ERROR, *args, **kwargs)


    def toggle_formatter(self):
        if self.currentformat == 'normal':
            formatter = self.formatter_plain
            self.currentformat = 'plain'
        else:
            formatter = self.formatter
            self.currentformat = 'normal'
        for h in self.logger.handlers:
            h.setFormatter(formatter)

    def set_terminator(self, char='\n'):
        for h in self.logger.handlers:
            h.terminator = char

    def close(self):
        handlers = self.logger.handlers[:]
        for h in handlers:
            self.logger.removeHandler(h)
            h.close()
            