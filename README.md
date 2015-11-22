# Anti-Voicemail

[![Build Status](https://travis-ci.org/atbaker/anti-voicemail.svg?branch=master)](https://travis-ci.org/atbaker/anti-voicemail)
[![Coverage Status](https://coveralls.io/repos/atbaker/anti-voicemail/badge.svg?branch=master&service=github)](https://coveralls.io/github/atbaker/anti-voicemail?branch=master)

A voicemail app for people who really, really don't like receiving voicemails.

## Deploy now

Deploy on Heroku instantly:

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/atbaker/anti-voicemail)

## Carrier voicemail codes

- Verizon: *71 + national format number (reset - *73)
    - name: "Verizon Wireless"
    - Details: http://www.verizonwireless.com/mobile-living/tech-smarts/verizon-call-forwarding/
- AT&T: Dial *004*<phone number>#, enter a forwarding number, then press #. (reset - Dial *93#.) (Helen)
    - name: "AT&T Wireless"
    - disable: ##004#
    - details: https://productforums.google.com/forum/#!topic/voice/XJt1i0rlm7A
- Sprint: *28 (reset - *38)
    - name: "Sprint Spectrum, L.P."
    - details: https://community.sprint.com/baw/message/492672
- T-Mobile: *004*[Phone Number]# (Thomas)
    - name: "T-Mobile USA, Inc."
    - disable: ##004#
    - details: https://productforums.google.com/forum/#!topic/voice/wTlShFC2hDA

## To-do

- Docker automated build
- Fix up README (start with outline)
    - Clean up README itself
    - Write instructions for getting started
    - Write instructions on how to add your carrier
- Tag release
- Add CONTRIBUTING
- Fill out sample issues
- PEP8 this biz

Maybe:
    - Ask for pronoun preference in setup?

Follow ups:
    - Time zone - Just use browser to get it programatically

DONE:

    - Model for Mailbox stored locally in SQLite
    - SMS-based setup workflow
    - Add carrier voicemail code to final setup step
    - Investigate using TwiML <Message> vs. REST API message
    - QR code SQLite dump
    - Add config image to TwimL responses
    - Config image import
    - See if we can remove PHONE_NUMBER from environment variables
    - Validate email field using WTF
    - Automatically configure callbacks to ease setup
    - Add note about how callback URLs are already set up
    - Put a Gather in before non-mobile numbers are allowed to leave a voicemail
    - Refactor into smaller apps
    - Prevent config image abuse - make sure that it's coming from the Mailbox number if it exists
    - Refactor onboarding
    - Add step asking about QR Codes to make UX better
    - Make help menu (kept it simple)
    - ADD AN EASTER EGG
    - Take out email notifications
    - Write tests
    - Write MOAR tests
    - Bug when calling Helen's phone from Google (lookup failed)
    - Set up CI
    - Change /import-config view to a helper method
    - Add more delay on the QR code question
    - Tweak Easter egg to only display on test run
    - Add note about unsupported carrier
    - 100% ALL THE WAY BABY
    - Change fallback URL to static S3 buckets that I maintain
    - Nicer template for listening to voicemail (+ download link)
    - Try it with a Trial Account - works for messing around - but not recommended
    - Dockerize!
    - Figure out how reliable 'ForwardedFrom' is (Carrier-specific, unfortunately)
    - Experiment with different <Say> voices
    - Possible bug that doesn't remember whether you like or hate QR codes
    - Whitelist
    - Maybe break command part into separate method
    - Rename templates to have more managable naming convention
    - Flatten migrations
    - Verify Twilio requests
    - Register anti-voicemail.com
    - Get HTTP scheme reflected in auto-setup util
    - Enum for love/hate?
    - Eliminate need for ForwardedFrom
    - Set up demo server
