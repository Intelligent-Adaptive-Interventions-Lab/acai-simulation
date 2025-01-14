from app import app
from app.chatbot import ask, append_interaction_to_chat_log
from app.forms import ChatForm, BotToBotChatForm
from app.conversation import CustomGPTConversation, GPTConversation, init_prompt


from flask import Flask, request, session, jsonify, render_template, redirect, url_for
from twilio.twiml.messaging_response import MessagingResponse
from datetime import datetime, timezone


import sqlite3


# run_with_ngrok(app)

USER = "Person"
CHATBOT = "AI"
WARNING = "warning"
END = "end"
NOTI = "notification"

conversation = [
    {
        "from": CHATBOT,
        "to": WARNING,
        "message": "The following is a conversation with a therapist. The therapist is helpful, creative, empathetic, and very friendly.",
        "send_time": datetime(2022, 6, 20, 0, 0, 0, tzinfo=timezone.utc)
    }, 
    {
        "from": CHATBOT,
        "to": NOTI,
        "message": "Yesterday",
        "send_time": datetime(2022, 6, 20, 0, 0, 0, tzinfo=timezone.utc)
    }, 
    {
        "from": USER,
        "to": CHATBOT,
        "message": "Hello, who are you?",
        "send_time": datetime(2022, 6, 20, 0, 0, 1, tzinfo=timezone.utc)
    }, 
    {
        "from": CHATBOT,
        "to": USER,
        "message": "I am an AI created by OpenAI. How can I help you today?",
        "send_time": datetime(2022, 6, 20, 0, 1, 0, tzinfo=timezone.utc)
    }, 
    {
        "from": USER,
        "to": CHATBOT,
        "message": "I need help.",
        "send_time": datetime(2022, 6, 20, 0, 2, 0, tzinfo=timezone.utc)
    }, 
    {
        "from": CHATBOT,
        "to": USER,
        "message": "I'm sorry to hear that. What's going on?",
        "send_time": datetime(2022, 6, 20, 0, 3, 0, tzinfo=timezone.utc)
    }, 
    {
        "from": CHATBOT,
        "to": NOTI,
        "message": "Today",
        "send_time": datetime(2022, 6, 20, 0, 4, 0, tzinfo=timezone.utc)
    }, 
    {
        "from": USER,
        "to": CHATBOT,
        "message": "I had an argument with my family today.",
        "send_time": datetime(2022, 6, 20, 0, 4, 0, tzinfo=timezone.utc)
    }, 
    {
        "from": CHATBOT,
        "to": USER,
        "message": "I'm sorry to hear that. Can you tell me more about what happened?",
        "send_time": datetime(2022, 6, 20, 0, 5, 0, tzinfo=timezone.utc)
    }, 
    {
        "from": USER,
        "to": CHATBOT,
        "message": "I told my mom that I want to buy a computer but she was very upset about that.",
        "send_time": datetime(2022, 6, 20, 0, 6, 0, tzinfo=timezone.utc)
    }, 
    {
        "from": CHATBOT,
        "to": USER,
        "message": "I'm sorry to hear that she was upset. Can you tell me more about why you want to buy a computer?",
        "send_time": datetime(2022, 6, 20, 0, 7, 0, tzinfo=timezone.utc)
    }, 
    {
        "from": USER,
        "to": CHATBOT,
        "message": "I told her that I need a computer to complete my assignment.",
        "send_time": datetime(2022, 6, 20, 0, 8, 0, tzinfo=timezone.utc)
    }, 
    {
        "from": CHATBOT,
        "to": USER,
        "message": "I see. And she was upset because she doesn't think you need a computer for that?",
        "send_time": datetime(2022, 6, 20, 0, 9, 0, tzinfo=timezone.utc)
    }, 
    {
        "from": USER,
        "to": CHATBOT,
        "message": "No, she doesn't 😥.",
        "send_time": datetime(2022, 6, 20, 0, 10, 0, tzinfo=timezone.utc)
    }, 
    {
        "from": CHATBOT,
        "to": USER,
        "message": "I'm sorry to hear that. Can you tell me more about your assignment? Maybe there's a way to do it without a computer.",
        "send_time": datetime(2022, 6, 20, 0, 11, 0, tzinfo=timezone.utc)
    }, 
    {
        "from": USER,
        "to": CHATBOT,
        "message": "There is NO WAY to finish that assignment without a computer. Why didn't she understand that??? 😡",
        "send_time": datetime(2022, 6, 20, 0, 12, 0, tzinfo=timezone.utc)
    }, 
    {
        "from": CHATBOT,
        "to": USER,
        "message": "It sounds like you're feeling frustrated because you feel like your mom doesn't understand your needs. Can you tell me more about that?",
        "send_time": datetime(2022, 6, 20, 0, 13, 0, tzinfo=timezone.utc)
    },
    {
        "from": CHATBOT,
        "to": END,
        "message": "This conversation ended by the system.",
        "send_time": datetime(2022, 6, 20, 0, 14, 0, tzinfo=timezone.utc)
    }
]


