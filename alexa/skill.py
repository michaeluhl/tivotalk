"""
This sample demonstrates a simple skill built with the Amazon Alexa Skills Kit.
The Intent Schema, Custom Slots, and Sample Utterances for this skill, as well
as testing instructions are located at http://amzn.to/1LzFrj6

For additional samples, visit the Alexa Skills Kit Getting Started guide at
http://amzn.to/1LGWsLG
"""

import os
from pubcom import Communicator


PUBKEY = os.environ['TT_PUBKEY']
SUBKEY = os.environ['TT_SUBKEY']
CLIENT_ID = os.environ['TT_CLIENT_ID']

# --------------- Helpers that build all of the responses ----------------------


def sequence_to_oxford_string(l):
    if len(l) > 2:
        return ', '.join([str(i) for i in l[:-1]]) + ", and " + str(l[-1])
    elif len(l) == 2:
        return ' and '.join([str(i) for i in l])
    elif len(l) > 0:
        return str(l[0])


def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': "SessionSpeechlet - " + title,
            'content': "SessionSpeechlet - " + output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }


# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """

    session_attributes = {}
    card_title = "Welcome"
    speech_output = "Welcome to TiVo Talk. " \
                    "Please tell me what you'd like to know, by saying, " \
                    "what's on, or when is Game of Throwns on?"
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "Please tell me what you'd like to know, by saying, " \
                    "what's on, or when is Big Bang Theory on?"
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "Thank you for using TiVo Talk.  " \
                    "Have a nice day! "
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))


def whats_on_intent(intent, session):
    """Queries the TiVo to find out what its going to record.
    """

    card_title = intent['name']
    session_attributes = {}
    should_end_session = True

    recording_time = 'PRESENT_REF'
    if 'RECORDING_TIME' in intent['slots'] and 'value' in intent['slots']['RECORDING_TIME']:
        recording_time = intent['slots']['RECORDING_TIME']['value']
        if recording_time == "":
            recording_time = 'PRESENT_REF'

    com = Communicator(pub_key=PUBKEY, sub_key=SUBKEY, client_id=CLIENT_ID)
    com.connect()
    msg = {'cmd': 'WHATSON',
           'rec_time': recording_time}
    com.connected.wait(timeout=1.0)
    com.publish(msg)
    resp = com.wait_for_message(timeout=3.0).message
    if resp['cmd'] == 'WHATSON' and resp['status'] == 'SUCCESS':
        count = resp['total_count']
        recordings = []
        while True:
            recordings.extend(resp['recordings'])
            if len(recordings) >= count:
                break
            resp = com.wait_for_message(timeout=3.0).message
        speech_output = "I'm recording the following items: " + \
                        sequence_to_oxford_string(recordings)
        reprompt_text = None
    else:
        speech_output = "An error occured processing your request.  " + \
                        "Please state your request again."
        reprompt_text = "Please state your request again."
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "WhatsOnIntent":
        return whats_on_intent(intent, session)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here


# --------------- Main handler ------------------

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    if (event['session']['application']['applicationId'] !=
            "amzn1.ask.skill.d1811372-04a5-4907-8794-929ccce2f416"):
        raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])
