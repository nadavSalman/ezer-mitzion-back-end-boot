#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=W0613, C0116
"""
This telegram bot can:
    -listen to any message on the "Ezer Metzion" groups and log them.
    -Send messages to specifig group.
    the bot uses the official telegram api and some python modules.
    for mor information about the modules look at requirements.txt
"""
import urllib
import requests
import os
import os.path
import pathlib
from os import path
import logging
import threading
from threading import Thread
import time
#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=W0613, C0116
"""
This telegram bot can:
    -listen to any message on the "Ezer Metzion" groups and log them.
    -Send messages to specifig group.
    the bot uses the official telegram api and some python modules.
    for mor information about the modules look at requirements.txt
"""
import urllib
import requests
import os
import os.path
import pathlib
from os import path
import logging
import threading
from threading import Thread
import time
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import re
import datetime



from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext


#Firestore
cred = credentials.Certificate("./ezer-b3f5c-firebase-adminsdk-jmqib-79a7795ad6.json")
firebase_admin.initialize_app(cred)
db = firestore.client()



# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

logger = logging.getLogger(__name__)

def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    update.message.reply_text('Hi!')


def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')

# Check for new messages to send
def checkOut():
    threading.Timer(3, checkOut).start()
    docs = db.collection('messages-out').get()
    for doc in docs:
        if (doc == None):
            pass
        else:
            sendMassage(doc)
            db.collection(u'messages-out').document(doc.id).delete()
            break


def get_grp(name):
    group_docs = firestore.client().collection(u'Groups').get()
    for doc in group_docs:
        doc = doc.to_dict()
        if(doc['name']==name):
            GID = doc['GID']
            return GID

# Send new message to specific chat
def sendMassage(doc):
    doc = doc.to_dict()
    grp = str(doc["group"])
    chat_id = str(get_grp(grp))
    mission = doc["mission"]
    mission = u"\U0001F4CD" + " "+"קריאה מספר:"+str(doc['call_id'])+"\n"+u'\U0001F697'+' '+"מ{}".format(doc['from'])+' '+'ל{}'.format(doc['to'])+'\n'+mission
    print(mission)
    mission = str(urllib.parse.quote(mission.encode('utf-8')))
    bot_token = '<<<SECRET>>>'
    send_text = 'https://api.telegram.org/bot' + str(bot_token) + '/sendMessage?chat_id=' + str(chat_id) + '&parse_mode=markdown&text=' + mission
    response = requests.get(send_text)
    print(response.json())
    return response.json()


# Listen and log any user masseges.
def listen(update: Update, context: CallbackContext) -> None:
    time = (datetime.datetime.now().strftime("%x"))
    new_update = update.message.to_dict()
    isbot = new_update['from']['is_bot']
    if(isbot != True):
        grp = str(update.message.chat_id)
        user = str(update.message.from_user)
        user = re.search(' (.+?),' , user)
        user = user.group(1)
        msg = update.message.text
        msg.encode("utf-8")
        user_docs = db.collection(u'Users').where(u'UID', u'==', user).get()
        for doc in user_docs:
            doc = doc.to_dict()
            user = doc['name']
        group_docs = db.collection(u'Groups').where(u'GID', u'==', grp).get()
        for doc in group_docs:
            doc = doc.to_dict()
            grp = doc['name']
        classification = msgClassification(msg)
        src = classification[2]
        dst = classification[3]
        call_id = int(re.findall('\d+', msg)[0])
        print (user)
        if(classification[0] == '1'):
            addDataMission(grp,user,msg,src,dst,time,call_id)
        elif (classification[0] == '0'):
            addDataResponse(grp,user,call_id)
        else:
            pass

def addDataMission(grp,user,msg,src,dst,time,call_id):
    doc_ref = db.collection(u'messages')
    doc_ref.add({
    u'group': grp,
    u'state': u'false',
    u'sender': user,
    u'accepter': u'-',
    u'from': src,
    u'to': dst,
    u'mission': msg,
    u'time':time,
    u'call_id':call_id
})

def addDataResponse(grp,user,call_id):
    doc_ref = db.collection(u'messages').where(u'time', u'==', datetime.datetime.now().strftime("%x")).get()
    for doc in doc_ref:
        doc_id = doc.id
        doc = doc.to_dict()
        if(doc['group'] == grp and doc['call_id'] == call_id):
            db.collection("messages").document(doc_id).update({
            u'state': True,
            u'accepter': user,})

