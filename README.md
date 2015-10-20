# anti-voicemail
A voicemail app for people who really, really don't like receiving voicemails

## To-do

QR CODES THAT ARE GIFS! GIFS THAT ARE QR CODES?!?! The world will never be the same.
- `brew install zbar` - +1 reason for Dockerizing this thing
http://stackoverflow.com/questions/24688802/saving-an-animated-gif-in-pillow
http://stackoverflow.com/questions/15144483/compositing-two-images-with-python-wand
http://www.graphicsmagick.org/programming.html


- Config image import
- Prevent config image abuse - make sure that it's coming from the Mailbox number if it exists
- Refactor onboarding
- Maybe use forms even though we're accepting data from Twilio
- Integrate QR code into setup workflow
- Put a Gather in before non-mobile numbers are allowed to leave a voicemail
- Write tests
- Maybe restructure views.py
- Nicer template for listening to voicemail

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
