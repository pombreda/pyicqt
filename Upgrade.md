## 0.8 -> 0.8.1 ##

If you use MySQL as XDB backend, after upgrade you will get exception `"Table 'pyicqt.csettings' doesn't exist"`. Reason - some tables were added and used in new version.
Necessary manually create these tables.
_tools/db-setup.mysql_ file contains required commands. You should run mysql client and execute script like:
```
mysql --host=localhost --user=pyicqt --password=pyicqt pyicqt
mysql> \. db-setup.mysql
```

New variables in config:
| usemd5auth | Enable/disable md5 (secure) authentification. Very recommended for use |
|:-----------|:-----------------------------------------------------------------------|
| enableShutdownMessage | Possibility send message to all users of transport when it stopping |
| customShutdownMessage | Custom text, which should be sent |
| xstatusessupport | x-status support |
| transportWebsite | Website, where user can get information about transport |
| supportRoom | Local jabber room, where user can discuss questions about using of transport |
| supportJid | JID of transport's admin or other person, who can help to user |

## 0.8.1 -> 0.8.1.1 ##

Possibilities for unicode detection introduced in 0.8.1.1 provides better possibilities for offline messages interpretation.

Variable in config:
| detectunicode | detection level (0 - detection disabled, 1 - in offline messages, 2 - in offline messages and nicknames) |
|:--------------|:---------------------------------------------------------------------------------------------------------|