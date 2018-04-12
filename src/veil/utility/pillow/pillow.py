# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division

import base64
import contextlib
import logging
from cStringIO import StringIO
import random
import os
import PIL.Image
import PIL.ImageFile
import PIL.ImageDraw
import PIL.ImageFont

LOGGER = logging.getLogger(__name__)

PIL.ImageFile.MAXBLOCK = PIL.ImageFile.SAFEBLOCK


def open_image(fp):
    try:
        return PIL.Image.open(fp)
    except Exception:
        LOGGER.warn('无法读取上传的图片: %(fp)s', {'fp': fp}, exc_info=1)
        raise InvalidImage('无法读取上传的图片: {}'.format(fp))


def save_image(image_path, bucket, key, format=None, quality=95, optimize=True, limit_width=None, limit_height=None, width_scope=(), height_scope=()):
    image = open_image(image_path)
    _save_image(image, bucket, key, format, quality, optimize, limit_width, limit_height, width_scope, height_scope)


def save_image_by_base64(image_base64, bucket, key, format=None, quality=95, optimize=True, limit_width=None, limit_height=None, width_scope=(),
                         height_scope=()):
    image_base64 = image_base64.split('base64,')[1] if 'base64,' in image_base64 else image_base64
    image = open_image(StringIO(base64.b64decode(image_base64)))
    _save_image(image, bucket, key, format, quality, optimize, limit_width, limit_height, width_scope, height_scope)


def _save_image(image, bucket, key, format, quality, optimize, limit_width, limit_height, width_scope, height_scope):
    """
    :param image:
    :param bucket:
    :param key:
    :param format:
    :param quality:
    :param optimize:
    :param limit_width: 宽度限制，不能与 width_scope 同时存在
    :param limit_height: 高度限制，不能与 height_scope 同时存在
    :param width_scope: 宽度范围，格式为元组，当不为空时，必须包含两个参数（最小值，最大值），最大值与最小值可设为None表示无限制，但不能同时为None
    :param height_scope: 高度范围，格式为元组，当不为空时，必须包含两个参数（最小值，最大值），最大值与最小值可设为None表示无限制，但不能同时为None
    """
    assert not (limit_width and width_scope) and not (limit_height and height_scope), 'limit and scope cannot be both appear'
    if limit_width and image.size[0] != limit_width:
        raise InvalidImage('图片尺寸不正确，请上传宽度为{}px的图片'.format(limit_width))
    if width_scope:
        assert isinstance(width_scope, tuple) and len(width_scope) == 2, 'width scope must include two parameters'
        assert (width_scope[0] or width_scope[1]) and (not width_scope[1] or width_scope[1] > width_scope[0])
        if width_scope[0] and image.size[0] < width_scope[0]:
            raise InvalidImage('图片尺寸不正确，请上传宽度不小于{}px的图片'.format(width_scope[0]))
        if width_scope[1] and image.size[0] > width_scope[1]:
            raise InvalidImage('图片尺寸不正确，请上传宽度不大于{}px的图片'.format(width_scope[1]))

    if limit_height and image.size[1] != limit_height:
        raise InvalidImage('图片尺寸不正确，请上传高度为{}px的图片'.format(limit_height))
    if height_scope:
        assert isinstance(height_scope, tuple) and len(height_scope) == 2, 'height scope must include two parameters'
        assert (height_scope[0] or height_scope[1]) and (not height_scope[1] or height_scope[1] > height_scope[0])
        if height_scope[0] and image.size[0] < height_scope[0]:
            raise InvalidImage('图片尺寸不正确，请上传高度不小于{}px的图片'.format(height_scope[0]))
        if height_scope[1] and image.size[0] > height_scope[1]:
            raise InvalidImage('图片尺寸不正确，请上传高度不大于{}px的图片'.format(height_scope[1]))

    image_format = format or image.format
    if image_format.lower() == 'gif':
        image.fp.seek(0)
        bucket().store(key, image.fp)
    else:
        with contextlib.closing(StringIO()) as buffer_:
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


