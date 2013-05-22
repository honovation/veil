#coding=utf-8
from __future__ import unicode_literals, print_function, division
from cStringIO import StringIO
from datetime import timedelta
import functools
import logging
import random
import uuid
import os
from PIL import Image, ImageDraw, ImageFont
from veil_installer import *
from veil.frontend.template import *
from veil.frontend.web import *
from veil.backend.bucket import *
from veil.backend.redis import *
from veil.environment import *

LOGGER = logging.getLogger(__name__)

bucket = register_bucket('captcha_image')
redis = register_redis('captcha_answer')

CAPTCHA_ANSWER_ALIVE_TIME = timedelta(minutes=5)

def register_captcha(website):
    add_application_sub_resource(
        'captcha_image_bucket',
        lambda config: bucket_resource(purpose='captcha_image', config=config))
    add_application_sub_resource(
        'captcha_answer_redis_client',
        lambda config: redis_client_resource(purpose='captcha_answer', **config))
    import_widget(captcha_widget)
    route('GET', '/captcha', website=website, tags=('PUBLIC',))(captcha_widget)
    return captcha_protected


@widget
def captcha_widget():
    challenge_code, captcha_image_url = generate_captcha()
    return get_template('captcha.html').render(challenge_code=challenge_code, captcha_image_url=captcha_image_url)


def generate_captcha():
    challenge_code = uuid.uuid4().get_hex()
    image, answer = generate(size=(150, 30), font_size=25)
    redis().setex(challenge_code, CAPTCHA_ANSWER_ALIVE_TIME, answer)
    buffer = StringIO()
    image.save(buffer, 'GIF')
    buffer.reset()
    bucket().store(challenge_code, buffer)
    return challenge_code, bucket().get_url(challenge_code)


def captcha_protected(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        challenge_code = get_http_argument('captcha_challenge_code', optional=True)
        delete_http_argument('captcha_challenge_code')
        captcha_answer = get_http_argument('captcha_answer', optional=True)
        delete_http_argument('captcha_answer')
        kwargs['captcha_errors'] = validate_captcha(challenge_code, captcha_answer)
        return func(*args, **kwargs)

    return wrapper


def validate_captcha(challenge_code, captcha_answer):
    request = get_current_http_request()
    real_answer = redis().get(challenge_code)
    if 'test' == VEIL_SERVER or (captcha_answer and real_answer == captcha_answer):
        if 'test' != VEIL_SERVER:
            LOGGER.info('[sensitive]validate captcha succeeded: %(site)s, %(function)s, %(uri)s, %(referer)s, %(remote_ip)s, %(user_agent)s', {
                'site': request.host,
                'function': 'captcha',
                'uri': request.uri,
                'referer': request.headers.get('Referer'),
                'remote_ip': request.remote_ip,
                'user_agent': request.headers.get('User-Agent')
            })
        bucket().delete(challenge_code)
        return {}
    else:
        LOGGER.warn('[sensitive]validate captcha failed: %(site)s, %(function)s, %(user_answer)s, %(real_answer)s, %(uri)s, %(referer)s, %(remote_ip)s, %(user_agent)s', {
            'site': request.host,
            'function': 'captcha',
            'user_answer': captcha_answer,
            'real_answer': real_answer,
            'uri': request.uri,
            'referer': request.headers.get('Referer'),
            'remote_ip': request.remote_ip,
            'user_agent': request.headers.get('User-Agent')
        })
        return {'captcha_answer': ['验证码错误，请填入正确的计算结果']}


def generate(size=(180, 30),
             img_type="GIF",
             mode="RGB",
             bg_color=(255, 255, 255),
             fg_color=(0, 0, 255),
             font_size=100,
             font_type="{}/wqy-microhei.ttc".format(os.path.dirname(__file__)),
             draw_lines=False,
             n_line=(1, 2),
             draw_points=False,
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

    width, height = size
    img = Image.new(mode, size, bg_color)
    draw = ImageDraw.Draw(img)

    numbers = range(1, 11)
    operator = [u'+', u'-', u'x']

    def get_question():
        first_number = random.choice(numbers)
        selected_operator = random.choice(operator)
        question = str(first_number) + selected_operator
        if selected_operator == u'-':
            second_number = 0
            while True:
                second_number = random.choice(numbers)
                if second_number <= first_number:
                    break
            question += str(second_number)
        else:
            question += str(random.choice(numbers))
        eval_question = question.replace(u'+', '+').replace(u'-', '-').replace(u'x', '*')
        answer = str(eval(eval_question))

        return question+'= ?', answer

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
        draw.text((0, 0), strs, font=font, fill=fg_color)

        return answer

    if draw_lines:
        create_lines()
    if draw_points:
        create_points()
    answer = create_strs()
    #img = img.filter(ImageFilter.EDGE_ENHANCE_MORE) # 滤镜，边界加强（阈值更大）

    return img, answer
