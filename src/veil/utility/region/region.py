# -*- coding: utf-8 -*-
"""
    Region Utility
    基于中国统计局行政区划代码数据：http://www.stats.gov.cn/tjsj/tjbz/xzqhdm/
    依赖应用有region表，并有code(PK), name, parent_code, level, has_child, has_active_child, deleted列，如果code不是主键需要有SERIAL主键并且在code上有UNIQUE

    init：使用最新统计局数据初始化region表，version记录在REGION_VERSION_TABLE中
    validate：检查当前region表数据
    check-for-update：检查当前region表数据与最新统计局数据的差异
    migrate：更新到统计局最新版本的数据并将原数据备份到REGION_BACKUP_TABLE中
    rollback：回滚备份的数据到REGION_TABLE中

    TODO: another source of data http://www.mca.gov.cn/article/sj/tjbz/a/
    TODO: another source of data http://www.mohrss.gov.cn/SYrlzyhshbzb/zhuanti/jinbaogongcheng/jbgcshouyexiazaizhuanqu/
"""
from __future__ import unicode_literals, print_function, division
import logging
import re
from datetime import date
import operator
from pyquery import PyQuery as pq
from veil.utility.http import *
from veil_component import red, green, yellow, blue
from veil.frontend.cli import *
from veil.model.collection import *
from veil.model.binding import *
from veil.backend.database.client import *


LOGGER = logging.getLogger(__name__)

REGION_TABLE = 'region'
REGION_VERSION_TABLE = 'region_version'
REGION_BACKUP_TABLE = 'region_backup'
HEADERS = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.80 Safari/537.36'}
CONTENTS_URL = 'http://www.stats.gov.cn/tjsj/tjbz/xzqhdm/'


@script('init')
def init_region(purpose):
    response = requests.get(CONTENTS_URL, headers=HEADERS)
    response.encoding = 'UTF-8'
    latest_region_version = get_latest_region_version(pq(response.text)('ul.center_list_contlist'))
    LOGGER.info('latest region version: %(latest_region_version)s', {'latest_region_version': latest_region_version})
    latest_code2region = get_latest_code2region(latest_region_version)

    db = lambda: require_database(purpose)

    @transactional(db)
    def init():
        if db().get_scalar('SELECT COUNT(*) FROM {REGION_TABLE}'.format(REGION_TABLE=REGION_TABLE)):
            LOGGER.warn('cannot initialize region table: already initialized')
            return
        db().execute('''
            DROP TABLE IF EXISTS {REGION_BACKUP_TABLE};
            DROP TABLE IF EXISTS {REGION_VERSION_TABLE};
            CREATE TABLE {REGION_BACKUP_TABLE} AS TABLE {REGION_TABLE};
            CREATE TABLE {REGION_VERSION_TABLE} (
                id SERIAL PRIMARY KEY,  -- 编号
                closing_date DATE NOT NULL,  -- 截止日期
                published_at DATE NOT NULL,  -- 发布日期
                applied_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP  -- 应用时间
                );
        '''.format(REGION_TABLE=REGION_TABLE, REGION_BACKUP_TABLE=REGION_BACKUP_TABLE, REGION_VERSION_TABLE=REGION_VERSION_TABLE))

        add_regions(db, latest_code2region.values())
        reset_has_child_and_has_active_child(db)

        validate_regions(db)

        db().insert(REGION_VERSION_TABLE, closing_date=latest_region_version.closing_date, published_at=latest_region_version.published_at)

    init()


@script('validate')
def validate_regions_script(purpose):
    db = lambda: require_database(purpose)
    validate_regions(db)


