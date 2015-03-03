# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function, division
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
        raise


def save_image(image, bucket, key, format=None, delete_image=True, quality=95, optimize=True):
    if not isinstance(image, PIL.Image.Image):
        image = open_image(image)
    image_format = format or image.format
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


def generate_captcha_image_and_answer(size=(180, 30), img_type="GIF", mode="RGB", bg_color=(255, 255, 255), fg_color=(0, 0, 255), font_size=100,
        font_type="{}/wqy-microhei.ttc".format(os.path.dirname(__file__)), draw_lines=False, n_line=(1, 2), draw_points=False, point_chance=2):
    """
    @todo: 生成验证码图片
    @param size: 图片的大小，格式（宽，高），默认为(120, 30)
    @param chars: 允许的字符集合，格式字符串
    @param img_type: 图片保存的格式，默认为GIF，可选的为GIF，JPEG，TIFF，PNG
    @param mode: 图片模式，默认为RGB
    @param bg_color: 背景颜色，默认为白色
    @param fg_color: 前景色，验证码字符颜色，默认为蓝色#0000FF
    @param font_size: 验证码字体大小
    @param font_type: 验证码字体，默认为 ae_AlArabiya.ttf
    @param length: 验证码字符个数
    @param draw_lines: 是否划干扰线
    @param n_lines: 干扰线的条数范围，格式元组，默认为(1, 2)，只有draw_lines为True时有效
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

        font = PIL.ImageFont.truetype(font_type, font_size)
        font_width, font_height = font.getsize(strs)
        draw.text((0, 0), strs, font=font, fill=fg_color)

        return answer

    if draw_lines:
        create_lines()
    if draw_points:
        create_points()
    answer = create_strs()
    #img = img.filter(ImageFilter.EDGE_ENHANCE_MORE) # 滤镜，边界加强（阈值更大）

    return img, answer
