# Anti-Voicemail

A voicemail app for people who really, really don't like receiving voicemails

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

- Nicer template for listening to voicemail (+ download link)
- 100% ALL THE WAY BABY
- Change /import-config view to a helper method
- Add more delay on the QR code question
- Bug when calling Helen's phone from Google (lookup failed)
- SENDING MESSAGES BASED ON \n's??!?!?!?
- Experiment with different <Say> voices
- Send text message to user on error
- Add note about unsupported carrier
- Try it with a Trial Account
- Tweak Easter egg to only display on test run
- Figure out how reliable 'ForwardedFrom' is
- Experiment with different voices
- Possible bug that doesn't remember whether you like or hate QR codes
- Set up CI
- Dockerize?
- Fix up README
    - Clean up README itself
    - Write instructions for getting started
    - Write instructions on how to add your carrier
- Add CONTRIBUTING
- Fill out sample issues

Maybe:
    - Ask for pronoun preference in setup?

Follow ups:
    - Time zone - Just use browser to get it programatically

- Multi-tenant:
    - Calling Twilio Number directly: Remember a previous call

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
