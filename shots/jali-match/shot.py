"""Which photo the chain works on, and where it writes (C-022).

By default: this folder's own photo (photo/agra-jali.jpg), its out/, results/ and sheet.jpg, and the constants C-007 to
C-021 used, so the jali-match shot builds exactly as before. With JALI_SHOT=<folder> in the environment: that folder's
photo and outputs, and what <folder>/shot.json says about the photo:

  photo       the file's name in <folder>/photo/
  size        [w, h], the file's pixels
  work        [w, h], the size the chain works at (default here: half the photo, 1230 x 1402)
  lens_mm     the camera's focal length, 35 mm equivalent
  sensor_mm   the sensor width that focal length implies across the photo's width (35 mm equivalent)
  width_m     the screen's width in metres (an estimate unless measured)
  credit      the line the sheet prints under the photo

Only os and json here: normals.py and intrinsics.py import it in the .venv, the rest in Blender."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
FOLDER = os.path.abspath(os.environ.get("JALI_SHOT", HERE))
_META = os.path.join(FOLDER, "shot.json")
META = json.load(open(_META)) if os.path.exists(_META) else {}
PHOTO = os.path.join(FOLDER, "photo", META.get("photo", "agra-jali.jpg"))
OUT = os.path.join(FOLDER, "out")
RESULTS = os.path.join(FOLDER, "results")
SHEET = os.path.join(FOLDER, "sheet.jpg")
PHOTO_SIZE = tuple(META.get("size", (2460, 2803)))
WORK = tuple(META.get("work", (1230, 1402)))                         # this photo at half size (common.SCALE)
WIDTH_M = META.get("width_m", 1.05)                                    # an estimate (photo/CREDIT.md)
# Ours: a Samsung SM-G998B main camera, 24 mm equivalent (EXIF). Assumed: a 12 MP 3000 x 4000 portrait frame cropped to
# 2460 px wide, so the crop spans 2460 / 3000 of the 25.96 mm equivalent short side of a 4:3 frame.
LENS_MM = META.get("lens_mm", 24.0)
SENSOR_MM = META.get("sensor_mm", 25.96 * 2460 / 3000)
CREDIT = META.get("credit", "photograph (Prof. Mortel, CC BY 2.0)")
DEFAULT = FOLDER == HERE
