# -*- coding: utf-8 -*-
"""
    Region Utility
    基于中国统计局行政区划代码数据：http://www.stats.gov.cn/tjsj/tjbz/xzqhdm/
    依赖应用有region表，并有code(PK), name, level, has_child, parent_code, deleted列，如果code不是主键需要有SERIAL主键并且在code上有UNIQUE

    init：初始化region表数据，并使用最新统计局数据，version记录在REGION_VERSION_TABLE中
    check-update：检查当前数据与最新数据的变化
    update：更新到最新版本的数据并将原数据备份到REGION_BACKUP_TABLE中
    rollback-update：回滚备份的数据到REGION_TABLE中
"""
from __future__ import unicode_literals, print_function, division
import logging
import re
from datetime import date
from collections import OrderedDict
from pyquery import PyQuery as pq
from veil.utility.encoding import *
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
    db = lambda: require_database(purpose)

    @transactional(db)
    def init():
        if db().get_scalar('SELECT COUNT(*) FROM {REGION_TABLE}'.format(REGION_TABLE=REGION_TABLE)) != 0:
            LOGGER.warn('can not initialize region table: already initialized')
            return
        db().execute('''
            DROP TABLE IF EXISTS {REGION_BACKUP_TABLE};
            DROP TABLE IF EXISTS {REGION_VERSION_TABLE};
            CREATE TABLE {REGION_BACKUP_TABLE} AS TABLE {REGION_TABLE};
            CREATE TABLE {REGION_VERSION_TABLE} (
                id SERIAL PRIMARY KEY,
                due_date DATE NOT NULL,
                published_at DATE NOT NULL,
                applied_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
        '''.format(REGION_TABLE=REGION_TABLE, REGION_BACKUP_TABLE=REGION_BACKUP_TABLE, REGION_VERSION_TABLE=REGION_VERSION_TABLE))

        response = requests.get(CONTENTS_URL, headers=HEADERS)
        response.encoding = 'UTF-8'
        latest_gov_region_version = extract_gov_latest_region_version(pq(response.text)('ul.center_list_contlist'))
        LOGGER.info('latest gov region version: %(latest_gov_region_version)s', {'latest_gov_region_version': latest_gov_region_version})

        add_regions(db, list_gov_latest_region(latest_gov_region_version))

        validate_regions(db)

        db().insert(REGION_VERSION_TABLE, due_date=latest_gov_region_version.due_date, published_at=latest_gov_region_version.published_at)

    init()


@script('check-update')
def check_region_update(purpose):
    db = lambda: require_database(purpose)

    @transactional(db)
    def check_update():
        latest_db_region_version = db().get('SELECT * FROM {REGION_VERSION_TABLE} ORDER BY id DESC FETCH FIRST ROW ONLY'.format(REGION_VERSION_TABLE=REGION_VERSION_TABLE))
        if not latest_db_region_version:
            LOGGER.error('can not check update: can not find region version in db')
            return
        response = requests.get(CONTENTS_URL, headers=HEADERS)
        response.encoding = 'UTF-8'
        gov_latest_region_version = extract_gov_latest_region_version(pq(response.text)('ul.center_list_contlist'))
        if gov_latest_region_version.published_at <= latest_db_region_version.published_at:
            LOGGER.debug('local region version: %(l_published_at)s, latest region version: %(r_published_at)s', {
                'l_published_at': latest_db_region_version.published_at,
                'r_published_at': gov_latest_region_version.published_at
            })
            LOGGER.info('no updates')
            return
        LOGGER.info('region version in db: due date: %(due_date)s, published date: %(published_at)s', {
            'due_date': latest_db_region_version.due_date,
            'published_at': latest_db_region_version.published_at
        })
        LOGGER.info('region version in stats.gov.cn: due date: %(due_date)s, published date: %(published_at)s', {
            'due_date': gov_latest_region_version.due_date,
            'published_at': gov_latest_region_version.published_at
        })
        latest_regions = list_gov_latest_region(gov_latest_region_version)
        local_regions = list_local_regions(purpose)

        added_codes, deleted_codes, modified_codes = diff(local_regions, latest_regions)

        for code in added_codes:
            print(green('+ {}: {}'.format(code, latest_regions[code])))

        for code in deleted_codes:
            print(red('- {}: {}'.format(code, local_regions[code].name)))

        for code in modified_codes:
            if local_regions[code].deleted:
                print(yellow('[恢复]{}: {} -> {}'.format(code, local_regions[code].name, latest_regions[code])))
            else:
                print(yellow('{}: {} -> {}'.format(code, local_regions[code].name, latest_regions[code])))

        print(blue('{} added keys'.format(len(added_codes))))
        print(blue('{} deleted keys'.format(len(deleted_codes))))
        print(blue('{} modified keys'.format(len(modified_codes))))

        return added_codes, deleted_codes, modified_codes, latest_regions, gov_latest_region_version

    return check_update()


