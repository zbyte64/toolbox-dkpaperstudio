import glob
import sys
import re
import os
import os.path
import shutil
from PIL import Image

PNGS_ARE_MIRRORED = True
KEEP_MIRRORED_IMAGES = False
DRY_RUN = False
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
    info = {k: re.match(r, apath) is not None for k, r in SIGNIFIERS.items()}
    parts = apath.split(os.path.sep)
    ext = apath.split(".")[-1]
    info["design_folder_name"], folders, info["filename"] = (
        parts[0],
        parts[1:-1],
        parts[-1],
    )
    info["design"] = info["design_folder_name"][: -len("_FILES")]
    for folder in folders:
        if re.match(MUG_SIZE, folder):
            info["size"] = folder
        else:
            info["variation"] = folder
    if info["is_design"] and not info["is_bonus"]:
        info["format"] = ext.upper()
        for format in FILE_FORMATS:
            m = re.match(format, info["filename"])
            if m:
                info.update(m.groupdict())
                break
    return info


def format_destdir(outdir, info, outpaths):
    parts = [p.format(**info) for p in outpaths]
    destdir = os.path.join(outdir, *parts)
    return destdir


def write_to(outdir, srcpath, info, outpaths, dry_run=DRY_RUN):
    try:
        destdir = format_destdir(outdir, info, outpaths)
    except:
        print(srcpath)
        print(info)
        raise
    print(srcpath, "->", destdir)
    if not dry_run:
        os.makedirs(destdir, exist_ok=True)
        shutil.copy(srcpath, destdir)


def main():
    indir = sys.argv[1]
    outdir = sys.argv[2]
    all_files = glob.glob(os.path.join(indir, "**/*"), recursive=True)
    for apath in all_files:
        if os.path.isfile(apath):
            file_info = read_path_into_struct(apath[len(indir) :])
            if file_info["is_instructions"]:
                write_to(
                    outdir, apath, file_info, OUTPUT_FOLDER_STRUCTURE["instructions"]
                )
            elif file_info["is_bonus"]:
                write_to(outdir, apath, file_info, OUTPUT_FOLDER_STRUCTURE["bonus"])
            elif file_info["is_sublimation"]:
                write_to(
                    outdir, apath, file_info, OUTPUT_FOLDER_STRUCTURE["sublimation"]
                )
            elif file_info["is_design"]:
                if PNGS_ARE_MIRRORED and apath.endswith(".png"):
                    # image is mirorred
                    image = Image.open(apath)
                    dpi = image.info["dpi"]
                    image = image.transpose(Image.FLIP_LEFT_RIGHT)
                    destdir = format_destdir(
                        outdir, file_info, OUTPUT_FOLDER_STRUCTURE["design"]
                    )
                    if not DRY_RUN:
                        os.makedirs(destdir, exist_ok=True)
                        filename = os.path.split(apath)[-1]
                        # save unmirrored image as vanilla name
                        image.save(os.path.join(destdir, filename), dpi=dpi)
                        if KEEP_MIRRORED_IMAGES:
                            # save orginal mirrored image with a MIRRORED prefix
                            mirrored_name = "MIRRORED_" + filename
                            shutil.copyfile(apath, os.path.join(destdir, mirrored_name))
                else:
                    write_to(
                        outdir, apath, file_info, OUTPUT_FOLDER_STRUCTURE["design"]
                    )
            else:
                print("warn", apath)
                write_to(
                    outdir, apath, file_info, OUTPUT_FOLDER_STRUCTURE["instructions"]
                )
                print(file_info)
    for dir_name in glob.glob(os.path.join(outdir, "*")):
        if os.path.isdir(dir_name):
            file_name = dir_name
            if file_name.endswith("_FILES"):
                file_name = file_name[: -len("_FILES")]
            print("zip up:", file_name)
            if not DRY_RUN:
                shutil.make_archive(file_name, "zip", dir_name)


if __name__ == "__main__":
    main()