def _delete_session_variable(variable: str) -> None:
    try:
        del session[variable]
    except KeyError:
        pass

@app.route('/')
def main():
    return render_template("/pages/main.html")


@app.route('/bot_to_bot', methods=['GET', 'POST'])
def bot_to_bot():
    form = BotToBotChatForm(turn="User")

    bot = CustomGPTConversation(
        user="HUMAN", 
        chatbot="AI", 
        chat_log=session.get('bot_chat_log', form.bot_prompt.data),
        prompt=form.bot_prompt.data,
        default_start="I am an AI created by OpenAI. How are you doing today?"
    )
    user = CustomGPTConversation(
        user="HUMAN", 
        chatbot="AI", 
        chat_log=session.get('user_chat_log', form.user_prompt.data),
        prompt=form.user_prompt.data,
        default_start="Hello, who are you?"
    )

    if form.validate_on_submit():
        print("============== START ==============")
        message = form.message.data
        turn = form.turn.data

        # Check current turn of the conversation
        if turn == 'User':
            # USER turn
            # Check if providing message manually
            if message != '':
                # [USER] Add answer (self) message to chat log
                user_chat_log = user.append_interaction_to_chat_log(answer=message)

                # [BOT] Generate message to chat log
                answer = bot.ask(question=message)

                # [BOT] Add message back to chat log
                bot_chat_log = bot.append_interaction_to_chat_log(question=message, answer=answer)
            else:
                # [USER] Get last message for question
                question = user.get_last_message()

                if question == '':
                    # [USER] If no starting message is given, use the default start
                    answer = user.default_start
                else:
                    # [USER] Ask to get answer
                    answer = user.ask()

                # [BOT] Add question (opposite) message to chat log
                bot_chat_log = bot.append_interaction_to_chat_log(question=answer)

                # [USER] Add answer (self) message to chat log
                user_chat_log = user.append_interaction_to_chat_log(answer=answer)

            form.turn.default = 'Bot'
        else:
            # BOT turn
            # Check if providing message manually
            if message != '':
                # [BOT] Add answer (self) message to chat log
                bot_chat_log = bot.append_interaction_to_chat_log(answer=message)

                # [USER] Generate message to chat log
                answer = user.ask(question=message)

                # [USER] Add message back to chat log
                user_chat_log = user.append_interaction_to_chat_log(question=message, answer=answer)
            else:
                # [BOT] Get last message for question
                question = bot.get_last_message()

                if question == '':
                    # [BOT] If no starting message is given, use the default start
                    answer = bot.default_start
                else:
                    # [BOT] Ask to get answer
                    answer = bot.ask()

                # [USER] Add question (opposite) message to chat log
                user_chat_log = user.append_interaction_to_chat_log(question=answer)

                # [BOT] Add answer (self) message to chat log
                bot_chat_log = bot.append_interaction_to_chat_log(answer=answer)

            form.turn.default = 'User'

        # Sync both USER and BOT chat logs
        user.sync_chat_log(user_chat_log)
        bot.sync_chat_log(bot_chat_log)

        # Update Session
        session['user_chat_log'] = user_chat_log
        session['bot_chat_log'] = bot_chat_log
        form.process()

        print("============== END ==============")
        # Render conversation from BOT
        return render_template(
            "/pages/bot_to_bot.html",
            user=bot.get_user(), 
            bot=bot.get_chatbot(), 
            warning=bot.WARNING, 
            end=bot.END,
            notification=bot.NOTI,
            conversation=bot.get_conversation(test=False),
            form=form
        )

    return render_template(
        "/pages/bot_to_bot.html",
        user=bot.get_user(), 
        bot=bot.get_chatbot(), 
        warning=bot.WARNING, 
        end=bot.END,
        notification=bot.NOTI,
        conversation=bot.get_conversation(test=False),
        form=form
    )