def validate_regions(db):
    invalid_regions = db().list_scalar('''
        SELECT code
            FROM {REGION_TABLE}
            WHERE level NOT IN (1, 2, 3) OR level=1 AND parent_code IS NOT NULL OR level!=1 AND parent_code IS NULL
        UNION
        SELECT c.code
            FROM {REGION_TABLE} c
                INNER JOIN region p ON p.code=c.parent_code
            WHERE c.level!=p.level+1
    '''.format(REGION_TABLE=REGION_TABLE))
    if invalid_regions:
        raise Exception('invalid regions with wrong level: {}'.format(invalid_regions))
    invalid_regions = db().list_scalar('''
        SELECT r.code
        FROM {REGION_TABLE} r
        WHERE r.has_child AND NOT EXISTS (SELECT 1 FROM {REGION_TABLE} c WHERE c.parent_code=r.code)
            OR NOT r.has_child AND EXISTS (SELECT 1 FROM {REGION_TABLE} c WHERE c.parent_code=r.code)
    '''.format(REGION_TABLE=REGION_TABLE))
    if invalid_regions:
        raise Exception('invalid regions with wrong has_child: {}'.format(invalid_regions))
    invalid_regions = db().list_scalar('''
        SELECT code
            FROM {REGION_TABLE}
            WHERE LENGTH(code)!=6 OR level=1 AND code!=(SUBSTRING(code,  1, 2)||'0000') OR level=2 AND code!=(SUBSTRING(code,  1, 4)||'00')
        UNION
        SELECT c.code
            FROM {REGION_TABLE} c
                INNER JOIN region p ON p.code=c.parent_code
            WHERE c.code NOT LIKE CASE c.level WHEN 2 THEN SUBSTRING(p.code, 1, LENGTH(p.code)-4)||'__00' ELSE SUBSTRING(p.code, 1, LENGTH(p.code)-2)||'__' END
    '''.format(REGION_TABLE=REGION_TABLE))
    if invalid_regions:
        raise Exception('invalid regions with wrong codes: {}'.format(invalid_regions))


@script('validate')
def validate_regions_script(purpose):
    db = lambda: require_database(purpose)
    validate_regions(db)


@script('update')
def update_region(purpose):
    db = lambda: require_database(purpose)

    @transactional(db)
    def update():
        added_codes, deleted_codes, modified_codes, gov_latest_region, gov_latest_region_version = check_region_update(purpose)
        if any(e for e in (added_codes, deleted_codes, modified_codes)):
            LOGGER.info('backup old region table')
            db().execute('DROP TABLE IF EXISTS region_backup')
            db().execute('CREATE TABLE region_backup AS TABLE region')

            LOGGER.info('updating region table')
            add_regions(db, {ac: gov_latest_region[ac] for ac in added_codes})
            db().executemany(
                "UPDATE {REGION_TABLE} SET deleted=TRUE WHERE NOT deleted AND code=%(code)s".format(REGION_TABLE=REGION_TABLE),
                [DictObject(code=code) for code in deleted_codes]
            )
            db().executemany(
                'UPDATE {REGION_TABLE} SET name=%(name)s, deleted=FALSE WHERE code=%(code)s'.format(REGION_TABLE=REGION_TABLE),
                [DictObject(code=code, name=gov_latest_region[code]) for code in modified_codes]
            )

            db().insert(REGION_VERSION_TABLE, due_date=gov_latest_region_version.due_date, published_at=gov_latest_region_version.published_at)

            validate_regions(db)

            LOGGER.info('update finished')

    update()


