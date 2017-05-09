# coding=utf-8
import logging
import os

import sqlalchemy as sa

from storage import metadata

log_level = getattr(logging, os.environ.get('LOG_LEVEL', 'INFO'))
logging.basicConfig(level=log_level)
logger = logging.getLogger('__name__')







# mirror of https://github.com/steemit/condenser/blob/master/db/models/users.js
'''
var User = sequelize.define('User', {
        name: DataTypes.STRING,
        email: {type: DataTypes.STRING},
        uid: {type: DataTypes.STRING(64)},
        first_name: DataTypes.STRING,
        last_name: DataTypes.STRING,
        birthday: DataTypes.DATE,
        gender: DataTypes.STRING(8),
        picture_small: DataTypes.STRING,
        picture_large: DataTypes.STRING,
        location_id: DataTypes.BIGINT.UNSIGNED,
        location_name: DataTypes.STRING,
        locale: DataTypes.STRING(12),
        timezone: DataTypes.INTEGER,
        remote_ip: DataTypes.STRING,
        verified: DataTypes.BOOLEAN,
        waiting_list: DataTypes.BOOLEAN,
        bot: DataTypes.BOOLEAN,
        sign_up_meta: DataTypes.TEXT,
        account_status: DataTypes.STRING
    }, {
        tableName: 'users',
        createdAt   : 'created_at',
        updatedAt   : 'updated_at',
        timestamps  : true,
        underscored : true,
        classMethods: {
            associate: function (models) {
                User.hasMany(models.Identity);
                User.hasMany(models.Account);
            }
        }
    });
'''

users_table = sa.Table('yo_users', metadata,
sa.Column('user_id', sa.Integer, primary_key=True), # uid in sequelize model
sa.Column('name', sa.Unicode),
sa.Column('email', sa.Unicode),

sa.Column('first_name', sa.Unicode),
sa.Column('last_name', sa.Unicode),
sa.Column('birthday', sa.Date),
sa.Column('gender', sa.Unicode),
sa.Column('picture_small', sa.Unicode),
sa.Column('picture_large', sa.Unicode),
sa.Column('location_id', sa.Integer),
sa.Column('location_name', sa.Unicode),
sa.Column('locale', sa.Unicode),
sa.Column('timezone', sa.Unicode),
sa.Column('remote_ip', sa.Unicode),
sa.Column('verified', sa.Boolean),
sa.Column('waiting_list', sa.Boolean),
sa.Column('bot', sa.Boolean),
sa.Column('signup_meta', sa.UnicodeText),
sa.Column('account_status', sa.Unicode),


sa.Column('created_at', sa.DateTime),
sa.Column('updated_at', sa.DateTime)
                       )