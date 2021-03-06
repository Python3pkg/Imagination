# v2
from ..core  import Imagination
from ..debug import dump_meta_container

from .xml import XMLParser


class UnsupportedConfigFileError(RuntimeError):
    """ Error when detect unsupported configuration file """


class Assembler(object):
    def __init__(self, core : Imagination = None):
        self._parsers = [
            XMLParser(),
        ]

        self._core = Imagination()

    @property
    def core(self):
        return self._core

    def load(self, *filepaths):
        meta_container_map = self._load_config_files(*filepaths)

        self.core.update_metadata(meta_container_map)

    def _load_config_files(self, *filepaths):
        meta_container_map = {}

        for filepath in filepaths:
            config_handled = False

            for parser in self._parsers:
                if not parser.can_handle(filepath):
                    continue

                sub_meta_container_map = parser.parse(filepath)

                meta_container_map.update(sub_meta_container_map)

                config_handled = True

            if not config_handled:
                raise UnsupportedConfigFileError(filepath)

        return meta_container_map