@script('rollback-update')
def rollback_update(purpose):
    db = lambda: require_database(purpose)

    @transactional(db)
    def rollback():
        db_region_versions = db().list('SELECT * FROM {REGION_VERSION_TABLE} ORDER BY id DESC FETCH FIRST 2 ROWS ONLY'.format(REGION_VERSION_TABLE=REGION_VERSION_TABLE))
        if not db_region_versions:
            LOGGER.error('can not rollback: can not find region version')
            return
        if db().get_scalar('SELECT COUNT(*) FROM {REGION_BACKUP_TABLE}'.format(REGION_BACKUP_TABLE=REGION_BACKUP_TABLE)) == 0:
            LOGGER.error('can not rollback: no data in backup table')
            return
        LOGGER.info('current region version: published at %(published_at)s, applied_at: %(applied_at)s', {
            'published_at': db_region_versions[0].published_at, 'applied_at': db_region_versions[0].applied_at
        })
        if len(db_region_versions) >= 2:
            LOGGER.info('will rollback to region version: published at %(published_at)s, applied_at: %(applied_at)s', {
                'published_at': db_region_versions[1].published_at, 'applied_at': db_region_versions[1].applied_at
            })
        db().execute('''
            UPDATE {REGION_TABLE} r
            SET name=rb.name, level=rb.level, has_child=rb.has_child, parent_code=rb.parent_code, deleted=rb.deleted
            FROM {REGION_BACKUP_TABLE} rb
            WHERE r.code=rb.code
            '''.format(REGION_TABLE=REGION_TABLE, REGION_BACKUP_TABLE=REGION_BACKUP_TABLE))
        try:
            deleted_count = db().execute('DELETE FROM {REGION_TABLE} WHERE code NOT IN (SELECT code FROM {REGION_BACKUP_TABLE})'.format(REGION_TABLE=REGION_TABLE, REGION_BACKUP_TABLE=REGION_BACKUP_TABLE))
        except Exception:
            LOGGER.error('can not delete rows in %(REGION_TABLE)s but not in backup table', {'REGION_TABLE': REGION_TABLE})
            raise
        else:
            if deleted_count > 0:
                LOGGER.info('number of deleted regions: %(count)s', {'count': deleted_count})
        db().execute('DELETE FROM {REGION_BACKUP_TABLE}'.format(REGION_BACKUP_TABLE=REGION_BACKUP_TABLE))
        db().execute('DELETE FROM {REGION_VERSION_TABLE} WHERE id=(SELECT MAX(id) FROM {REGION_VERSION_TABLE})'.format(REGION_VERSION_TABLE=REGION_VERSION_TABLE))
        LOGGER.info('rollback update finished')

    try:
        rollback()
    except Exception:
        LOGGER.exception('rollback failed')


def extract_gov_latest_region_version(contents):
    contents.find('li.cont_line').remove()
    latest_region = pq(contents.children()[0])
    return DictObject(
        url=latest_region.find('a').attr('href'),
        due_date=date(*(int(e) for e in re.match('.*(\d{4})年(\d{1,2})月(\d{1,2})日.*', latest_region.find('.cont_tit03').text()).groups())),
        published_at=to_date()(latest_region.find('.cont_tit02').text())
    )


def list_gov_latest_region(latest_region_version):
    url = '{}{}'.format(CONTENTS_URL if 'gov.cn' not in latest_region_version.url else '', latest_region_version.url)
    response = requests.get(url, headers=HEADERS)
    response.encoding = 'UTF-8'
    region_content = pq(response.text)('.xilan_con').find('p')
    region = {}
    for p in region_content:
        text = pq(p).text()
        parts = text.split()
        if parts[0].isdigit():
            region[parts[0]] = ''.join(e for e in parts[1:])
        else:
            raise Exception('invalid lines: {}'.format(text))
    return region


def list_local_regions(purpose):
    db = lambda: require_database(purpose)
    return {r.code: r for r in db().list('SELECT * FROM {REGION_TABLE}'.format(REGION_TABLE=REGION_TABLE))}


def diff(local_regions, latest_regions):
    local_codes = set(local_regions)
    latest_codes = set(latest_regions)
    added_codes = latest_codes - local_codes
    deleted_codes = set(code for code in local_codes - latest_codes if not local_regions[code].deleted)
    modified_codes = set(code for code in local_codes & latest_codes if (local_regions[code].name, local_regions[code].deleted) != (latest_regions[code], False))

    return added_codes, deleted_codes, modified_codes


