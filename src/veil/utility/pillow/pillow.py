# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division
import logging
from cStringIO import StringIO
import PIL.Image
import PIL.ImageFile

LOGGER = logging.getLogger(__name__)

PIL.ImageFile.MAXBLOCK = PIL.ImageFile.SAFEBLOCK

def open_image(fp):
    try:
        return PIL.Image.open(fp)
    except Exception:
        LOGGER.warn('无法读取上传的图片: %(fp)s', {'fp': fp}, exc_info=1)
        raise


def save_image(image, bucket, key, format=None, delete_image=True, quality=95, optimize=True):
    if not isinstance(image, PIL.Image.Image):
        image = open_image(image)
    buffer_ = StringIO()
    image_format = format or image.format
    try:
        try:
            image.save(buffer_, image_format, quality=quality, optimize=optimize) # JPEG默认保存质量是75, 不太清楚。可选值(0~100, 推荐75~95)
        except IOError:
            # max block is not enough for saving this image, then use the square of max value in image's size
            old_max_block = PIL.ImageFile.MAXBLOCK
            try:
                PIL.ImageFile.MAXBLOCK = max(image.size) ** 2
                image.save(buffer_, image_format, quality=quality, optimize=optimize)
            finally:
                PIL.ImageFile.MAXBLOCK = old_max_block
        buffer_.reset()
        bucket().store(key, buffer_)
    finally:
        buffer_.close()
    if delete_image:
        del image


def crop_image(image, box, bucket, key, format=None, delete_image=True, quality=95, optimize=True):
    # ImageOps compatible mode
    if image.mode not in ("L", "RGB"):
        image = image.convert("RGB")
    save_image(image.crop(box), bucket, key, format=format, delete_image=delete_image, quality=quality, optimize=optimize)


def generate_thumbnail(image, size, bucket, key, format=None, delete_image=True, quality=92, optimize=True):
    # ImageOps compatible mode
    if image.mode not in ("L", "RGB"):
        image = image.convert("RGB")
    image.thumbnail(size, PIL.Image.ANTIALIAS)
    save_image(image, bucket, key, format=format, delete_image=delete_image, quality=quality, optimize=optimize)