@app.route('/conversation', methods=['GET', 'POST'])
def start_conversation():
    chat_log = session.get('chat_log')

    if chat_log is None:
        arm_no = session.get("arm_no")
        if arm_no is None:
            select_prompt = init_prompt(random=True)
        else:
            select_prompt = init_prompt(arm_no=arm_no)
        session["chat_log"] = select_prompt["prompt"] + select_prompt["message_start"]
        session["chatbot"] = select_prompt["chatbot"]
        session["user"] = request.remote_addr
        session["start"] = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

    convo = GPTConversation(session.get("user"), session.get("chatbot"), session.get("chat_log"))

    form = ChatForm()
    if form.validate_on_submit():
        user_message = form.message.data
        answer = convo.ask(user_message)
        chat_log = convo.append_interaction_to_chat_log(user_message, answer)
        session["chat_log"] = chat_log
        sqliteConnection = None
        try:
            sqliteConnection = sqlite3.connect('/var/www/html/acaidb/database.db')
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")

            sqlite_insert_query = """INSERT INTO chats
                                  (user_id, chat_log) 
                                   VALUES 
                                  (?,?);"""
            param_tuple = (session["user"],session["chat_log"])
            count = cursor.execute(sqlite_insert_query,param_tuple)
            sqliteConnection.commit()
            print("Record inserted successfully into SqliteDb_developers table ", cursor.rowcount)
            cursor.close()

        except sqlite3.Error as error:
            print("Failed to insert data into sqlite table", error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
                print("The SQLite connection is closed")
        
        return redirect(url_for('start_conversation'))
    
    return render_template(
        '/pages/convo.html', 
        user=convo.get_user(), 
        bot=convo.get_chatbot(), 
        warning=convo.WARNING, 
        end=convo.END,
        notification=convo.NOTI,
        conversation=convo.get_conversation(test=True),
        form=form
    )

@app.route('/qualtrics', methods=['GET', 'POST'])
def start_qualtrics_conversation():
    chat_log = session.get('chat_log')
    if chat_log is None:
        arm_no = session.get("arm_no")
        if arm_no is None:
            select_prompt = init_prompt(random=True)
        else:
            select_prompt = init_prompt(arm_no=arm_no)
        session["chat_log"] = select_prompt["prompt"] + select_prompt["message_start"]
        session["chatbot"] = select_prompt["chatbot"]
        session["user"] = request.remote_addr
        session["start"] = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

    convo = GPTConversation(session.get("user"), session.get("chatbot"), session.get("chat_log"))

    start = session.get('start')
    if start is None:
        session["start"] = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

    stop = session.get('stop')
    if stop is None:
        session["stop"] = 5*60

    now = datetime.now()
    difference = now - datetime.strptime(session.get('start'), "%m/%d/%Y, %H:%M:%S")
    difference_seconds = difference.total_seconds()

    end = session.get('end')
    if end is None or not end:
        session["end"] = (difference_seconds >= session.get('stop'))

    form = ChatForm()
    if form.validate_on_submit() and not session.get('end'):
        user_message = form.message.data
        answer = convo.ask(user_message)
        chat_log = convo.append_interaction_to_chat_log(user_message, answer)

        session['chat_log'] = chat_log
        sqliteConnection = None
        try:
            sqliteConnection = sqlite3.connect('/var/www/html/acaidb/database.db')
            cursor = sqliteConnection.cursor()
            print("Successfully Connected to SQLite")

            sqlite_insert_query = """INSERT INTO chats
                                  (user_id, chat_log) 
                                   VALUES 
                                  (?,?);"""
            param_tuple = (session["user"],session["chat_log"])
            count = cursor.execute(sqlite_insert_query,param_tuple)
            sqliteConnection.commit()
            print("Record inserted successfully into SqliteDb_developers table ", cursor.rowcount)
            cursor.close()

        except sqlite3.Error as error:
            print("Failed to insert data into sqlite table", error)
        finally:
            if sqliteConnection:
                sqliteConnection.close()
                print("The SQLite connection is closed")

        return redirect(url_for('start_qualtrics_conversation'))

    return render_template(
        '/dialogue/qualtrics_card.html', 
        user=convo.get_user(), 
        bot=convo.get_chatbot(), 
        warning=convo.WARNING, 
        end=convo.END,
        notification=convo.NOTI,
        conversation=convo.get_conversation(end=session.get('end')),
        form=form
    )


@app.route('/chatsms', methods=['POST'])
def chatsms():
    incoming_msg = request.values['Body']
    chat_log = session.get('chat_log')
    answer = ask(incoming_msg, chat_log)

    session['chat_log'] = append_interaction_to_chat_log(incoming_msg, answer,chat_log)

    msg = MessagingResponse()
    msg.message(answer)

    return str(msg)


@app.route('/chatweb', methods=['POST'])
def chatweb():
    input_json = request.get_json(force=True) 
    incoming_msg = str(input_json['response'])
    chat_log = session.get('chat_log')
    answer = ask(incoming_msg, chat_log)
    session['chat_log'] = append_interaction_to_chat_log(incoming_msg, answer, chat_log)

    dictToReturn = {
        "answer": answer,
        "chat_log": session['chat_log']
    }
    return jsonify(dictToReturn)

@app.route('/clear', methods=['GET'])
def clear_session():
    delete_variables = ['chat_log', 'start', 'end', 'arm_no', 'bot_chat_log', 'user_chat_log']
    for variable in delete_variables:
        _delete_session_variable(variable)

    return "cleared!"


@app.route('/end', methods=['GET'])
def end():
    session['end'] = True
    return "ended!"


@app.route('/arm', methods=['GET'])
def select_arm():
    args = request.args
    location = int(args['location'])
    if location == 12345:
        arm_no = 0
    elif location == 23456:
        arm_no = 1
    elif location == 34567:
        arm_no = 2
    elif location == 45678:
        arm_no = 3
    elif location == 56789:
        arm_no = 4
    elif location == 67891:
        arm_no = 5
    elif location == 78910:
        arm_no = 6
    elif location == 89101:
        arm_no = 7
    elif location == 91011:
        arm_no = 8
    elif location == 10111:
        arm_no = 9
    elif location == 11121:
        arm_no = 10
    elif location == 12131:
        arm_no = 11
    elif location == 13141:
        arm_no = 12
    elif location == 14151:
        arm_no = 13
    elif location == 15161:
        arm_no = 14
    elif location == 16171:
        arm_no = 15
    elif location == 17181:
        arm_no = 16
    elif location == 18192:
        arm_no = 16
    session['arm_no'] = arm_no
    return redirect(url_for('start_qualtrics_conversation'))
