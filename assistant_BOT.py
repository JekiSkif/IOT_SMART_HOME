import time
from speech import *
import data_acquisition as da
from init import *
import pandas as pd
from pocketsphinx import LiveSpeech  # Live speech recognition
from icecream import ic as icA
from datetime import datetime
import os.path
from os import path


# Define time format for logging
def time_format():
    return f'{datetime.now()}  Assistant BOT|> '


# Configure icecream logging output with custom time format and disable file context
icA.configureOutput(prefix=time_format)
icA.configureOutput(includeContext=False)

# Define the main BOT class with business logic
class BOT():

    # Business logic handler method
    def bl(self, pl, st, ts):
        icA('Hello friend, how can I help you?')  # Log a greeting message

        # Play greeting message or generate and play if the file does not exist
        if path.exists('Hello friend.wav'):
            pl.play('Hello friend.wav')
        else:
            ts.save2file(ts.tts_request('Hello friend, how can I help you?'), ttsfile)
            pl.play(ttsfile)

        time.sleep(sys_delay)  # Pause for the defined system delay
        rep_pl = 0  # Initialize repeat count

        # Main loop for interacting with the user
        while True:
            pl.record(userresponcefile)  # Record user response
            time.sleep(sys_delay)
            try:
                # Recognize and transcribe the recorded user response
                userresponcestring = st.recognize(st.opensoundfile(userresponcefile)).results[0].alternatives[
                    0].transcript
            except:
                userresponcestring = ''
            icA(userresponcestring)  # Log user response
            time.sleep(sys_delay)

            # Handle empty response with retries
            if len(userresponcestring) == 0:
                icA('Sorry, could you repeat, please?')
                if path.exists('Sorry.wav'):
                    pl.play('Sorry.wav')
                else:
                    ts.save2file(ts.tts_request('Sorry, could you repeat, please?'), ttsfile)
                    pl.play(ttsfile)
                time.sleep(sys_delay)
                rep_pl += 1
                if rep_pl == 3:  # Break loop after 3 retries
                    break
                continue

            # Check for exit command
            if 'stop it' in userresponcestring:
                icA('Ok, goodbye my friend')
                if path.exists('Goodbye.wav'):
                    pl.play("Goodbye.wav")
                else:
                    ts.save2file(ts.tts_request('Goodbye my friend'), ttsfile)
                    pl.play(ttsfile)
                time.sleep(sys_delay)
                return

            # Check for home status request
            if "home status" in userresponcestring:
                icA('Data request..')
                ts.save2file(ts.tts_request('All systems are in normal state. Would you like to listen to the report?'),
                             ttsfile)
                time.sleep(sys_delay)
                pl.play(ttsfile)
                time.sleep(sys_delay)

                # Record response to the status report offer
                pl.record(userresponcefile)
                time.sleep(sys_delay)
                try:
                    userresponcestring = st.recognize(st.opensoundfile(userresponcefile)).results[0].alternatives[
                        0].transcript
                except:
                    userresponcestring = ''
                icA(userresponcestring)

                # Process response to the status report offer
                if "yes" in userresponcestring:
                    # Fetch and process data from data acquisition module
                    dfW = da.fetch_data(db_name, 'data', 'SensitivityMeter').value
                    W_report = str((pd.to_numeric(dfW, errors='ignore', downcast='float')).mean()) if len(
                        dfW) > 0 else 'currently unavailable'

                    dfE = da.fetch_data(db_name, 'data', 'ElectricityMeter').value
                    E_report = str((pd.to_numeric(dfE, errors='ignore', downcast='float')).mean()) if len(
                        dfE) > 0 else 'currently unavailable'

                    # Create report message
                    text_msg = f'The current home state: electricity average consumption is {E_report} kiloWatt per hour and operated under normal condition, Sensitivity average consumption is {W_report} cubic meters per hour and it is usual to current season'
                    ts.save2file(ts.tts_request(text_msg), ttsfile)
                    time.sleep(sys_delay)
                    pl.play(ttsfile)
                    time.sleep(sys_delay)

                    # Ask if user needs further assistance
                    icA('Something else?')
                    if path.exists("something else.wav"):
                        pl.play("something else.wav")
                    else:
                        ts.save2file(ts.tts_request('Something else ?'), ttsfile)
                        pl.play(ttsfile)
                    time.sleep(sys_delay)
                    pl.record(userresponcefile)
                    time.sleep(sys_delay)
                    try:
                        userresponcestring = st.recognize(st.opensoundfile(userresponcefile)).results[0].alternatives[
                            0].transcript
                    except:
                        userresponcestring = ''
                    icA(userresponcestring)
                    if 'yes' in userresponcestring:
                        continue
                    elif 'no' in userresponcestring:
                        icA('Ok, goodbye my friend')
                        if path.exists("Goodbye.wav"):
                            pl.play("Goodbye.wav")
                        else:
                            ts.save2file(ts.tts_request('Ok, goodbye my friend'), ttsfile)
                            pl.play(ttsfile)
                        time.sleep(sys_delay)
                        return
                    else:
                        continue
                else:
                    # Handle when user doesn't want the report
                    icA('Something else?')
                    pl.play("something else.wav")
                    time.sleep(sys_delay)
                    pl.record(userresponcefile)
                    time.sleep(sys_delay)
                    try:
                        userresponcestring = st.recognize(st.opensoundfile(userresponcefile)).results[0].alternatives[
                            0].transcript
                    except:
                        userresponcestring = ''
                    icA(userresponcestring)
                    if 'yes' in userresponcestring:
                        icA('What else can I do to help you?')
                        pl.play("What_else.wav")
                        time.sleep(sys_delay)
                        continue
                    elif 'no' in userresponcestring:
                        icA('Ok, goodbye my friend')
                        pl.play("Goodbye.wav")
                        time.sleep(sys_delay)
                        return
                    else:
                        continue

            # Similar logic applies for other commands like "room temperature" and "Sensitivity Volume"
            # Each case fetches or updates data, responds with voice messages, and handles follow-up questions

            # Default continue if no recognized command
            else:
                continue


# Main entry point of the script
if __name__ == '__main__':
    pl = Player()  # Initialize Player for playing audio
    st = STT()  # Initialize Speech-to-Text engine
    ts = TTS()  # Initialize Text-to-Speech engine

    bot = BOT()  # Create instance of the BOT class
    keyphrase = 'house'  # Define activation keyphrase
    icA('BOT started..')  # Log BOT start
    speech = LiveSpeech(lm=False, keyphrase=keyphrase, kws_threshold=1e-20)  # Initialize live speech listener

    # Continuous loop waiting for activation keyphrase
    while 1:
        for phrase in speech:
            icA(phrase)
            if keyphrase in phrase.segments(detailed=True)[0][0]:
                bot.bl(pl, st, ts)  # Trigger the business logic handler when keyphrase is detected
                icA('Ending current business logic iteration')
                break