@script('check-for-update')
def check_for_update(purpose):
    response = requests.get(CONTENTS_URL, headers=HEADERS)
    response.encoding = 'UTF-8'
    latest_region_version = get_latest_region_version(pq(response.text)('ul.center_list_contlist'))
    latest_code2region = get_latest_code2region(latest_region_version)

    db = lambda: require_database(purpose)

    def _check_for_update():
        latest_db_region_version = db().get(
            'SELECT * FROM {REGION_VERSION_TABLE} ORDER BY id DESC FETCH FIRST ROW ONLY'.format(REGION_VERSION_TABLE=REGION_VERSION_TABLE))
        if not latest_db_region_version:
            raise Exception('cannot check update: no region version log')
        if latest_region_version.published_at <= latest_db_region_version.published_at:
            LOGGER.debug('local region version: %(l_published_at)s, latest region version: %(r_published_at)s', {
                'l_published_at': latest_db_region_version.published_at,
                'r_published_at': latest_region_version.published_at
            })
            LOGGER.info('no updates')
            return [], [], [], latest_region_version
        LOGGER.info('region version in db: closing date: %(closing_date)s, published date: %(published_at)s', {
            'closing_date': latest_db_region_version.closing_date,
            'published_at': latest_db_region_version.published_at
        })
        LOGGER.info('region version in stats.gov.cn: closing date: %(closing_date)s, published date: %(published_at)s', {
            'closing_date': latest_region_version.closing_date,
            'published_at': latest_region_version.published_at
        })

        local_code2region = get_local_code2region(db)
        added_regions, deleted_regions, modified_regions = diff(local_code2region, latest_code2region)

        for region in added_regions:
            print(green('+ {}: {}'.format(region.code, region.name)))

        for region in deleted_regions:
            print(red('- {}: {}'.format(region.code, region.name)))

        for region in modified_regions:
            local_region = local_code2region[region.code]
            if local_region.deleted:
                print(yellow('[恢复]{}: {} {} => {} {}'.format(region.code, local_region.name, local_region.parent_code, region.name, region.parent_code)))
            else:
                print(yellow('{}: {} {} => {} {}'.format(region.code, local_region.name, local_region.parent_code, region.name, region.parent_code)))

        print(blue('{} added keys'.format(len(added_regions))))
        print(blue('{} deleted keys'.format(len(deleted_regions))))
        print(blue('{} modified keys'.format(len(modified_regions))))

        return added_regions, deleted_regions, modified_regions, latest_region_version

    return _check_for_update()


@script('migrate')
def migrate(purpose):
    added_regions, deleted_regions, modified_regions, latest_region_version = check_for_update(purpose)
    if not added_regions and not deleted_regions and not modified_regions:
        return

    db = lambda: require_database(purpose)

    @transactional(db)
    def _migrate():
        LOGGER.info('backup old region table')
        db().execute('DROP TABLE IF EXISTS {REGION_BACKUP_TABLE}'.format(REGION_BACKUP_TABLE=REGION_BACKUP_TABLE))
        db().execute('CREATE TABLE {REGION_BACKUP_TABLE} AS TABLE region'.format(REGION_BACKUP_TABLE=REGION_BACKUP_TABLE))
        db().execute('ALTER TABLE {REGION_BACKUP_TABLE} ADD UNIQUE (code)'.format(REGION_BACKUP_TABLE=REGION_BACKUP_TABLE))

        LOGGER.info('adding regions')
        add_regions(db, added_regions)
        if deleted_regions:
            LOGGER.info('deleting regions')
            db().execute('UPDATE {REGION_TABLE} SET deleted=TRUE WHERE code IN %(codes)s AND NOT deleted'.format(REGION_TABLE=REGION_TABLE),
                         codes=tuple(r.code for r in deleted_regions))
        LOGGER.info('updating regions')
        db().executemany(
            'UPDATE {REGION_TABLE} SET name=%(name)s, parent_code=%(parent_code)s, deleted=%(deleted)s WHERE code=%(code)s'.format(REGION_TABLE=REGION_TABLE),
            modified_regions)
        reset_has_child_and_has_active_child(db)

        validate_regions(db)

        db().insert(REGION_VERSION_TABLE, closing_date=latest_region_version.closing_date, published_at=latest_region_version.published_at)

        LOGGER.info('migrate finished')

    _migrate()


