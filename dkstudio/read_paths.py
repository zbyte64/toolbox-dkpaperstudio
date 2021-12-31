import re
import os


FILE_FORMATS = [
    r"(?P<format>(SVG|PNG|DXF))_(?P<variation>[A-Z_]+)_(?P<design>[\w_]+)_(?P<size>\d+(oz|OZ))\.(?P<extension>\w+)",
    r"(?P<variation>[A-Z_]+)_(?P<design>[\w_]+)_(?P<size>\d+(oz|OZ))\.(?P<extension>\w+)",
    r"(?P<variation>[A-Z_]+)_(?P<size>\d+(oz|OZ))_(?P<design>[\w_]+)\.(?P<extension>\w+)",
]
SIGNIFIERS = {
    "is_sublimation": r"(?i).*/SUBLIMINATION_.*",
    "is_bonus": r"(?i).*/BONUS SVG.*",
    "is_instructions": r".*\.pdf$",
    "is_design": r".*\.(png|dxf|svg)$",
    "is_mirrored": r"(?i).*/mirrored.*",
}
MUG_SIZE = r"(?i)\d+oz"
OUTPUT_FOLDER_STRUCTURE = {
    "design": ["{design_folder_name}", "{size}", "{format}"],
    "bonus": ["{design_folder_name}", "{variation}"],
    "sublimation": ["{design_folder_name}", "SUBLIMATION", "{size}", "{variation}"],
    "instructions": ["{design_folder_name}"],
}


def read_path_into_struct(apath):
    """
    Given a path, return attributes
    """
    parts = apath.split(os.path.sep)
    info = {}
    for part_index, apart in enumerate(parts):
        if part_index == len(parts) - 1:
            # extract info from filename
            ext = apart.split(".")[-1]
            if info["is_design"] and not info["is_bonus"]:
                info["format"] = ext.upper()
                for format in FILE_FORMATS:
                    m = re.match(format, info["filename"])
                    if m:
                        info.update(m.groupdict())
                        break
        elif len(info):
            # is a subfolder
            if re.match(MUG_SIZE, apart):
                info["size"] = apart
            elif "varation" in info:
                # additional variation
                pass
            else:
                info["variation"] = apart
        elif apart.endswith("_FILES"):
            info["design"] = info["design_folder_name"] = apart[: -len("_FILES")]
    return info
