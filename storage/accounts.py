# coding=utf-8
import logging
import os

import sqlalchemy as sa

from storage import metadata

log_level = getattr(logging, os.environ.get('LOG_LEVEL', 'INFO'))
logging.basicConfig(level=log_level)
logger = logging.getLogger('__name__')


# mirror of https://github.com/steemit/condenser/blob/master/db/models/account.js
'''
var Account = sequelize.define('Account', {
        UserId: {
            type: DataTypes.INTEGER,
            references: {
                model: 'users',
                key: 'id'
            },
            field: 'user_id'
        },
        name: {type: DataTypes.STRING, unique: true},
        owner_key: {type: DataTypes.STRING, unique: true},
        active_key: {type: DataTypes.STRING, unique: true},
        posting_key: {type: DataTypes.STRING, unique: true},
        memo_key: {type: DataTypes.STRING, unique: true},
        referrer: DataTypes.STRING,
        refcode: DataTypes.STRING,
        remote_ip: DataTypes.STRING,
        ignored: {type: DataTypes.BOOLEAN},
        created: {type: DataTypes.BOOLEAN}
    }, {
        tableName: 'accounts',
        createdAt   : 'created_at',
        updatedAt   : 'updated_at',
        timestamps  : true,
        underscored : true,
        classMethods: {
            associate: function (models) {
                Account.belongsTo(models.User, {
                    onDelete: "CASCADE",
                    foreignKey: {
                        allowNull: false
                    }
                });
            }
        }
    });
'''
accounts_table = sa.Table('yo_accounts', metadata,
 sa.Column('user_id', sa.Integer, primary_key=True),

sa.Column('name', sa.Unicode),
sa.Column('owner_key', sa.Unicode),
sa.Column('active_key', sa.Unicode),
sa.Column('posting_key', sa.Unicode),
sa.Column('memo_key', sa.Unicode),
sa.Column('referrer', sa.Unicode),
sa.Column('refcode', sa.Unicode),
sa.Column('remote_ip', sa.Unicode),
sa.Column('ignored', sa.Boolean),
sa.Column('created_at', sa.DateTime),
sa.Column('updated_at', sa.DateTime)
)