@script('rollback')
def rollback(purpose):
    db = lambda: require_database(purpose)

    @transactional(db)
    def _rollback():
        db_region_versions = db().list(
            'SELECT * FROM {REGION_VERSION_TABLE} ORDER BY id DESC FETCH FIRST 2 ROWS ONLY'.format(REGION_VERSION_TABLE=REGION_VERSION_TABLE))
        if len(db_region_versions) != 2:
            raise Exception('cannot rollback: no region version logs')
        if not db().get_scalar('SELECT COUNT(*) FROM {REGION_BACKUP_TABLE}'.format(REGION_BACKUP_TABLE=REGION_BACKUP_TABLE)):
            raise Exception('cannot rollback: no data in backup table')
        LOGGER.info('current region version: published at %(published_at)s, applied_at: %(applied_at)s', {
            'published_at': db_region_versions[0].published_at, 'applied_at': db_region_versions[0].applied_at
        })
        LOGGER.info('will rollback to region version: published at %(published_at)s, applied_at: %(applied_at)s', {
            'published_at': db_region_versions[1].published_at, 'applied_at': db_region_versions[1].applied_at
        })

        LOGGER.info('restoring regions from backup')
        db().execute('''
            UPDATE {REGION_TABLE} r
            SET name=rb.name, parent_code=rb.parent_code, level=rb.level, has_child=rb.has_child, has_active_child=rb.has_active_child, deleted=rb.deleted
            FROM {REGION_BACKUP_TABLE} rb
            WHERE r.code=rb.code
            '''.format(REGION_TABLE=REGION_TABLE, REGION_BACKUP_TABLE=REGION_BACKUP_TABLE))
        try:
            LOGGER.info('deleting regions not in backup')
            deleted_count = db().execute(
                'DELETE FROM {REGION_TABLE} WHERE code NOT IN (SELECT code FROM {REGION_BACKUP_TABLE})'.format(REGION_TABLE=REGION_TABLE,
                                                                                                               REGION_BACKUP_TABLE=REGION_BACKUP_TABLE))
        except Exception:
            LOGGER.error('cannot delete rows in %(REGION_TABLE)s but not in backup table', {'REGION_TABLE': REGION_TABLE})
            raise
        else:
            if deleted_count:
                LOGGER.info('number of deleted regions: %(count)s', {'count': deleted_count})

        db().execute('DROP TABLE {REGION_BACKUP_TABLE}'.format(REGION_BACKUP_TABLE=REGION_BACKUP_TABLE))
        db().execute('DELETE FROM {REGION_VERSION_TABLE} WHERE id=%(id)s'.format(REGION_VERSION_TABLE=REGION_VERSION_TABLE), id=db_region_versions[0].id)

        LOGGER.info('rollback finished')

    try:
        _rollback()
    except Exception:
        LOGGER.exception('rollback failed')

    validate_regions(db)


def get_latest_region_version(contents):
    contents.find('li.cont_line').remove()
    latest_region = pq(contents.children()[0])
    return DictObject(url=latest_region.find('a').attr('href'),
                      closing_date=date(*(int(e) for e in re.match('.*(\d{4})年(\d{1,2})月(\d{1,2})日.*', latest_region.find('.cont_tit03').text()).groups())),
                      published_at=to_date()(latest_region.find('.cont_tit02').text()))


def get_latest_code2region(latest_region_version):
    url = '{}{}'.format(CONTENTS_URL if 'gov.cn' not in latest_region_version.url else '', latest_region_version.url)
    response = requests.get(url, headers=HEADERS)
    response.encoding = 'UTF-8'
    region_content = pq(response.text)('.xilan_con').find('p')
    latest_code2region = {}
    for p in region_content:
        text = pq(p).text()
        parts = text.split()
        code = parts[0]
        if code.isdigit() and len(code) == 6:
            if code[2:] == '0000':
                level = 1
                parent_code = None
            elif code[4:] == '00':
                level = 2
                parent_code = '{}0000'.format(code[:2])
            else:
                level = 3
                parent_code = '{}00'.format(code[:4])
            name = ''.join(e for e in parts[1:])
            latest_code2region[code] = DictObject(code=code, name=name, parent_code=parent_code, level=level, deleted=False)
        else:
            raise Exception('invalid lines: {}'.format(text))
    return latest_code2region


def get_local_code2region(db):
    return {r.code: r for r in db().list('SELECT code, name, parent_code, level, deleted FROM {REGION_TABLE}'.format(REGION_TABLE=REGION_TABLE))}


def diff(local_code2region, latest_code2region):
    local_codes = set(local_code2region)
    latest_codes = set(latest_code2region)
    added_regions = sorted((latest_code2region[code] for code in latest_codes - local_codes), key=operator.attrgetter('code'))
    deleted_regions = sorted((local_code2region[code] for code in local_codes - latest_codes if not local_code2region[code].deleted),
                             key=operator.attrgetter('code'))
    modified_regions = sorted((latest_code2region[code] for code in local_codes & latest_codes if local_code2region[code] != latest_code2region[code]),
                              key=operator.attrgetter('code'))
    return added_regions, deleted_regions, modified_regions


