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