def crop_image(image, box, bucket, key, format=None, quality=95, optimize=True):
    image_format = format or image.format
    assert image_format.lower() != 'gif', 'do not support gif thumbnail'
    # ImageOps compatible mode
    if image.mode not in ("L", "RGB"):
        image = image.convert("RGB")

    image = image.crop(box)

    with contextlib.closing(StringIO()) as buffer_:
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


def generate_thumbnail(image_path, size, bucket, key, format=None, quality=92, optimize=True):
    image = open_image(image_path)
    image_format = format or image.format
    assert image_format.lower() != 'gif', 'do not support gif thumbnail'
    # ImageOps compatible mode
    if image.mode not in ("L", "RGB"):
        image = image.convert("RGB")

    image.thumbnail(size, PIL.Image.ANTIALIAS)

    with contextlib.closing(StringIO()) as buffer_:
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


def get_wqy_font(font_size):
    return PIL.ImageFont.truetype('{}/wqy-microhei.ttc'.format(os.path.dirname(__file__)), font_size)


def generate_captcha_image_and_answer(size=(180, 30), mode="RGB", bg_color=(255, 255, 255), fg_color=(0, 0, 255), font_size=100, draw_lines=False,
                                      n_line=(1, 2), draw_points=False, point_chance=2):
    """
    @todo: 生成验证码图片
    @param size: 图片的大小，格式（宽，高），默认为(120, 30)
    @param mode: 图片模式，默认为RGB
    @param bg_color: 背景颜色，默认为白色
    @param fg_color: 前景色，验证码字符颜色，默认为蓝色#0000FF
    @param font_size: 验证码字体大小
    @param draw_lines: 是否划干扰线
    @param n_line: 干扰线的条数范围，格式元组，默认为(1, 2)，只有draw_lines为True时有效
    @param draw_points: 是否画干扰点
    @param point_chance: 干扰点出现的概率，大小范围[0, 100]
    @return: [0]: PIL Image实例
    @return: [1]: 验证码图片中的字符串
    """
    width, height = size
    img = PIL.Image.new(mode, size, bg_color)
    draw = PIL.ImageDraw.Draw(img)

    numbers = range(10)
    operator = ['+', '-', 'x']

    def get_question():
        first_number = random.choice(numbers)
        selected_operator = random.choice(operator)
        if selected_operator == '-':
            second_number = random.choice(range(first_number + 1))
        else:
            second_number = random.choice(numbers)
        question = '{}{}{}'.format(first_number, selected_operator, second_number)
        eval_question = question.replace('x', '*')
        answer = unicode(eval(eval_question))
        return '{}等于?'.format(question), answer

    def create_lines():
        """绘制干扰线"""
        line_num = random.randint(*n_line) # 干扰线条数

        for i in range(line_num):
            # 起始点
            begin = (random.randint(0, size[0]), random.randint(0, size[1]))
            #结束点
            end = (random.randint(0, size[0]), random.randint(0, size[1]))
            draw.line([begin, end], fill=(0, 0, 0))

    def create_points():
        """绘制干扰点"""
        chance = min(100, max(0, int(point_chance))) # 大小限制在[0, 100]

        for w in range(width):
            for h in range(height):
                rand = random.randint(0, 100)
                if rand > 100 - chance:
                    draw.point((w, h), fill=(0, 0, 0))

    def create_strs():
        """绘制验证码字符"""
        c_chars, answer = get_question()
        strs = ' {} '.format(' '.join(c_chars))  # 每个字符前后以空格隔开

        font = get_wqy_font(font_size)
        draw.text((0, 0), strs, font=font, fill=fg_color)

        return answer

    if draw_lines:
        create_lines()
    if draw_points:
        create_points()
    answer = create_strs()
    #img = img.filter(ImageFilter.EDGE_ENHANCE_MORE) # 滤镜，边界加强（阈值更大）

    return img, answer


class InvalidImage(Exception):
    pass
