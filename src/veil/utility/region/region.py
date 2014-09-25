# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
import logging
import re
from datetime import date
from pyquery import PyQuery as pq
from veil_component import red, green, yellow, blue
from veil.frontend.cli import *
from veil.model.collection import *
from veil.model.binding import *
from veil.backend.database.client import *


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

        latest_gov_region_version = extract_gov_latest_region_version(pq(url=CONTENTS_URL)('ul.center_list_contlist'))
        LOGGER.info('latest gov region version: %(latest_gov_region_version)s', {'latest_gov_region_version': latest_gov_region_version})

        add_regions(db, get_gov_latest_region(latest_gov_region_version))

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
        gov_latest_region_version = extract_gov_latest_region_version(pq(url=CONTENTS_URL)('ul.center_list_contlist'))
        if gov_latest_region_version.due_date <= latest_db_region_version.due_date or gov_latest_region_version.published_at <= latest_db_region_version.published_at:
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
        gov_latest_region = get_gov_latest_region(gov_latest_region_version)
        db_latest_region = get_db_latest_region(purpose)

        added_codes, deleted_codes, modified_codes = diff(db_latest_region, gov_latest_region)

        for code in added_codes:
            print(green('+ {}: {}'.format(code, gov_latest_region[code])))

        for code in deleted_codes:
            print(red('- {}: {}'.format(code, db_latest_region[code].name)))

        for code in modified_codes:
            if db_latest_region[code].deleted:
                print(yellow('[恢复]{}: {} -> {}'.format(code, db_latest_region[code].name, gov_latest_region[code])))
            else:
                print(yellow('{}: {} -> {}'.format(code, db_latest_region[code].name, gov_latest_region[code])))

        print(blue('{} added keys'.format(len(added_codes))))
        print(blue('{} deleted keys'.format(len(deleted_codes))))
        print(blue('{} modified keys'.format(len(modified_codes))))

        return added_codes, deleted_codes, modified_codes, gov_latest_region, gov_latest_region_version

    return check_update()


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
            LOGGER.info('update finished')
        else:
            LOGGER.info('no updates')

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


def get_gov_latest_region(latest_region_version):
    region_content = pq(url='{}{}'.format(CONTENTS_URL if 'gov.cn' not in latest_region_version.url else '', latest_region_version.url))('.xilan_con').text()
    region_content = region_content[region_content.index('110000'):].split()
    region_content = dict(tuple(region_content[i: i + 2]) for i in range(0, len(region_content), 2))
    return region_content


def get_db_latest_region(purpose):
    db = lambda: require_database(purpose)
    return {r.code: r for r in db().list('SELECT * FROM {REGION_TABLE}'.format(REGION_TABLE=REGION_TABLE))}


def diff(db_source, site_source):
    db_codes = set(db_source)
    site_codes = set(site_source)
    added_codes = site_codes - db_codes
    deleted_codes = set(code for code in db_codes - site_codes if not db_source[code].deleted)
    modified_codes = set(code for code in db_codes & site_codes if (db_source[code].name, db_source[code].deleted) != (site_source[code], False))

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
        db().insert(REGION_TABLE, new_regions, code=lambda r: r.code, name=lambda r: r.name, level=lambda r: r.level, has_child=False,
            parent_code=lambda r: r.parent_code)
        db().execute('''
            UPDATE {REGION_TABLE} r
            SET has_child=TRUE
            WHERE level=1 AND EXISTS(SELECT 1 FROM {REGION_TABLE} WHERE level=2 AND NOT deleted AND parent_code=r.code)
            '''.format(REGION_TABLE=REGION_TABLE))
        db().execute('''
            UPDATE {REGION_TABLE} r
            SET has_child=TRUE
            WHERE level=2 AND EXISTS(SELECT 1 FROM {REGION_TABLE} WHERE level=3 AND NOT deleted AND parent_code=r.code)
            '''.format(REGION_TABLE=REGION_TABLE))