def add_regions(db, regions):
    LOGGER.info('number of to-be-inserted regions: %(region_count)s', {'region_count': len(regions)})
    db().insert(REGION_TABLE, regions, has_child=False, has_active_child=False)


def reset_has_child_and_has_active_child(db):
    db().execute('''
        UPDATE {REGION_TABLE} r
        SET has_child=EXISTS(SELECT 1 FROM {REGION_TABLE} WHERE parent_code=r.code),
            has_active_child=EXISTS(SELECT 1 FROM {REGION_TABLE} WHERE parent_code=r.code AND NOT deleted)
        '''.format(REGION_TABLE=REGION_TABLE))


def validate_regions(db):
    invalid_regions = db().list_scalar('''
        SELECT code
            FROM {REGION_TABLE}
            WHERE level NOT IN (1, 2, 3) OR level=1 AND parent_code IS NOT NULL OR level!=1 AND parent_code IS NULL
        UNION
        SELECT c.code
            FROM {REGION_TABLE} c
                INNER JOIN {REGION_TABLE} p ON p.code=c.parent_code
            WHERE c.level!=p.level+1
    '''.format(REGION_TABLE=REGION_TABLE))
    if invalid_regions:
        raise Exception('invalid regions with wrong level: {}'.format(invalid_regions))
    invalid_regions = db().list_scalar('''
        SELECT r.code
        FROM {REGION_TABLE} r
        WHERE r.has_child AND NOT EXISTS (SELECT 1 FROM {REGION_TABLE} c WHERE c.parent_code=r.code)
            OR NOT r.has_child AND EXISTS (SELECT 1 FROM {REGION_TABLE} c WHERE c.parent_code=r.code)
            OR r.has_active_child AND NOT EXISTS (SELECT 1 FROM {REGION_TABLE} c WHERE c.parent_code=r.code AND NOT deleted)
            OR NOT r.has_active_child AND EXISTS (SELECT 1 FROM {REGION_TABLE} c WHERE c.parent_code=r.code AND NOT deleted)
    '''.format(REGION_TABLE=REGION_TABLE))
    if invalid_regions:
        raise Exception('invalid regions with wrong has_child/has_active_child: {}'.format(invalid_regions))
    invalid_regions = db().list_scalar('''
        SELECT code
            FROM {REGION_TABLE}
            WHERE LENGTH(code)!=6 OR level=1 AND code!=(SUBSTRING(code,  1, 2)||'0000') OR level=2 AND code!=(SUBSTRING(code,  1, 4)||'00')
        UNION
        SELECT c.code
            FROM {REGION_TABLE} c
                INNER JOIN {REGION_TABLE} p ON p.code=c.parent_code
            WHERE c.code NOT LIKE CASE c.level WHEN 2 THEN SUBSTRING(p.code, 1, LENGTH(p.code)-4)||'__00' ELSE SUBSTRING(p.code, 1, LENGTH(p.code)-2)||'__' END
    '''.format(REGION_TABLE=REGION_TABLE))
    if invalid_regions:
        raise Exception('invalid regions with wrong codes: {}'.format(invalid_regions))


