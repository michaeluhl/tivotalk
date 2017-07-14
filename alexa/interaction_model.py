{
    "schema": {
        "intents": [
            {
                "intent": "AMAZON.CancelIntent"
            },
            {
                "intent": "AMAZON.HelpIntent"
            },
            {
                "intent": "AMAZON.StopIntent"
            },
            {
                "slots": [
                    {
                        "name": "RECORDING_DATE",
                        "type": "AMAZON.DATE"
                    }
                ],
                "intent": "WhatsOnIntent",
                "utterances": [
                    "<What is|What's> on <{RECORDING_DATE}|>",
                    "<What is|What's> on <your|the> to do list <{RECORDING_DATE}|>",
                    "<What is|What's> going to record <{RECORDING_DATE}|>"
                ]
            },
            {
                "slots": [
                    {
                        "name": "MOVIE_TITLE",
                        "type": "AMAZON.Movie"
                    },
                    {
                        "name": "TV_TITLE",
                        "type": "AMAZON.TVSeries"
                    }
                ],
                "intent": "TellAboutIntent",
                "utterances": [
                    "Tell me about <{MOVIE_TITLE}|{TV_TITLE}>"
                ]
            },
            {
                "intent": "PauseIntent",
                "utterances": [
                    "<Pause|Stop|Halt|Wait>"
                ]
            },
            {
                "intent": "ResumeIntent",
                "utterances": [
                    "<Resume|Play|Continue|Go|Unpause>"
                ]
            },
            {
                "intent": "AdvanceIntent",
                "utterances": [
                    "<Advance|Skip|Skip ahead>"
                ]
            }
        ]
    }
}
