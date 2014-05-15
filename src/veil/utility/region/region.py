# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
import logging
import re
from datetime import date
from veil.backend.database.client import *
from veil.model.collection import *
from veil.frontend.cli import *
from veil.model.binding import *
from pyquery import PyQuery as pq


LOGGER = logging.getLogger(__name__)

REGION_TABLE = 'region'
REGION_VERSION_TABLE = 'region_version'
REGION_BACKUP_TABLE = 'region_backup'
CONTENTS_URL = 'http://www.stats.gov.cn/tjsj/tjbz/xzqhdm/'


@script('init')
def init_region(purpose):
    db = lambda: require_database(purpose)

    @transactional(db)
    def init():
        if db().get_scalar('SELECT COUNT(*) FROM {REGION_TABLE}'.format(REGION_TABLE=REGION_TABLE)) != 0:
            LOGGER.info('can not initialize region table: already initialized')
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

        contents = pq(url=CONTENTS_URL)('ul.center_list_contlist')
        latest_region = get_latest_region(contents)
        LOGGER.info('latest region: %(latest_region)s', {'latest_region': latest_region})

        add_regions(db, get_gov_latest_region(latest_region))

        db().insert(REGION_VERSION_TABLE, due_date=latest_region.due_date, published_at=latest_region.published_at)

    init()


@script('check-update')
def check_region_update(purpose):
    db = lambda: require_database(purpose)

    @transactional(db)
    def check_update():
        latest_region_in_db = db().get('SELECT * FROM {REGION_VERSION_TABLE} ORDER BY id DESC FETCH FIRST ROW ONLY'.format(REGION_VERSION_TABLE=REGION_VERSION_TABLE))
        if not latest_region_in_db:
            LOGGER.info('can not check update: can not find region version in db')
            return
        contents = pq(url=CONTENTS_URL)('ul.center_list_contlist')
        gov_region_info = get_latest_region(contents)
        if gov_region_info.due_date <= latest_region_in_db.due_date and gov_region_info.published_at <= latest_region_in_db.published_at:
            LOGGER.info('no updates')
            return
        LOGGER.info('region version in db: due date: %(due_date)s, published date: %(published_at)s', {
            'due_date': latest_region_in_db.due_date,
            'published_at': latest_region_in_db.published_at
        })
        LOGGER.info('region version in stats.gov.cn: due date: %(due_date)s, published date: %(published_at)s', {
            'due_date': gov_region_info.due_date,
            'published_at': gov_region_info.published_at
        })
        gov_latest_region = get_gov_latest_region(gov_region_info)
        db_latest_region = get_db_latest_region(db)

        added_keys, deleted_keys, modified_keys = diff(db_latest_region, gov_latest_region, is_db_source=True)

        for key in added_keys:
            LOGGER.info(green('+ {}: {}'.format(key, gov_latest_region[key])))

        for key in deleted_keys:
            LOGGER.info(red('- {}: {}'.format(key, db_latest_region[key].name)))

        for key in modified_keys:
            LOGGER.info(yellow('{}{}: {} -> {}'.format('[恢复]' if db_latest_region[key].is_deleted else '', key, db_latest_region[key].name, gov_latest_region[key])))

        LOGGER.info(blue('{} added keys'.format(len(added_keys))))
        LOGGER.info(blue('{} deleted keys'.format(len(deleted_keys))))
        LOGGER.info(blue('{} modified keys'.format(len(modified_keys))))

        return added_keys, deleted_keys, modified_keys, gov_latest_region, gov_region_info

    return check_update()


@script('update')
def update_region(purpose):
    db = lambda: require_database(purpose)

    @transactional(db)
    def update():
        added_codes, deleted_codes, modified_codes, gov_latest_region, gov_region_info = check_region_update(purpose)
        if any(e for e in (added_codes, deleted_codes, modified_codes)):
            LOGGER.info('updating region table')
            LOGGER.info('backup old region table')
            db().execute('DROP TABLE IF EXISTS region_backup')
            db().execute('CREATE TABLE region_backup AS TABLE region')

            add_regions(db, {ac: gov_latest_region[ac] for ac in added_codes})

            db().executemany(
                "UPDATE {REGION_TABLE} SET is_deleted=TRUE WHERE NOT is_deleted AND code=%(code)s".format(REGION_TABLE=REGION_TABLE),
                [DictObject(code=code) for code in deleted_codes]
            )
            db().executemany(
                'UPDATE {REGION_TABLE} SET name=%(name)s, is_deleted=FALSE WHERE code=%(code)s'.format(REGION_TABLE=REGION_TABLE),
                [DictObject(code=code, name=gov_latest_region[code]) for code in modified_codes]
            )
            db().insert(REGION_VERSION_TABLE, due_date=gov_region_info.due_date, published_at=gov_region_info.published_at)
            LOGGER.info('update finished')
        else:
            LOGGER.info('no updates')

    update()


