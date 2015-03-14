### Presets ###
PyICQt supports several presets for x-statuses support.
These presets is:
  * ICQ 5.1 mode is classic x-statuses mode. It is supported by most ICQ clients. 35 different icons for x-statuses are available (including "heart"). Some clients can supports only bare minimum - 24 icons. Sending and receiving takes a lot of traffic.
  * ICQ 6 mode is modern mode for latest version of official client. It takes small amount off traffic, but iconset contains only 24 icons
  * ICQ 5.1+6 mode is mixed one. Maximum of compatibility and maximum of traffic. Part of contacts can see 24 icons (as ICQ6), other part - 35 icons (as ICQ5.1)
PyICQt also supports option for smoothing differences between old and new modes: you can see icon for clients with other mode, but can't see status message.


### Compatibility in different modes ###
ICQ clients uses different ways for sending/receiving of x-statuses. Part of them listed in table:
| PyICQt 		| Miranda | qutIM | R&Q | Jimm |
|:---------|:--------|:------|:----|:-----|
| ICQ5.1 		|   +/+   |  **/+**| -/+ | +/+  |
| ICQ5.1 smooth 	|   +/+   |  **/+**| -/+ | +/+  |
| ICQ6   		|   -/x   |  +/x  | +/+ | -/x  |
| ICQ6 smooth 		|   x/x   |  +/x  | +/+ | x/x  |
| ICQ5.1+6 		|   +/+   |  +/+  | +/+ | +/+  |
How read this table? Sample: symbols x/+ in cell at intersection of PyICQt(5.1) and qutIM describes what PyICQt in ICQ5.1 mode can see status icons from qutIM, and qutIM can see icon and status message from PyICQt.

### X-statuses table ###
Some x-status icons are different in different clients. Here is list of equivalents:
| ICQ 5.1 (loc) | ICQ 6 | Miranda | qutIM | R&Q | QIP Infium | Jimm | PyICQt |
|:--------------|:------|:--------|:------|:----|:-----------|:-----|:-------|
| Angry | Angry | Angry | Angry | Angry | Angry | Angry | Angry |
| Taking a bath | Taking a bath | Taking a bath | Taking a bath | Duck | Duck | Taking a bath | Taking a bath |
| Tired | Tired | Tired | Tired | Tired | Tired | Tired |  Tired |
| Party | Party | Party | Party | Party | Party | Party | Party |
| Drinking beer | Drinking beer | Drinking beer | Drinking beer | Beer | Beer | Drinking beer | Drinking beer |
| Thinking | Thinking | Thinking | Thinking | Thinking | Thinking | Thinking | Thinking |
| Eating | Eating | Eating | Eating | Eating | Eating | Eating | Eating |
| Watching TV | Watching TV | Watching TV | Watching TV | TV | TV | Watching TV | Watching TV |
| Meeting | Meeting | Meeting | Meeting | Friends | Friends | Friends | Meeting |
| Coffee | Coffee | Coffee | Coffee | Coffee | Coffee | Coffee | Coffee |
| Listening to music | Listening to music | Listening to music | Listening to music | Music | Music | Listening to music | Listening to music |
| Business | Business | Business | Business | Business | Business | Business | Business |
| Shooting | Shooting | Shooting | Shooting | Camera | Camera | Shooting | Shooting |
| Having fun | Having fun | Having fun | Having fun | Funny | Funny | Having fun | Having fun |
| On the phone | On the phone | On the phone | On the phone | Phone | Phone | Phone | On the phone |
| Gaming | Gaming | Gaming | Gaming | Games | Games | Gaming | Gaming |
| Studying | Studying | Studying | Studying | College | College | Studying | Studying |
| Shopping | Shopping | Shopping | Shopping | Shopping | Shopping | Shopping | Shopping |
| Feeling sick | Feeling sick | Feeling sick | Feeling sick | Sick | Sick | Feeling sick | Feeling sick |
| Sleeping | Sleeping | Sleeping | Sleeping | Sleeping | Sleeping | Sleeping | Sleeping |
| Surfing | Surfing | Surfing | Surfing | Surfing | Surfing | Surfing | Surfing |
| Browsing | Browsing | Browsing | Browsing | Internet | @ | Browsing | Browsing |
| Working | Working | Working | Working | Engineering | Engineering | Working | Working |
| Typing | Typing | Typing | Typing | Typing | Typing | Typing | Typing |
| Eating...yummy.. (cn) | - | Picnic | Picnic | - | China1 | Picnic | Picnic |
| Having fun (cn) | - | Cooking | ? | - | China2 | Ppc | Happy |
| Chit chatting (cn) | - | Mobile | ? | - | China3 | Mobile | Chit chatting |
| Sleeping (cn) | - | I'm high | ? | - | China4 | Falling asleep | I'm high |
| I'm MOOVing (cn) | - | On WC | On WC | - | China5 | On WC | I'm mooving |
| To be or not to be (de) | - | To be or not to be | To be or not to be | - | De1 | Question | To be or not to be |
| Watching on TV (de) | - | Watching pro7 on TV | PRO 7 | - | De2 | Way | Watching a movie |
| Love (de) | - | Love | Love | - | De3 | Heart | Love |
| Searhing (ru) | - | Searching | ? | - | RuSearch | Search | Searching |
| Love (ru) | - | Love | - | - | RuLove | - | Flirt |
| Journal (ru) | - | Journal | ? | - | RuJournal | Journal | Blogging |
| - | - | Smoking | - | Smoking | - | Cigarette | - |
| - | - | Sex | - | Sex | - | Sex | - |

**Loc** in ICQ 5.1 column notes what status emerged in non-english localization of ICQ client

### X-statuses mapping ###
Of course, jabber don't supports ICQ x-statuses. And it's impossible to show x-status icon directly in roster of jabber client. Therefore PyICQt uses _mapping_: x-status icon is represented as one of such jabber's abilities as:
  * mood
  * activity
  * tune

| X-status | Mood | Activity | Tune |
|:---------|:-----|:---------|:-----|
| Angry | Angry | - | - |
| Taking a bath | - | Grooming: Taking a bath | - |
| Tired | Stressed | - | - |
| Party | - | Relaxing: Partying | - |
| Drinking beer | - | Drinking: Having a beer | - |
| Thinking | Serious | - | - |
| Eating | - | Eating | - |
| Watching TV | - | Relaxing: Watching TV | - |
| Meeting | - | Relaxing: Socializing | - |
| Coffee | - | Drinking: Having a coffee | - |
| Listening to music | - | - | Tune |
| Business | - | Having appointment | - |
| Shooting | - | Traveling: Commuting | - |
| Having fun | Contented | - | - |
| On the phone | - | Talking: On the phone | - |
| Gaming | - | Relaxing: Gaming | - |
| Studying | - | Working: Studying | - |
| Shopping | - | Relaxing: Shopping | - |
| Feeling sick | Sick | - | - |
| Sleeping | - | Inactive: Sleeping | - |
| Surfing | - | Exercising: Swimming | - |
| Browsing | - | Relaxing: Reading | - |
| Working | - | Working | - |
| Typing | - | Working: Writing | - |
| Picnic | - | Relaxing: Going out | - |
| Happy | Happy | - | - |
| Chit chatting | - | Talking: In real life | - |
| I'm high | - | Inactive: Hanging out | - |
| I'm mooving | - | Excited | - |
| To be or not to be | - | Amazed | - |
| Watching a movie | - | Relaxing: Watching a movie | - |
| Love | In love | - | - |
| Searching | Curious | - | - |
| Flirt | Flirtatious | - | - |
| Blogging | Impressed | - | - |

You should use modern jabber client for full representation.