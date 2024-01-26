from configparser import ConfigParser
from dataclasses import dataclass
from pathlib import Path

from magicgui import use_app
from magicgui.types import FileDialogMode

from seg2link import parameters
import os
import glob

CURRENT_DIR = Path.home()
CONFIG_PATH_FILE = Path.home() / ".seg2link_config_path.ini"


def get_last_current_base_dir(CONFIG_DIR):
    """Grabs and shows as default paths the last directory based on config files if saved."""
    config_ = ConfigParser()
    seg2link_configs = glob.glob(f"{CONFIG_DIR}/*.ini")
    if not len(seg2link_configs):
        raise ValueError(f"There are no config files saved in {CONFIG_DIR}.")

    seg2link_configs.sort(key=os.path.getmtime)  # sort files based on last modified
    last_config = Path(seg2link_configs[-1])  # grab the last modified file
    config_.read(last_config)

    global CURRENT_DIR
    CURRENT_DIR = Path(os.path.dirname(config_["parameters_r1r2"]["path_cells"]))
    return CURRENT_DIR


def get_config_dir():
    config_ = ConfigParser()
    if not CONFIG_PATH_FILE.exists():
        raise ValueError(".seg2link_config_path.ini was not found")
    config_.read(CONFIG_PATH_FILE)
    return Path(config_["PATH"]["config_folder"])


def save_config_dir(path: str):
    config_ = ConfigParser()
    config_["PATH"] = {"config_folder": path}
    with open(CONFIG_PATH_FILE, 'w') as configfile:
        config_.write(configfile)


@dataclass
class Pars:
    r1r2: dict
    r1: dict
    r2: dict
    advanced: dict


@dataclass
class UserConfig:
    ini_path: str = None
    pars: Pars = Pars({}, {}, {}, parameters.pars.all_attributes)

    def load_ini(self, current_dir):
        mode_ = FileDialogMode.EXISTING_FILE
        start_path = str(current_dir)
        path = use_app().get_obj("show_file_dialog")(
            mode_,
            caption="Load ini",
            start_path=start_path,
            filter='*.ini'
        )
        if path:
            config_ = ConfigParser()
            config_.read(path)

            self.pars = Pars(
                r1r2=dict(config_["parameters_r1r2"]),
                r1=dict(config_["parameters_r1"]),
                r2=dict(config_["parameters_r2"]),
                advanced=dict(config_["advanced_parameters"])
            )
            self.ini_path = path
        else:
            raise ValueError("No folder selected")

    def save_ini_r1(self, pars_r1, current_dir):
        self.pars.r1 = pars_r1
        self.save_or_save_as(current_dir)

    def save_ini_r2(self, pars_r2, current_dir):
        self.pars.r2 = pars_r2
        self.save_or_save_as(current_dir)

    def save_ini_r1r2(self, pars_r1r2, current_dir):
        self.pars.r1r2 = pars_r1r2
        self.save_or_save_as(current_dir)

    def save_or_save_as(self, current_dir):
        if self.ini_path is None:
            path = self.get_path_save(current_dir)
            if path:
                self.save_ini(Path(path))
            self.ini_path = path
        else:
            self.save_ini(Path(self.ini_path))

    def save_ini(self, filename: Path):
        config_ = ConfigParser()
        config_["parameters_r1r2"] = self.pars.r1r2
        config_["parameters_r1"] = self.pars.r1
        config_["parameters_r2"] = self.pars.r2
        config_["advanced_parameters"] = self.pars.advanced
        with open(filename, 'w') as configfile:
            config_.write(configfile)
        save_config_dir(str(filename.parent))

    def get_path_save(self, current_dir):
        seg_filename = "config.ini"
        mode_ = FileDialogMode.OPTIONAL_FILE
        path = use_app().get_obj("show_file_dialog")(
            mode_,
            caption="Save ini",
            start_path=str(current_dir / seg_filename),
            filter='*.ini'
        )
        return path
