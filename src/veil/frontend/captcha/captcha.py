#coding=utf-8
from __future__ import unicode_literals, print_function, division
from cStringIO import StringIO
import functools
import random
import uuid
import os
import logging
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from veil.frontend.template import *
from veil.frontend.web import *
from veil.backend.bucket import *
from veil.backend.redis import *

bucket = register_bucket('captcha_image')
redis = register_redis('captcha_answer')
LOGGER = logging.getLogger(__name__)

def register_captcha(website):
    import_widget(captcha_widget)
    route('GET', '/captcha', website=website)(captcha_widget)
    return captcha_protected


@widget
def captcha_widget():
    challenge_code, captcha_image_url = generate_captcha()
    return get_template('captcha.html').render(challenge_code=challenge_code,
        captcha_image_url=captcha_image_url)


def generate_captcha():
    challenge_code = str(uuid.uuid4()).replace('-', '')
    image, answer = generate(size=(150, 30), font_size=20)
    redis().set(challenge_code, answer)
    redis().expire(challenge_code, 60) #expire 30 seconds
    buffer = StringIO()
    image.save(buffer, 'GIF')
    buffer.reset()
    bucket().store(challenge_code, buffer)
    return challenge_code, bucket().get_url(challenge_code)


def captcha_protected(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        challenge_code = get_http_argument('captcha_challenge_code')
        delete_http_argument('captcha_challenge_code')
        captcha_answer = get_http_argument('captcha_answer', optional=True)
        delete_http_argument('captcha_answer')
        kwargs['captcha_errors'] = validate_captcha(challenge_code, captcha_answer)
        return func(*args, **kwargs)

    return wrapper


def validate_captcha(challenge_code, captcha_answer):
    bucket().delete(challenge_code)
    real_answer = redis().get(challenge_code)
    if real_answer == captcha_answer:
        return {}
    else:
        return {'captcha_answer': ['验证码错误']}


def generate(size=(180, 30),
             img_type="GIF",
             mode="RGB",
             bg_color=(255, 255, 255),
             fg_color=(0, 0, 255),
             font_size=100,
             font_type="{}/wqy-microhei.ttc".format(os.path.dirname(__file__)),
             draw_lines=True,
             n_line=(1, 2),
             draw_points=True,
             point_chance=2):
    '''
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
    '''

    width, height = size # 宽， 高
    img = Image.new(mode, size, bg_color) # 创建图形
    draw = ImageDraw.Draw(img) # 创建画笔

    numbers = range(1, 11)
    operator = [u'加', u'减', u'乘']

    def get_question():
        first_number = random.choice(numbers)
        selected_operator = random.choice(operator)
        question = str(first_number) + selected_operator
        if selected_operator == u'减':
            second_number = 0
            while True:
                second_number = random.choice(numbers)
                if second_number <= first_number:
                    break
            question += str(second_number)
        else:
            question += str(random.choice(numbers))
        eval_question = question.replace(u'加', '+').replace(u'减', '-').replace(u'乘', '*')
        answer = str(eval(eval_question))

        return question + u'等于？', answer

    def create_lines():
        '''绘制干扰线'''
        line_num = random.randint(*n_line) # 干扰线条数

        for i in range(line_num):
            # 起始点
            begin = (random.randint(0, size[0]), random.randint(0, size[1]))
            #结束点
            end = (random.randint(0, size[0]), random.randint(0, size[1]))
            draw.line([begin, end], fill=(0, 0, 0))

    def create_points():
        '''绘制干扰点'''
        chance = min(100, max(0, int(point_chance))) # 大小限制在[0, 100]

        for w in xrange(width):
            for h in xrange(height):
                tmp = random.randint(0, 100)
                if tmp > 100 - chance:
                    draw.point((w, h), fill=(0, 0, 0))

    def create_strs():
        '''绘制验证码字符'''
        c_chars, answer = get_question()
        strs = ' %s ' % ' '.join(c_chars) # 每个字符前后以空格隔开

        font = ImageFont.truetype(font_type, font_size)
        font_width, font_height = font.getsize(strs)
        draw.text(((width - font_width) / 4, height / 4),
            strs, font=font, fill=fg_color)

        return answer

    if draw_lines:
        create_lines()
    if draw_points:
        create_points()
    answer = create_strs()

    # 图形扭曲参数
    params = [1 - float(random.randint(1, 2)) / 100,
              0,
              0,
              0,
              1 - float(random.randint(1, 10)) / 100,
              float(random.randint(1, 2)) / 500,
              0.001,
              float(random.randint(1, 2)) / 500
    ]
    img = img.transform(size, Image.PERSPECTIVE, params) # 创建扭曲

    img = img.filter(ImageFilter.EDGE_ENHANCE_MORE) # 滤镜，边界加强（阈值更大）

    return img, answer
