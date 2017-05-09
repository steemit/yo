# coding=utf-8
import logging
import os

import sqlalchemy as sa

from storage import metadata

log_level = getattr(logging, os.environ.get('LOG_LEVEL', 'INFO'))
logging.basicConfig(level=log_level)
logger = logging.getLogger('__name__')




# mirror of https://github.com/steemit/condenser/blob/master/db/models/identity.js
'''
var Identity = sequelize.define('Identity', {
        UserId: {
            type: DataTypes.INTEGER,
            references: {
                model: 'users',
                key: 'id'
            },
            field: 'user_id'
        },
        provider: DataTypes.STRING,
        provider_user_id: {type: DataTypes.STRING},
        name: DataTypes.STRING,
        email: {type: DataTypes.STRING},
        phone: {type: DataTypes.STRING(32)},
        confirmation_code: {type: DataTypes.STRING, unique: true},
        verified: DataTypes.BOOLEAN,
        score: DataTypes.INTEGER
    }, {
        tableName: 'identities',
        createdAt   : 'created_at',
        updatedAt   : 'updated_at',
        timestamps  : true,
        underscored : true,
        classMethods: {
            associate: function (models) {
                Identity.belongsTo(models.User, {
                    onDelete: "CASCADE",
                    foreignKey: {
                        allowNull: false
                    }
                });
            }
        }
    });
'''
identities_table = sa.Table('yo_identities', metadata,
    sa.Column('user_id', sa.Integer, primary_key=True),
    sa.Column('provider', sa.Unicode),
sa.Column('provider_user_id', sa.Unicode),
sa.Column('name', sa.Unicode),
sa.Column('email', sa.Unicode),
sa.Column('phone', sa.Unicode),
sa.Column('confirmation_code', sa.Unicode, unique=True),
sa.Column('verified', sa.Boolean),
sa.Column('score', sa.Integer),
sa.Column('created_at', sa.DateTime),
sa.Column('updated_at', sa.DateTime)
)
