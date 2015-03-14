PyICQt supports different settings for every user. You can change them via Ad-Hoc menu (most jabber clients can do it)

### Statistics for PyICQt menu ###
You can see statistics for transport here
  * Online Users
  * Incoming Messages
  * Uptime
  * Total Sessions
  * Max Concurrent Sessions
  * Outgoing Messages

### Set x-status menu ###
You can choose x-status and fill details for it using this menu
Choosing is 2-steps process:
  1. Selection x-status name from list
  1. Entering text for x-status title and description
List of x-status names contains not only predefined statuses for English version of official ICQ client, but also statuses from other localizations. Some clients do not support all these x-statuses, thereby minor statuses (from Angry to Typing) more preferred than major (all other)

### Settings menu ###
This menu contains several categories

**Contact list settings**

  * Show temporary ICQ contacts in roster
When you delete contact from your ICQ contact list, it not deleted really, but marked as deleted and become 'temporary' contact. It's ICQ server feature to improve speed as I think (you may delete contact by mistake and restore it after some time - all this time contact is 'cached' in your contact list). Users wouldn't see these contacts usually, but it may be useful when contact-list on server is corrupted or user manually deletes all contacts from his own list and wants to restore them back.
Number of temporary contacts is usually much more than number of real contacts (it is 141 vs 54 for me) and getting them from server can take a long time.
If you enable this feature, you must re-login in PyICQt to apply changes.
If you enable and disable this feature without re-login, PyICQt will not erase temporary contacts from your roster and you must delete them manually or re-register in PyICQt

  * Deny all authorization requests
Don't send subscription messages from ICQ contacts to jabber-client. This option useful for spam protection. All users requested authorization will receive 'Request denied' answer.


**X-status settings**

_NOTE:_ administrator of PyICQt may disable x-status support for all users
  * Away messages sending
Send status messages when your status is 'away', 'n/a', or 'busy'. Sending of status messages in 'online' or 'free for chat' stats isn't supported (and it's ICQ issue).
  * Away messages receiving
When this option is enabled, you can see your contacts status messages (_away_ messages).
  * X-status sending mode.
If this option is enabled, your contacts can see your x-status message.
If this option is disabled, you can't set your own x-status.
Value of the option is mode sending (like _ICQ 5.1_, _ICQ 6_ or combination).
After changing of mode you should re-login into transport
  * Restore latest x-status after disconnect
When you don't want change x-status long time, you can pick this option, and your latest x-status will automatically set after connecting to ICQ network.
  * X-status receiving mode
If this option is enabled, you can receive x-status messages from your contacts (if client of contact supports x-statuses).
If value changed to 'None', option works immediately. In other cases you will see x-status messages from contacts as soon as they change their states.
Value is one of _ICQ 5.1_, _ICQ 6_ and _ICQ 5.1+6_ (check ExtendedStatus page for full information about these modes)
  * Allow status icons between 5.1 and 6
When you selected 5.1 or 6 in previous option, you can't see x-status information from clients, which use other mode. With this option enabled you can see x-status name (icon) for these contacts.
  * Display status icon as personal event
That's possibility to see x-status icons for contacts. Jabber-client with PEP support is required, and it should be able to display PEP event as icon.

_NOTE:_ Icons for all activities (60+) aren't created yet, and it's impossible see icons for all x-statuses now.
  * Try to display status text as personal event
Very funny option :) Your contact can put name of mood or activity in x-status title and you will see PEP icon for this name. Currently, it works only when _ICQ 6_ or _ICQ 5.1+6_ mode of x-status receiving is enabled.
  * Display status icon for transport (some client only)
As least Gajim can draw PEP icons in roster for all contacts, including transports. Option uses this feature for displaying your own icon (i.e. icon for your x-status name).

**Message settings**

  * utf-8 messages sending mode
Send messages in utf-8 when:

...contact supports utf-8 messages (_Always_)

...contact really uses utf-8 (_As reply on incoming utf-8 message_)

...never (_Sending disabled_)

  * Confirmations sending mode
Send confirmations on incoming messages when:

...contact can receive them (_Always_)

...contact uses modern ICQ client (_Only for utf-8 messages_)

...never (_Sending disabled_)

  * Confirmations receiving
Sends requests for messages confirmations. It's works when your jabber-client can send such requests (Bombus, for example) and contact's client can response on requests.

  * Encoding for outgoing offline messages
Send offline messages encoded in:

... _local_ one-byte encoding, specified in config

... _Unicode_

... In depends on remote client features (_auto detect_)


**Personal events settings**

PyICQt tries to represent ICQ x-status for contacts as PEP event (you can read more about it at ExtendedStatus page) and uses for this aim 3 things: mood, activity and tune.
Unfortunately, not all jabber-clients understand these things, and you can choose only some things, which are supported by your client.
Most of clients supports moods and tune, support of activity isn't ready yet in most cases (seems only Gajim, Jabbim and Tkabber can display this in stable version, Miranda — only in unstable builds)

  * User mood receiving

  * User activity receiving

  * User tune receiving

Clients supports personal events since versions:
| Client | Mood | Activity | Tune |
|:-------|:-----|:---------|:-----|
| Psi    | 0.11| -      | 0.11 |
| Gajim  | 0.12| 0.12 | 0.12 |
| Jabbim | 0.4 | 0.4  | 0.4 |
| Tkabber | 0.11.0 | 0.11.0 | 0.11.0 |
| Coccinella | 0.95.14 | 0.96.2 | - |
| Miranda IM | 0.7.0.27 | 0.8.0.18 | 0.7.0.36 |
| Bombus | 0.7.1358 | - |  0.7.1358 |

_NOTE:_ It's global settings for user. If you are connected to PyICQt with two and more resources, option apply for all them