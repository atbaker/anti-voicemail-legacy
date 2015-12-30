# Anti-voicemail

[![Build Status](https://travis-ci.org/atbaker/anti-voicemail.svg?branch=master)](https://travis-ci.org/atbaker/anti-voicemail)
[![Coverage Status](https://coveralls.io/repos/atbaker/anti-voicemail/badge.svg?branch=master&service=github)](https://coveralls.io/github/atbaker/anti-voicemail?branch=master)

A voicemail app for people who really, really don't like receiving voicemails.

**Try it yourself:** Call the demo number at
[+1 (202) 499-7699](tel:+12024997699). (Your phone number will not be recorded.)

Using [Twilio](https://www.twilio.com/), Anti-voicemail actively dissuades
callers from leaving you voicemail by:

- Sending callers from mobile phones a text message with your contact info
- Requiring callers from non-mobile phones to press a button before leaving a voicemail

In the unfortunate event you *do* receive a voicemail, Anti-voicemail will
send you a text message with a transcription of the voicemail so you don't have
to listen to it.

Anti-voicemail also has a few other handy features. You can:

- Listen to and download voicemail recordings (loathing optional)
- Add phone numbers to a whitelist of callers who are always allowed to leave
you voicemail
- Save your Anti-Voicemail configuration in your phone in case you need to set
it up again

After you deploy Anti-voicemail, you will complete the setup process.

## Deploy it now

Deploy on Heroku instantly:

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/atbaker/anti-voicemail)

**(more instructions coming soon)**
