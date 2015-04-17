# -*- coding: utf-8 -*-
db = DAL('sqlite://storage.db', migrate=True, lazy_tables=True)
from datetime import datetime


'''
db.define_table('map_object',
                Field('id', 'string', required=True),
                Field('polyline', 'long'),
                Field('summary_polyline', 'string'),
                format='%(id)s'
                )
'''

db.define_table('segment',
                Field('id', 'integer'),
                Field('distance', 'float'),
                Field('name', 'string'),
                Field('activity_type', 'string'),
                Field('average_grade', 'float'),
                Field('maximum_grade', 'float'),
                Field('elevation_high', 'float'),
                Field('elevation_low', 'float'),
                Field('climb_category', 'integer'),
                Field('city', 'string'),
                Field('state', 'string'),
                Field('country', 'string'),
                #Field('map_object', 'reference map_object'),
                format='%(name)s'
                )
db.segment.activity_type.requires = IS_IN_SET(['Ride','Run'])
db.segment.climb_category.requires = IS_IN_SET([0,1,2,3,4,5])

db.define_table('activity',
                Field('id', 'integer'),
                Field('user_id', 'integer'),
                Field('name', 'string'),
                Field('description', 'string'),
                Field('distance', 'float'),
                Field('moving_time', 'integer'),
                Field('elapsed_time', 'integer'),
                Field('total_elevation_gain', 'float'),
                Field('type', 'string'),
                Field('start_date', 'datetime'),
                Field('location_city', 'string'),
                Field('location_state', 'string'),
                Field('location_country', 'string'),
                Field('achievement_count', 'integer'),
                Field('average_speed', 'float'),
                Field('max_speed', 'float'),
                #Field('map_object', 'reference map_object'),
                format='%(name)s %(start_date)s %(description)s'
                )
db.activity.type.requires = IS_IN_SET(['Ride','Run'])

db.define_table('segment_effort',
                Field('user_id', 'integer'),
                Field('elapsed_time', 'integer'),
                Field('moving_time', 'integer'),
                Field('start_date', 'datetime'),
                Field('distance', 'float'),
                Field('activity', 'reference activity'),
                Field('segment', 'reference segment'),
                format='%(segment_name)s: %(start_date)s'
                )