REGION_LEVEL2SUFFIX = {
    1: ('省', '市', '壮族自治区', '维吾尔自治区', '回族自治区', '自治区', '特别行政区'),
    2: ('市', '新区', '地区', '蒙古族藏族自治州', '藏族自治州', '朝鲜族自治州', '土家族苗族自治州', '藏族羌族自治州', '哈尼族彝族自治州', '彝族自治州', '布依族苗族自治州',
        '苗族侗族自治州', '傣族自治州', '白族自治州', '傣族景颇族自治州', '傈僳族自治州', '回族自治州', '蒙古自治州', '柯尔克孜自治州', '哈萨克自治州'),
    3: ('市', '新区', '矿区', '区', '彝族回族自治县', '回族自治县', '满族自治县', '满族蒙古族自治县', '蒙古族自治县', '蒙古自治县', '朝鲜族自治县', '畲族自治县',
        '土家族自治县', '土家族苗族自治县', '仡佬族苗族自治县', '布依族苗族自治县', '苗族布依族自治县', '彝族回族苗族自治县', '彝族苗族自治县', '苗族自治县', '瑶族自治县',
        '苗族侗族自治县', '侗族自治县', '各族自治县', '仫佬族自治县', '毛南族自治县', '黎族苗族自治县', '黎族自治县', '羌族自治县', '回族彝族自治县', '傣族彝族自治县',
        '哈尼族彝族自治县', '彝族自治县', '藏族自治县', '水族自治县', '哈尼族自治县', '彝族傣族自治县', '拉祜族佤族布朗族傣族自治县', '纳西族自治县', '彝族哈尼族拉祜族自治县',
        '拉祜族自治县', '哈尼族彝族傣族自治县', '傣族拉祜族佤族自治县', '傣族佤族自治县', '苗族瑶族傣族自治县', '佤族自治县', '独龙族怒族自治县', '白族普米族自治县',
        '傈僳族自治县', '裕固族自治县', '哈萨克族自治县', '哈萨克自治县', '东乡族自治县', '保安族东乡族撒拉族自治县', '回族土族自治县', '土族自治县', '撒拉族自治县',
        '塔吉克自治县', '锡伯自治县', '县', '左旗', '右旗', '中旗', '前旗', '后旗', '联合旗', '左翼前旗', '左翼中旗', '左翼后旗', '右翼前旗', '右翼中旗', '右翼后旗',
        '自治旗', '瓦达斡尔族自治旗', '旗')
}
for k, v in REGION_LEVEL2SUFFIX.items():
    REGION_LEVEL2SUFFIX[k] = sorted(v, key=len, reverse=True)


def list_candidate_region_names(name, level):
    main = get_main_region_name(name, level)
    candidates = ['{}{}'.format(main, s) for s in REGION_LEVEL2SUFFIX[level]]
    return sorted(candidates, key=lambda c: c != name)


def get_main_region_name(name, level):
    matched_suffix = next((s for s in REGION_LEVEL2SUFFIX[level] if name.endswith(s)), None)
    return name[:-len(matched_suffix)] if matched_suffix else name


def list_region_name_patterns(region):
    patterns = [region.name]
    name_len = len(region.name)
    if name_len > 2:
        suffix = next((s for s in REGION_LEVEL2SUFFIX[region.level] if name_len >= len(s) + 2 and region.name.endswith(s)), None)
        if suffix:
            patterns.append(region.name[:-len(suffix)])
    return patterns


def parse_full_address(db, full_address):
    original_full_address = full_address

    provinces = db().list('SELECT * FROM {REGION_TABLE} WHERE level=1'.format(REGION_TABLE=REGION_TABLE))
    province, pattern = next(
        ((province, pattern) for province in provinces for pattern in list_region_name_patterns(province) if full_address.startswith(pattern)), (None, None))
    if pattern:
        full_address = full_address[len(pattern):].strip()
    if not province:
        LOGGER.debug('can not parse province: %(full_address)s', {'full_address': original_full_address})
        return DictObject(province=None, city=None, district=None, address_detail=full_address)

    cities = db().list('SELECT * FROM {REGION_TABLE} WHERE level=2 AND code LIKE %(pattern)s'.format(REGION_TABLE=REGION_TABLE),
                       pattern='{}%'.format(province.code[:2]))
    city, pattern = next(((city, pattern) for city in cities for pattern in list_region_name_patterns(city) if full_address.startswith(pattern)), (None, None))
    if pattern:
        full_address = full_address[len(pattern):].strip()
    districts = db().list('SELECT * FROM {REGION_TABLE} WHERE level=3 AND code LIKE %(pattern)s'.format(REGION_TABLE=REGION_TABLE),
                          pattern='{}%'.format(city.code[:4] if city else province.code[:2]))
    district, pattern = next(
        ((district, pattern) for district in districts for pattern in list_region_name_patterns(district) if full_address.startswith(pattern)), (None, None))
    if pattern:
        if not city:
            city = db().get('SELECT * FROM {REGION_TABLE} WHERE code=%(code)s'.format(REGION_TABLE=REGION_TABLE), code=district.parent_code)
        full_address = full_address[len(pattern):].strip()
    if not city:
        LOGGER.debug('can not parse city: %(full_address)s', {'full_address': original_full_address})
    elif not district:
        LOGGER.debug('can not parse district: %(full_address)s', {'full_address': original_full_address})

    return DictObject(province=province, city=city, district=district, address_detail=full_address)