def add_regions(db, regions):
    new_regions = []
    for code in regions:
        if code[2:] == '0000':
            level = 1
            parent_code = None
        elif code[4:] == '00':
            level = 2
            parent_code = '{}0000'.format(code[:2])
        else:
            level = 3
            parent_code = '{}00'.format(code[:4])
        new_regions.append(DictObject(code=code, name=regions[code], level=level, parent_code=parent_code))
    LOGGER.info('number of to-be-inserted regions: %(region_count)s', {'region_count': len(new_regions)})
    db().insert(REGION_TABLE, new_regions, code=lambda r: r.code, name=lambda r: r.name, level=lambda r: r.level, has_child=False, parent_code=lambda r: r.parent_code)
    db().execute('''
        UPDATE {REGION_TABLE} r
        SET has_child=EXISTS(SELECT 1 FROM {REGION_TABLE} WHERE NOT deleted AND parent_code=r.code)
        '''.format(REGION_TABLE=REGION_TABLE))


@script('fdiff')
def file_diff_script(file1, file2):
    """
    :param file1: old file source
    :param file2: latest file source
    :return: nothing, print diff from file1 to file2
    """

    def to_dict(lines):
        d = OrderedDict()
        for line in lines:
            line = line.strip()
            if not line:
                continue
            line = to_unicode(line)
            code, name = line.split()
            if code[2:] == '0000':
                d[code] = DictObject(code=code, name=name, cities=OrderedDict())
            elif code[4:] == '00':
                parent_code = '{}0000'.format(code[:2])
                if parent_code not in d:
                    print('can not find parent of {} {}'.format(code, name))
                else:
                    d[parent_code].cities[code] = DictObject(code=code, name=name, districts=OrderedDict())
            else:
                parent_code = '{}00'.format(code[:4])
                parent_code2 = '{}0000'.format(code[:2])
                if parent_code2 not in d:
                    print('can not find parent2 of {} {}'.format(code, name))
                elif parent_code not in d[parent_code2].cities:
                    print('can not find parent of {} {}'.format(code, name))
                else:
                    d[parent_code2].cities[parent_code].districts[code] = DictObject(code=code, name=name)
        return d

    with open(file1) as f1:
        f1_dict = to_dict(f1.readlines())

    with open(file2) as f2:
        f2_dict = to_dict(f2.readlines())

    def list_changes(old, new):
        """
        :param old: {code1: name1, code2:name2, ..., codeN:nameN}
        :param new: {code1: name1, code2:name2, ..., codeN:nameN}
        :return: news, renames, deletes
        """
        news = []
        renames = []
        deletes = []
        for e in new.values():
            if e.code not in old:
                news.append(e)
            elif e.name != old[e.code].name:
                e.old_name = old[e.code].name
                renames.append(e)
        for e in old.values():
            if e.code not in new:
                deletes.append(e)
        return news, renames, deletes

    for code, province in f2_dict.items():
        new_cities, rename_cities, delete_cities = list_changes(f1_dict[code].cities, province.cities)
        if new_cities or rename_cities or delete_cities:
            for city in new_cities:
                print(green('{}: +{} {}'.format(province.name, city.code, city.name)))
            for city in rename_cities:
                print(yellow('{}: -+{} {}->{}'.format(province.name, city.code, city.old_name, city.name)))
            for city in delete_cities:
                print(red('{}: -{} {}'.format(province.name, city.code, city.name)))
        for city in province.cities.values():
            f1_city = f1_dict[code].cities.get(city.code)
            if f1_city:
                new_districts, rename_districts, delete_districts = list_changes(f1_city.districts, city.districts)
                if new_districts or rename_districts or delete_districts:
                    for district in new_districts:
                        print(green('{}#{}: +{} {}'.format(province.name, city.name, district.code, district.name)))
                    for district in rename_districts:
                        print(yellow('{}#{}: -+{} {}->{}'.format(province.name, city.name, district.code, district.old_name, district.name)))
                    for district in delete_districts:
                        print(red('{}#{}: -{} {}'.format(province.name, city.name, district.code, district.name)))
