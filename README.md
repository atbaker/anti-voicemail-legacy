# Anti-Voicemail

A voicemail app for people who really, really don't like receiving voicemails

## Deploy now

Deploy on Heroku instantly:

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/atbaker/anti-voicemail)

## Carrier voicemail codes

- Verizon: *71 + national format number (reset - *73)
    - name: "Verizon Wireless"
    - Details: http://www.verizonwireless.com/mobile-living/tech-smarts/verizon-call-forwarding/
- AT&T: Dial *92, enter a forwarding number, then press #. (reset - Dial *93#.)
    - name: "AT&T Wireless"
- Sprint: *73 (reset - *730)
    - name: "Sprint Spectrum, L.P."
- T-Mobile:
    - name: "T-Mobile USA, Inc."

## To-do

- Maybe use forms even though we're accepting data from Twilio
- Nicer template for listening to voicemail (+ download link)
- Write tests
- Set up CI
- Dockerize?
- Fix up README
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