@script('rollback-update')
def rollback_update(purpose):
    db = lambda: require_database(purpose)

    @transactional(db)
    def rollback():
        region_versions = db().list('SELECT * FROM {REGION_VERSION_TABLE} ORDER BY id DESC FETCH FIRST 2 ROWS ONLY'.format(REGION_VERSION_TABLE=REGION_VERSION_TABLE))
        if not region_versions:
            LOGGER.info('can not rollback: can not find region version')
            return
        if db().get_scalar('SELECT COUNT(*) FROM {REGION_BACKUP_TABLE}'.format(REGION_BACKUP_TABLE=REGION_BACKUP_TABLE)) == 0:
            LOGGER.info('can not rollback: no data in backup table')
            return
        LOGGER.info('current region version: published at %(published_at)s, applied_at: %(applied_at)s', {
            'published_at': region_versions[0].published_at, 'applied_at': region_versions[0].applied_at
        })
        if len(region_versions) >= 2:
            LOGGER.info('will rollback to region version: published at %(published_at)s, applied_at: %(applied_at)s', {
                'published_at': region_versions[1].published_at, 'applied_at': region_versions[1].applied_at
            })
        db().execute('''
            UPDATE {REGION_TABLE} r
            SET name=rb.name, level=rb.level, has_child=rb.has_child, parent_code=rb.parent_code, is_deleted=rb.is_deleted
            FROM {REGION_BACKUP_TABLE} rb
            WHERE r.code=rb.code
            '''.format(REGION_TABLE=REGION_TABLE, REGION_BACKUP_TABLE=REGION_BACKUP_TABLE))
        try:
            deleted_count = db().execute('DELETE FROM {REGION_TABLE} WHERE code NOT IN (SELECT code FROM {REGION_BACKUP_TABLE})'.format(REGION_TABLE=REGION_TABLE, REGION_BACKUP_TABLE=REGION_BACKUP_TABLE))
        except Exception as e:
            LOGGER.info('can not delete rows in %(REGION_TABLE)s but not in backup table', {'REGION_TABLE': REGION_TABLE})
            raise
        else:
            if deleted_count > 0:
                LOGGER.info('deleted %(count)s regions', {'count': deleted_count})
        db().execute('DELETE FROM {REGION_BACKUP_TABLE}'.format(REGION_BACKUP_TABLE))
        db().execute('DELETE FROM {REGION_VERSION_TABLE} WHERE id=(SELECT MAX(id) FROM {REGION_VERSION_TABLE})'.format(REGION_VERSION_TABLE=REGION_VERSION_TABLE))
        LOGGER.info('rollback update finished')

    try:
        rollback()
    except Exception as e:
        LOGGER.info('rollback failed')


def get_latest_region(contents):
    contents.find('li.cont_line').remove()
    latest_region = pq(contents.children()[0])
    return DictObject(
        url=latest_region.find('a').attr('href'),
        due_date=date(*(int(e) for e in re.match('.*(\d{4})年(\d{1,2})月(\d{1,2})日.*', latest_region.find('.cont_tit03').text()).groups())),
        published_at=to_date()(latest_region.find('.cont_tit02').text())
    )


def get_gov_latest_region(latest_region):
    region_content = pq(url='{}{}'.format(CONTENTS_URL if 'gov.cn' not in latest_region.url else '', latest_region.url))('.xilan_con').text()
    region_content = region_content[region_content.index('110000'):].split()
    region_content = dict(tuple(region_content[i: i + 2]) for i in range(0, len(region_content), 2))
    return region_content


def get_db_latest_region(db):
    return {r.code: r for r in db().list('SELECT * FROM {REGION_TABLE}'.format(REGION_TABLE=REGION_TABLE))}


def diff(old_data_dict, new_data_dict, is_db_source=False):
    old_codes = set(old_data_dict.keys())
    new_codes = set(new_data_dict.keys())
    added_keys = new_codes - old_codes
    if is_db_source:
        deleted_keys = set(key for key in old_codes - new_codes if not old_data_dict[key].is_deleted)
        modified_keys = set(key for key in old_codes & new_codes if (old_data_dict[key].name, old_data_dict[key].is_deleted) != (new_data_dict[key], False))
    else:
        deleted_keys = old_codes - new_codes
        modified_keys = set(key for key in old_codes & new_codes if old_data_dict[key] != new_data_dict[key])

    return added_keys, deleted_keys, modified_keys


def _wrap_with(code):
    def inner(text, bold=False):
        c = code
        if bold:
            c = '1;{}'.format(c)
        return '\033[{}m{}\033[0m'.format(c, text)

    return inner

red = _wrap_with('31')
green = _wrap_with('32')
yellow = _wrap_with('33')
blue = _wrap_with('34')


def add_regions(db, regions):
        new_regions = []
        for code in regions.keys():
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
        LOGGER.info('%(region_count)s region records will be inserted', {'region_count': len(new_regions)})
        db().insert(REGION_TABLE, new_regions, code=lambda r: r.code, name=lambda r: r.name, level=lambda r: r.level, has_child=False,
            parent_code=lambda r: r.parent_code)
        db().execute('''
            UPDATE {REGION_TABLE} r
            SET has_child=TRUE
            WHERE level=1 AND EXISTS(SELECT 1 FROM {REGION_TABLE} WHERE level=2 AND NOT is_deleted AND parent_code=r.code)
            '''.format(REGION_TABLE=REGION_TABLE))
        db().execute('''
            UPDATE {REGION_TABLE} r
            SET has_child=TRUE
            WHERE level=2 AND EXISTS(SELECT 1 FROM {REGION_TABLE} WHERE level=3 AND NOT is_deleted AND parent_code=r.code)
            '''.format(REGION_TABLE=REGION_TABLE))