# anti-voicemail
A voicemail app for people who really, really don't like receiving voicemails

## To-do

- Add carrier voicemail code to final setup step
- Investigate using TwiML <Message> vs. REST API message
- Maybe use forms even though we're accepting data from Twilio
- Put a Gather in before non-mobile numbers are allowed to leave a voicemail
- Write tests
- QR code SQLite dump
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