#Message classification - 
#   if the message is a mission - return '1' in index 0 of array
#   else if its an acceptence return '0' in index 0 of array
#   else its a regular message and index 0 = '2'
#   indexes:
#       [0] = mission or not
#       [1] = call id
#       [2] = from
#       [3] = to
#       [4] = msg content
def msgClassification (msg):
    classification = list()
    if (len(msg) > 70 and re.search(r'\d', msg)):
        classification.append("1")
        classification.append(None)
    elif (len(msg) < 70 and re.search(r'\d', msg)):
        classification.append("0")
        classification.append(re.search(r'\d',msg))
    else:
        classification.append("2")
        classification.append(None)
    classification.append(None)
    classification.append(None)
    classification.append(msg)
    if (classification[0]=='1'):
        citys = ["ירושלים","תל אביב-יפו","חיפה","ראשון לציון","פתח תקווה","אשדוד","נתניה","באר שבע","בני ברק","חולון","רמת גן","אשקלון","רחובות","בת ים","בית שמש","כפר סבא","הרצליה","חדרה","מודיעין- מכבים- רעות","נצרת","לוד","רמלה","רעננה","מודיעין עילית","רהט","הוד השרון","גבעתיים","קריית אתא","נהריה","ביתר עילית","אום אל-פחם","קריית גת","אילת","ראש העין","עפולה","נס ציונה","עכו","אלעד","רמת השרון","כרמיאל","יבנה","טבריה","טייבה","קריית מוצקין","שפרעם","נוף הגליל","קריית ים","קריית ביאליק","קריית אונו","מעלה אדומים","אור יהודה","צפת","נתיבות","דימונה","טמרה","סח'נין","יהוד-מונוסון","באקה אל-גרבייה","אופקים","גבעת שמואל","טירה","ערד","מגדל העמק","שדרות","עראבה","נשר","קריית שמונה","יקנעם עילית","כפר קאסם","כפר יונה","קלנסווה","קריית מלאכי","מעלות- תרשיחא","טירת כרמל","אריאל","אור עקיבא","בית שאן"]
        citiesFrom = ["ירושלים","מתל אביב-יפו","מחיפה","מראשון לציון","מפתח תקווה","מאשדוד","מנתניה","מבאר שבע","מבני ברק","מחולון","מרמת גן","מאשקלון","מרחובות","מבת ים","מבית שמש","מכפר סבא","מהרצליה","מחדרה","ממודיעין- מכבים- רעות","מנצרת","מלוד","מרמלה","מרעננה","ממודיעין עילית","מרהט","מהוד השרון","מגבעתיים","מקריית אתא","מנהריה","מביתר עילית","מאום אל-פחם","מקריית גת","מאילת","מראש העין","מעפולה","מנס ציונה","מעכו","מאלעד","מרמת השרון","מכרמיאל","מיבנה","מטבריה","מטייבה","מקריית מוצקין","משפרעם","מנוף הגליל","מקריית ים","מקריית ביאליק","מקריית אונו","ממעלה אדומים","מאור יהודה","מצפת","מנתיבות","מדימונה","מטמרה","מסח'נין","מיהוד-מונוסון","מבאקה אל-גרבייה","מאופקים","מגבעת שמואל","מטירה","מערד","ממגדל העמק","משדרות","מעראבה","מנשר","מקריית שמונה","מיקנעם עילית","מכפר קאסם","מכפר יונה","מקלנסווה","מקריית מלאכי","ממעלות- תרשיחא","מטירת כרמל","מאריאל","מאור עקיבא","מבית שאן"]
        citiesTo = ["ירושלים","לתל אביב-יפו","לחיפה","לראשון לציון","לפתח תקווה","לאשדוד","לנתניה","לבאר שבע","לבני ברק","לחולון","לרמת גן","לאשקלון","לרחובות","לבת ים","לבית שמש","לכפר סבא","להרצליה","לחדרה","למודיעין- מכבים- רעות","לנצרת","ללוד","לרמלה","לרעננה","למודיעין עילית","לרהט","להוד השרון","לגבעתיים","לקריית אתא","לנהריה","לביתר עילית","לאום אל-פחם","לקריית גת","לאילת","לראש העין","לעפולה","לנס ציונה","לעכו","לאלעד","לרמת השרון","לכרמיאל","ליבנה","לטבריה","לטייבה","לקריית מוצקין","לשפרעם","לנוף הגליל","לקריית ים","לקריית ביאליק","לקריית אונו","למעלה אדומים","לאור יהודה","לצפת","לנתיבות","לדימונה","לטמרה","לסח'נין","ליהוד-מונוסון","לבאקה אל-גרבייה","לאופקים","לגבעת שמואל","לטירה","לערד","למגדל העמק","לשדרות","לעראבה","לנשר","לקריית שמונה","ליקנעם עילית","לכפר קאסם","לכפר יונה","לקלנסווה","לקריית מלאכי","למעלות- תרשיחא","לטירת כרמל","לאריאל","לאור עקיבא","לבית שאן"]
        for src in citiesFrom:
            if src in msg:
                classification[2] = src
        for destination in citiesTo:
            if destination in msg:
                classification[3] = destination
    return classification

def on_snapshot(col_snapshot, changes, read_time):
    print(u'Callback received query snapshot.')
    print(u'Current cities in California:')
    for doc in col_snapshot:
        print(f'{doc.id}')
    callback_done.set()

#main
def main():
    #Sender
    callback_done = threading.Event()
    Thread(target = checkOut).start()
    #Listener
    updater = Updater("<<<SECRET>>>", use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(MessageHandler(Filters.text, listen))
    # Start the Bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()