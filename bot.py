import telebot, random
import sqlite3 as sq
from telebot import types
from token import TOKEN

#Настройка бота
bot = telebot.TeleBot(TOKEN)

#Создание таблиц
con = sq.connect('quizbot.db')
cur = con.cursor()

#cur.execute("""DROP TABLE IF EXISTS users""")
#cur.execute("""DROP TABLE IF EXISTS quiz""")
#cur.execute("""DROP TABLE IF EXISTS userquiz""")
#cur.execute("""DROP TABLE IF EXISTS userresults""")

cur.execute("""CREATE TABLE IF NOT EXISTS users (
	tgID INTEGER,
	name TEXT,
	age INTEGER,
	rate INTEGER,
	opinion TEXT
)""")
cur.execute("""CREATE TABLE IF NOT EXISTS quiz (
	tgID INTEGER,
	quizUniqueID TEXT,
	quizQuestionID INTEGER,
	quizQuestionText TEXT,
	quizAnswers TEXT
)""")
cur.execute("""CREATE TABLE IF NOT EXISTS userquiz (
	tgID INTEGER,
	quizUniqueID TEXT,
	quizName TEXT,
	quizDescription TEXT
)""")
cur.execute("""CREATE TABLE IF NOT EXISTS userresults (
	tgID INTEGER,
	quizUniqueID TEXT,
	quizQuestion TEXT,
	questionResult TEXT
)""")

con.commit()
con.close()

#Reply клавиатура
Menu = types.ReplyKeyboardMarkup(resize_keyboard=True)  # Меню старт
buttonHelp = types.KeyboardButton('Помощь')
buttonQuiz = types.KeyboardButton('Квизы')
buttonProfile = types.KeyboardButton('Профиль')
buttonInfo = types.KeyboardButton('Инфо')
buttonFeedback = types.KeyboardButton('Обратная связь')
Menu.add(buttonQuiz, buttonProfile, buttonInfo, buttonHelp, buttonFeedback)

#Старт
@bot.message_handler(commands=['start'])
def startCMD(message):
	print('[QuizBot][bot] >> выполнил /start пользователем [{}]'.format(message.chat.id))
	con = sq.connect('quizbot.db')
	cur = con.cursor()
	cur.execute("SELECT tgID FROM users WHERE tgID = (?)", [message.chat.id])
	tgID = cur.fetchone()
	if tgID is None:
		print('[QuizBot][SQLite3] >> Добавлен новый пользователь - {}'.format(message.chat.id))
		cur.execute("INSERT INTO users (tgID) VALUES (?);", [message.chat.id])
		con.commit()
		con.close()
		askName = bot.send_message(message.chat.id, 'Привет! Как мне к вам обращаться?')
		bot.register_next_step_handler(askName, askname)
	else:
		bot.send_message(message.chat.id, 'Клавиатура обновлена!', reply_markup=Menu)
		con.commit()
		con.close()

#Спрашиваем имя
def askname(message):
	con = sq.connect('quizbot.db')
	cur = con.cursor()
	cur.execute("UPDATE users SET name = :Name WHERE tgID = :TgID", {'Name': message.text, 'TgID': message.chat.id})
	askAge = bot.send_message(message.chat.id, 'Отлично, так и запишем - <b>{}</b>. \nТак же, для сбора статистики мы хотим узнать ваш возраст, просто напишите его.'.format(message.text), parse_mode='HTML')
	bot.register_next_step_handler(askAge, askage)
	con.commit()
	con.close()

#Спрашиваем возраст
def askage(message):
	if message.text.isdigit() and int(message.text) > 0:
		con = sq.connect('quizbot.db')
		cur = con.cursor()
		cur.execute("UPDATE users SET age = :Age WHERE tgID = :TgID", {'Age': message.text, 'TgID': message.chat.id})
		bot.send_message(message.chat.id, 'Спасибо, мы записали. \nТеперь можно пользоваться ботом. \n\n<i>Изменить имя и возраст можно в меню редактирования профиля.</i>', reply_markup=Menu, parse_mode='HTML')
		con.commit()
		con.close()
	else:
		repeat = bot.send_message(message.chat.id, 'Введите <b>число</b> от 0 до <i>бесконечности</i>.', parse_mode='HTML')
		bot.register_next_step_handler(repeat, askage)

#Помощь
@bot.message_handler(commands=['help'])
def helpCMD(message):
	bot.send_message(message.chat.id, '<i>[Помощь]</i>\n\n<i>- /start - обновление клавиатуры\n- /help - список доступных команд \n- /profile - твой профиль и настройки\n- /quizmenu - меню квизов\n- /info - информация о боте\n- /feedback - обратная связь</i>',parse_mode='HTML')

#Настройки профиля
@bot.message_handler(commands=['profile'])
def profile(message):
	profileMenu = types.InlineKeyboardMarkup()
	buttonEditName = types.InlineKeyboardButton('[Изменить имя]', callback_data='changeName')
	buttonEditAge = types.InlineKeyboardButton('[Изменить возраст]', callback_data='changeAge')
	buttonEditClose = types.InlineKeyboardButton('[Закрыть]', callback_data='changeClose')
	profileMenu.add(buttonEditName, buttonEditAge).add(buttonEditClose)
	con = sq.connect('quizbot.db')
	cur = con.cursor()
	cur.execute("SELECT name FROM users WHERE tgID = (?)", [message.chat.id])
	name = cur.fetchone()
	cur.execute("SELECT age FROM users WHERE tgID = (?)", [message.chat.id])
	age = cur.fetchone()
	bot.send_message(message.chat.id, '<i>[Профиль]</i>\n\nИмя - <b>{}</b>\nВозраст - <b>{}</b>'.format(name[0], age[0]), reply_markup=profileMenu, parse_mode='HTML')
	con.commit()
	con.close()

#Callback от profileMenu
@bot.callback_query_handler(func=lambda call: call.data.startswith('change'))
def profileMenu(call):
	if call.message:
		if call.data == 'changeName':
			bot.delete_message(call.message.chat.id, call.message.message_id)
			ansName = bot.send_message(call.message.chat.id, 'Напишите новое имя.')
			bot.register_next_step_handler(ansName, ansname)
		elif call.data == 'changeAge':
			bot.delete_message(call.message.chat.id, call.message.message_id)
			ansAge = bot.send_message(call.message.chat.id, 'Напишите новый возраст.')
			bot.register_next_step_handler(ansAge, ansage)
		elif call.data == 'changeClose':
			bot.delete_message(call.message.chat.id, call.message.message_id)

#Меняем имя пользователя
def ansname(message):
	con = sq.connect('quizbot.db')
	cur = con.cursor()
	cur.execute("UPDATE users SET name = :Name WHERE tgID = :TgID", {'Name': message.text, 'TgID': message.chat.id})
	bot.send_message(message.chat.id, 'Установлено новое имя - {}.'.format(message.text))
	con.commit()
	con.close()
	profile(message)

#Меняем возраст пользователя
def ansage(message):
	if message.text.isdigit() and int(message.text) > 0:
		con = sq.connect('quizbot.db')
		cur = con.cursor()
		cur.execute("UPDATE users SET age = :Age WHERE tgID = :TgID", {'Age': message.text, 'TgID': message.chat.id})
		bot.send_message(message.chat.id, 'Установлен новый возраст - {}.'.format(message.text))
		con.commit()
		con.close()
		profile(message)
	else:
		repeat = bot.send_message(message.chat.id, 'Введите <b>число</b> от 0 до <i>бесконечности</i>.', parse_mode='HTML')
		bot.register_next_step_handler(repeat, ansage)

#Создание тестов
@bot.message_handler(commands=['quizmenu'])
def createQuiz(message):
	createMenu = types.InlineKeyboardMarkup(row_width=2)
	buttonCreateQuiz = types.InlineKeyboardButton('[Новый квиз]', callback_data='createMenuCreate')
	buttonJoinQuiz = types.InlineKeyboardButton('[Ввести код]', callback_data='createMenuJoin')
	buttonQuizData = types.InlineKeyboardButton('[Список ваших квизов]', callback_data='createMenuList')
	createMenu.add(buttonJoinQuiz, buttonCreateQuiz, buttonQuizData)
	con = sq.connect('quizbot.db')
	cur = con.cursor()
	cur.execute("SELECT name FROM users WHERE tgID = (?)", [message.chat.id])
	name = cur.fetchone()
	bot.send_message(message.chat.id, '<i>[Меню квизов]</i>\n\n<b>Привет, {}!</b> \nЭто меню квизов. \nЗдесь вы сможете создать новый квиз, пройти доступный квиз или посмотреть список своих квизов и людей, которые его прошли.'.format(name[0]), reply_markup=createMenu, parse_mode='HTML')
	con.commit()
	con.close()

#Callback от меню квизов
@bot.callback_query_handler(func=lambda call: call.data.startswith('createMenu'))
def createMenu(call):
	if call.message:
		if call.data == 'createMenuCreate':
			bot.delete_message(call.message.chat.id, call.message.message_id)
			quizName = bot.send_message(call.message.chat.id, 'Введите название нового квиза.')
			bot.register_next_step_handler(quizName, quizname)
		elif call.data == 'createMenuJoin':
			bot.delete_message(call.message.chat.id, call.message.message_id)
			askCode = bot.send_message(call.message.chat.id, 'Введите код')
			bot.register_next_step_handler(askCode, quizShow)
		elif call.data == 'createMenuGo':
			bot.delete_message(call.message.chat.id, call.message.message_id)
			quizGetData(call.message)
		elif call.data == 'createMenuBack':
			bot.delete_message(call.message.chat.id, call.message.message_id)
			createQuiz(call.message)
		elif call.data == 'createMenuList':
			bot.delete_message(call.message.chat.id, call.message.message_id)
			generateList(call.message)

def generateList(message):
	con = sq.connect('quizbot.db')
	cur = con.cursor()
	cur.execute("SELECT quizUniqueID, quizName FROM userquiz WHERE tgID = (?)", [message.chat.id])
	Quizzes = cur.fetchall()
	ListMenu = types.InlineKeyboardMarkup()
	for i in range(len(Quizzes)):
		ListMenu.add(types.InlineKeyboardButton(text=Quizzes[i][1], callback_data='generatedList{}'.format(str(Quizzes[i][0]))), types.InlineKeyboardButton('❌', callback_data='generatedDeleteList{}'.format(Quizzes[i][0])))
	ListMenu.add(types.InlineKeyboardButton('[Назад]', callback_data='generatedBackList'))
	bot.send_message(message.chat.id, '<i>[Список ваших квизов]</i>\n\nНажмите на название вашего квиза чтобы посомтреть список людей, которые его прошли.\nТак же вы можете удалить результаты пользователя, нажав на красный крестик рядом с его именем.', reply_markup=ListMenu, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data.startswith('generated'))
def listmenu(call):
	if call.message:
		con = sq.connect('quizbot.db')
		cur = con.cursor()
		if call.data.startswith('generatedDeleteList'):
			bot.delete_message(call.message.chat.id, call.message.message_id)
			quizUID = call.data.split('generatedDeleteList')[1]
			AreYouReally = types.InlineKeyboardMarkup()
			AreYouReally.add(types.InlineKeyboardButton('[Да]', callback_data='generatedYesList{}'.format(quizUID)), types.InlineKeyboardButton('[Нет]', callback_data='generatedNoList'))
			cur.execute("SELECT quizName FROM userquiz WHERE quizUniqueID = (?)", [quizUID])
			QuizName = cur.fetchone()
			bot.send_message(call.message.chat.id, 'Удалить квиз <b>{}</b> [{}]?\n\nВы уверены?'.format(QuizName[0], quizUID), reply_markup=AreYouReally, parse_mode='HTML')
		elif call.data.startswith('generatedYesList'):
			bot.delete_message(call.message.chat.id, call.message.message_id)
			quizUID = call.data.split('generatedYesList')[1]
			cur.execute("SELECT quizName FROM userquiz WHERE quizUniqueID = (?)", [quizUID])
			QuizName = cur.fetchone()
			cur.execute("DELETE FROM userquiz WHERE quizUniqueID = (?)", [quizUID])
			cur.execute("DELETE FROM quiz WHERE quizUniqueID = (?)", [quizUID])
			cur.execute("DELETE FROM userresults WHERE quizUniqueID = (?)", [quizUID])
			bot.send_message(call.message.chat.id, 'Квиз <b>"{}"</b> [{}] был удалён.'.format(QuizName[0], quizUID), parse_mode='HTML')
		elif call.data == 'generatedNoList':
			bot.delete_message(call.message.chat.id, call.message.message_id)
			generateList(call.message)
		elif call.data == 'generatedBackList':
			bot.delete_message(call.message.chat.id, call.message.message_id)
			createQuiz(call.message)
		elif call.data.startswith('generatedList'):
			bot.delete_message(call.message.chat.id, call.message.message_id)
			quizUID = call.data.split('generatedList')[1]
			cur.execute("SELECT tgID FROM userresults WHERE quizUniqueID = (?)", [quizUID])
			UniqueUsers = set(cur.fetchall())
			UsersListMenu = types.InlineKeyboardMarkup()
			for user in UniqueUsers:
				cur.execute("SELECT _rowid_ FROM userresults WHERE questionResult = '+' AND quizUniqueID = :quizUniqueID AND tgID = :tgID", {'quizUniqueID': quizUID, 'tgID': user[0]})
				CountOfUserResults = len(cur.fetchall())
				cur.execute("SELECT name FROM users WHERE tgID = (?)", user)
				UserName = cur.fetchone()
				cur.execute("SELECT _rowid_ FROM quiz WHERE quizUniqueID = (?)", [quizUID])
				QuestionsCount = len(cur.fetchall())
				UsersListMenu.add(types.InlineKeyboardButton('{} - {}/{}'.format(UserName[0], CountOfUserResults, QuestionsCount), callback_data='userlist{}/{}'.format(user[0], quizUID)), types.InlineKeyboardButton('❌', callback_data='userdelete{}/{}'.format(user[0], quizUID)))
			cur.execute("SELECT quizName FROM userquiz WHERE quizUniqueID = (?)", [quizUID])
			QuizName = cur.fetchone()
			UsersListMenu.add(types.InlineKeyboardButton('[Закрыть]', callback_data='userClose'))
			bot.send_message(call.message.chat.id, 'Список пользователей, прошедших квиз: <b>"{}"</b> [{}]'.format(QuizName[0], quizUID), reply_markup=UsersListMenu, parse_mode='HTML')
		con.commit()
		con.close()

@bot.callback_query_handler(func=lambda call: call.data.startswith('user'))
def userlistmenu(call):
	if call.message:
		con = sq.connect('quizbot.db')
		cur = con.cursor()
		if call.data.startswith('userlist'):
			bot.delete_message(call.message.chat.id, call.message.message_id)
			InfoAboutUser = call.data.split('userlist')[1].split('/')
			cur.execute("SELECT name FROM users WHERE tgID = (?)", [InfoAboutUser[0]])
			UserName = cur.fetchone()
			cur.execute("SELECT quizQuestion, questionResult FROM userresults WHERE tgID = :tgID AND quizUniqueID = :quizUniqueID", {'tgID': InfoAboutUser[0], 'quizUniqueID': InfoAboutUser[1]})
			UserQuizResults = cur.fetchall()
			cur.execute("SELECT _rowid_ FROM userresults WHERE questionResult = '+' AND quizUniqueID = :quizUniqueID AND tgID = :tgID", {'quizUniqueID': InfoAboutUser[1], 'tgID': InfoAboutUser[0]})
			CountOfUserResults = len(cur.fetchall())
			cur.execute("SELECT _rowid_ FROM quiz WHERE quizUniqueID = (?)", [InfoAboutUser[1]])
			QuestionsCount = len(cur.fetchall())
			output = ''
			for i in range(len(UserQuizResults)):
				output += '  "{}": {}\n'.format(UserQuizResults[i][0], UserQuizResults[i][1])
			translation = output.maketrans({'+': '🟢', '-': '🔴'})
			ResultMenu = types.InlineKeyboardMarkup()
			ResultMenu.add(types.InlineKeyboardButton('[Закрыть]', callback_data='userResultBack'), types.InlineKeyboardButton('❌', callback_data='userdelete{}/{}'.format(InfoAboutUser[0], InfoAboutUser[1])))
			bot.send_message(call.message.chat.id, '<i>[Результаты пользователя {}]</i>\n\n🟢 Правильный ответ\n🔴 Неправильный ответ\n\n<b>Вопрос - оценка:</b>\n{}\nКоличество правильных ответов: {}/{}'.format(UserName[0], output.translate(translation), CountOfUserResults, QuestionsCount), reply_markup=ResultMenu, parse_mode='HTML')
		elif call.data == 'userResultBack':
			bot.delete_message(call.message.chat.id, call.message.message_id)
		elif call.data.startswith('userdelete'):
			bot.delete_message(call.message.chat.id, call.message.message_id)
			InfoAboutUser = call.data.split('userdelete')[1].split('/')
			cur.execute("SELECT name FROM users WHERE tgID = (?)", [InfoAboutUser[0]])
			UserName = cur.fetchone()
			YouSerious = types.InlineKeyboardMarkup()
			YouSerious.add(types.InlineKeyboardButton('[Да]', callback_data='userYes{}/{}'.format(InfoAboutUser[0], InfoAboutUser[1])), types.InlineKeyboardButton('[Нет]', callback_data='userNo'))
			bot.send_message(call.message.chat.id, 'Удалить результаты квиза пользователя <b>{}</b> [{}]?\n\nВы уверены?'.format(UserName[0], InfoAboutUser[0]), reply_markup=YouSerious, parse_mode='HTML')
		elif call.data == 'userClose':
			bot.delete_message(call.message.chat.id, call.message.message_id)
		elif call.data.startswith('userYes'):
			InfoAboutUser = call.data.split('userYes')[1].split('/')
			cur.execute("SELECT name FROM users WHERE tgID = (?)", [InfoAboutUser[0]])
			UserName = cur.fetchone()
			bot.delete_message(call.message.chat.id, call.message.message_id)
			cur.execute("DELETE FROM userresults WHERE tgID = :tgID AND quizUniqueID = :quizUID", {'tgID': InfoAboutUser[0], 'quizUID': InfoAboutUser[1]})
			bot.send_message(call.message.chat.id, 'Результаты пользователя\n<b>{}</b> [{}] удалены.'.format(UserName[0], InfoAboutUser[0]), parse_mode='HTML')
		elif call.data == 'userNo':
			bot.delete_message(call.message.chat.id, call.message.message_id)
			generateList(call.message)
		con.commit()
		con.close()

#Показываем квиз. Кнопки начать и назад
def quizShow(message):
	global code
	msgText = message.text
	code = msgText.upper()
	quizShowMenu = types.InlineKeyboardMarkup()
	buttonGo = types.InlineKeyboardButton('[Начать]', callback_data='createMenuGo')
	buttonBack = types.InlineKeyboardButton('[Назад]', callback_data='createMenuBack')
	quizShowMenu.add(buttonBack, buttonGo)
	con = sq.connect('quizbot.db')
	cur = con.cursor()
	cur.execute("SELECT tgID, quizName, quizDescription FROM userquiz WHERE quizUniqueID = (?)", [code])
	QuizInfo = cur.fetchall()
	if QuizInfo == []:
		bot.send_message(message.chat.id, 'Увы, но такого квиза не существует.\nМожет быть вы ввели не тот код?')
		createQuiz(message)
	else:
		cur.execute("SELECT name FROM users WHERE tgID = (?)", [QuizInfo[0][0]])
		AuthorName = cur.fetchone()
		cur.execute("SELECT _rowid_ FROM quiz WHERE quizUniqueID = (?)", [code])
		QuizQuestionsCount = len(cur.fetchall())
		bot.send_message(message.chat.id, '<i>[Квиз. Код: {}]</i>\n\nАвтор квиза <b>{}</b> [{}].\nНазвание квиза:\n<b> - {}</b>.\n\nОписание квиза:\n<b> - {}</b>.\n\nКоличество вопросов - <b>{}</b>.'.format(code, AuthorName[0], QuizInfo[0][0], QuizInfo[0][1], QuizInfo[0][2], QuizQuestionsCount), reply_markup=quizShowMenu, parse_mode='HTML')
	con.commit()
	con.close()

#Запуск квиза. Происходит магия обработки квиза
def quizGetData(message):
	global AllQuestions, isUserCompleteThisQuiz
	con = sq.connect('quizbot.db')
	cur = con.cursor()
	cur.execute("SELECT quizQuestionText, quizAnswers FROM quiz WHERE quizUniqueID = (?)", [code])
	AllQuestions = cur.fetchall()
	cur.execute("SELECT _rowid_ FROM userresults WHERE tgID = :tgID AND quizUniqueID = :quizUniqueID", {'tgID': message.chat.id, 'quizUniqueID': code})
	isUserCompleteThisQuiz = len(cur.fetchall())
	if isUserCompleteThisQuiz != 0:
		bot.send_message(message.chat.id, 'Вы уже проходили этот квиз.\n\nКоличество правильных ответов: <b>{}</b> из <b>{}</b>.\n\nВаша следующая попытка не будет учтена.'.format(isUserCompleteThisQuiz, len(AllQuestions)), parse_mode='HTML')
		showQuestion(message)
	else:
		showQuestion(message)
	con.commit()
	con.close()

#Показываем вопрос
def showQuestion(message):
	global RightAns, Answers
	if AllQuestions == []:
		quizEnd(message)
	else:
		Answers = AllQuestions[0][1].split('/')
		RightAns = Answers[0]
		random.shuffle(Answers)
		AnswerMenu = types.InlineKeyboardMarkup()
		for i in range(len(Answers)):
			AnswerMenu.add(types.InlineKeyboardButton(text=Answers[i], callback_data='ans' + str(i)))
		bot.send_message(message.chat.id, AllQuestions[0][0], reply_markup=AnswerMenu)

#Заканчиваем квиз
def quizEnd(message):
	con = sq.connect('quizbot.db')
	cur = con.cursor()
	cur.execute("SELECT _rowid_ FROM userresults WHERE tgID = :tgID AND quizUniqueID = :quizUniqueID AND questionResult = '+'", {'tgID': message.chat.id, 'quizUniqueID': code})
	RightAnsCount = len(cur.fetchall())
	cur.execute("SELECT quizQuestionText, quizAnswers FROM quiz WHERE quizUniqueID = (?)", [code])
	QuestionsCount = len(cur.fetchall())
	if isUserCompleteThisQuiz != 0:
		bot.send_message(message.chat.id, '<i>[Квиз завершён]</i>\n\nЭта попытка не была сохранена.\n\nВ первой попытке правильных ответов: <b>{}</b> из <b>{}</b>.'.format(RightAnsCount, QuestionsCount), parse_mode='HTML')
	else:
		bot.send_message(message.chat.id, '<i>[Квиз завершён]</i>\n\nВы правильно ответили на: <b>{}</b> из <b>{}</b>.'.format(RightAnsCount, QuestionsCount), parse_mode='HTML')
	con.commit()
	con.close()

#Callback от клавиатуры с вопросами
@bot.callback_query_handler(func=lambda call: call.data.startswith('ans'))
def answermenu(call):
	if call.message:
		result = []
		con = sq.connect('quizbot.db')
		cur = con.cursor()
		for i in range(len(Answers)):
			if call.data == 'ans{}'.format(i) and RightAns == Answers[i]:
				result.append(True)
			else: result.append(False)
		if True in result:
			cur.execute("SELECT questionResult FROM userresults WHERE tgID = :tgID AND quizUniqueID = :quizUID AND quizQuestion = :quizQuestion", {'tgID': call.message.chat.id, 'quizUID': code, 'quizQuestion': AllQuestions[0][0]})
			IsUserDoThisQuestion = cur.fetchall()
			if IsUserDoThisQuestion == []:
				bot.delete_message(call.message.chat.id, call.message.message_id)
				cur.execute("INSERT INTO userresults (tgID, quizUniqueID, quizQuestion, questionResult) VALUES (?, ?, ?, ?)", [call.message.chat.id, code, AllQuestions[0][0], '+'])
				bot.send_message(call.message.chat.id, 'Верно!\nОтвет: <b>{}</b>'.format(RightAns), parse_mode='HTML')
			else:
				bot.delete_message(call.message.chat.id, call.message.message_id)
				bot.send_message(call.message.chat.id, 'Верно!\nОтвет: <b>{}</b>'.format(RightAns), parse_mode='HTML')
		else:
			cur.execute("SELECT questionResult FROM userresults WHERE tgID = :tgID AND quizUniqueID = :quizUID AND quizQuestion = :quizQuestion", {'tgID': call.message.chat.id, 'quizUID': code, 'quizQuestion': AllQuestions[0][0]})
			IsUserDoThisQuestion = cur.fetchall()
			if IsUserDoThisQuestion == []:
				bot.delete_message(call.message.chat.id, call.message.message_id)
				cur.execute("INSERT INTO userresults (tgID, quizUniqueID, quizQuestion, questionResult) VALUES (?, ?, ?, ?)", [call.message.chat.id, code, AllQuestions[0][0], '-'])
				bot.send_message(call.message.chat.id, 'Увы, не верно!\nПравильный ответ: <b>{}</b>'.format(RightAns), parse_mode='HTML')
			else:
				bot.delete_message(call.message.chat.id, call.message.message_id)
				bot.send_message(call.message.chat.id, 'Увы, не верно!\nПравильный ответ: <b>{}</b>'.format(RightAns), parse_mode='HTML')
		con.commit()
		con.close()
		AllQuestions.pop(0)
		showQuestion(call.message)

#Название нового квиза. Создание
def quizname(message):
	global quizName
	quizName = message.text
	quizDescription = bot.send_message(message.chat.id, 'Введите описание этого квиза.')
	bot.register_next_step_handler(quizDescription, quizdescription)

#Функция для создания уникального кода квиза
def uniqueid():
	global quizUniqueID
	Symbols = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
	quizUniqueID = ''
	con = sq.connect('quizbot.db')
	cur = con.cursor()
	for i in range(5):
		quizUniqueID += random.choice(list(Symbols))
	cur.execute("SELECT _rowid_ FROM quiz WHERE quizUniqueID = (?)", [quizUniqueID])
	while len(cur.fetchall()) != 0:
		for i in range(5):
			quizUniqueID += random.choice(list(Symbols))
		cur.execute("SELECT _rowid_ FROM userquiz WHERE quizUniqueID = (?)", [quizUniqueID])
	con.commit()
	con.close()

#Описание квиза. Создание
def quizdescription(message):
	global quizDescription
	con = sq.connect('quizbot.db')
	cur = con.cursor()
	quizDescription = message.text
	uniqueid()
	cur.execute("INSERT INTO userquiz (tgID, quizUniqueID, quizName, quizDescription) VALUES (?, ?, ?, ?)", [message.chat.id, quizUniqueID, quizName, quizDescription])
	con.commit()
	con.close()
	quizMenu(message)

#Меню добавления вопроса/ завершения квиза
def quizMenu(message):
	con = sq.connect('quizbot.db')
	cur = con.cursor()
	quizSetuper = types.InlineKeyboardMarkup()
	buttonNewQuestion = types.InlineKeyboardButton('[Добавить вопрос]', callback_data='setupQuestion')
	buttonDone = types.InlineKeyboardButton('[Завершить]', callback_data='setupDone')
	buttonCancel = types.InlineKeyboardButton('[Отмена]', callback_data='setupCancel')
	quizSetuper.add(buttonDone, buttonNewQuestion, buttonCancel)
	cur.execute("SELECT _rowid_ FROM quiz WHERE quizUniqueID = (?)", [quizUniqueID])
	AnsCount = len(cur.fetchall())
	bot.send_message(message.chat.id, '<i>[Меню создания нового квиза]</i>\n\nНазвание квиза - <b>"{}"</b>\nОписание квиза:\n<b>"{}"</b>\nКоличество вопросов - <b>{}</b>'.format(quizName, quizDescription, AnsCount), reply_markup=quizSetuper, parse_mode='HTML')
	con.commit()
	con.close()

#Callback от Меню создания вопросов квиза
@bot.callback_query_handler(func=lambda call: call.data.startswith('setup'))
def setup(call):
	if call.message:
		if call.data == 'setupQuestion':
			bot.delete_message(call.message.chat.id, call.message.message_id)
			askQuestion = bot.send_message(call.message.chat.id, '<i>[Введите текст вопроса]</i>\n\nВведите текст вашего вопроса.', parse_mode='HTML')
			bot.register_next_step_handler(askQuestion, askquestion)
		elif call.data == 'setupDone':
			bot.delete_message(call.message.chat.id, call.message.message_id)
			bot.send_message(call.message.chat.id, '<i>[Создан новый квиз]</i>\n\nВы создали новый квиз.\n\nУникальный код вашего квиза - <b>{}</b>\n\nПосмотреть список ваших квизов вы можете в меню квизов.'.format(quizUniqueID),parse_mode='HTML')
		elif call.data == 'setupCancel':
			bot.delete_message(call.message.chat.id, call.message.message_id)
			con = sq.connect('quizbot.db')
			cur = con.cursor()
			cur.execute("DELETE FROM quiz WHERE quizUniqueID = (?)", [quizUniqueID])
			cur.execute("DELETE FROM userquiz WHERE quizUniqueID = (?)", [quizUniqueID])
			con.commit()
			con.close()
			bot.send_message(call.message.chat.id, 'Создание квиза отменено. Все данные удалены.')

#Спрашиваем пользователя вопрос
def askquestion(message):
	global question
	question = message.text
	askAnswers = bot.send_message(message.chat.id, '<i>[Введите список ответов]</i>\n\nТеперь напишите правильный ответ первым, а через знак "/" все возможные варианты ответа.\n\n<i>Внимание! Разделять вопросы через знак "/" очень важно, или ничего не получится!</i>', parse_mode='HTML')
	bot.register_next_step_handler(askAnswers, askanswers)

#Спрашиваем пользователя правильный ответ и другие ответы
def askanswers(message):
	global quizQuestionID
	answers = message.text
	con = sq.connect('quizbot.db')
	cur = con.cursor()
	cur.execute("SELECT quizQuestionID FROM quiz WHERE quizUniqueID = (?)", [quizUniqueID])
	quizQuestionID = len(cur.fetchall()) + 1
	cur.execute("INSERT INTO quiz (tgID, quizUniqueID, quizQuestionID, quizQuestionText, quizAnswers) VALUES (?, ?, ?, ?, ?)", [message.chat.id, quizUniqueID, quizQuestionID, question, answers])
	bot.send_message(message.chat.id, '<i>[Создан вопрос]</i>\n\nВопрос: <b>"{}"</b>\nВарианты ответа:\n\n<b>- {}</b>\n\nПравильный ответ: \n<b>[{}]</b>'.format(question, '\n- '.join(answers.split('/')), answers.split('/')[0]), parse_mode='HTML')
	con.commit()
	con.close()
	quizMenu(message)

@bot.message_handler(commands=['info'])
def info(message):
	bot.send_message(message.chat.id, '<i>~~~</i>>', parse_mode='HTML')

@bot.message_handler(commands=['feedback'])
def feedback(message):
	FeedbackMenu = types.InlineKeyboardMarkup()
	buttonRate = types.InlineKeyboardButton('[Оценить]', callback_data='feedbackRate')
	buttonOpinion = types.InlineKeyboardButton('[Поделиться мнением]', callback_data='feedbackOpinion')
	FeedbackMenu.add(buttonOpinion).add(buttonRate)
	con = sq.connect('quizbot.db')
	cur = con.cursor()
	cur.execute("SELECT name FROM users WHERE tgID = (?)", [message.chat.id])
	userName = cur.fetchone()
	bot.send_message(message.chat.id, '<i>[Меню обратной связи]</i>\n\nПривет, <b>{}</b>!\nВ этом меню вы можете оставить оценку от 1 до 5, а так же своё мнение. Допустим, что бы вы хотели добавить в этого бота, какие функции вам нравятся, какие не нравятся.\nВообще, можете писать что вам угодно. Нам будет приятно.'.format(userName[0]), reply_markup=FeedbackMenu, parse_mode='HTML')
	con.commit()
	con.close()

@bot.callback_query_handler(func=lambda call: call.data.startswith('feedback'))
def feedbackMenu(call):
	if call.message:
		if call.data == 'feedbackRate':
			bot.delete_message(call.message.chat.id, call.message.message_id)
			getRate = bot.send_message(call.message.chat.id, 'Введите оценку от 1 до 5.\n\n<b>Если вы захотите повторно оставить оценку, ваша предыдущая оценка заменится на новую!</b>', parse_mode='HTML')
			bot.register_next_step_handler(getRate, getrate)
		elif call.data == 'feedbackOpinion':
			bot.delete_message(call.message.chat.id, call.message.message_id)
			getOpinion = bot.send_message(call.message.chat.id, 'Напишите своё мнение о нашем боте.\n\n<b>Если вы захотите повторно оставить мнение, ваша предыдущая запись заменится на новую!</b>', parse_mode='HTML')
			bot.register_next_step_handler(getOpinion, getopinion)

def getrate(message):
	con = sq.connect('quizbot.db')
	cur = con.cursor()
	cur.execute("UPDATE users SET rate = :rate WHERE tgID = :tgID", {'rate': message.text, 'tgID': message.chat.id})
	cur.execute("SELECT name FROM users WHERE tgID = (?)", [message.chat.id])
	UserName = cur.fetchone()
	bot.send_message(message.chat.id, 'Мы записали вашу оценку.\n\n<b>{}</b>, спасибо за то что помогаете сделать бота лучше!'.format(UserName[0]), parse_mode='HTML')
	con.commit()
	con.close()

def getopinion(message):
	con = sq.connect('quizbot.db')
	cur = con.cursor()
	cur.execute("UPDATE users SET opinion = :opinion WHERE tgID = :tgID", {'opinion': message.text, 'tgID': message.chat.id})
	cur.execute("SELECT name FROM users WHERE tgID = (?)", [message.chat.id])
	UserName = cur.fetchone()
	bot.send_message(message.chat.id, 'Мы записали ваше мнение.\n\n<b>{}</b>, спасибо за то что помогаете сделать бота лучше!'.format(UserName[0]), parse_mode='HTML')
	con.commit()
	con.close()

#Команды ReplyKeyboard + непонимашка
@bot.message_handler(func=lambda message: True)
def echo_all(message):
	print('[{}]'.format(str(message.chat.id)), '>> ', message.text)
	if message.text == 'Помощь':
		helpCMD(message)
	elif message.text == 'Квизы':
		createQuiz(message)
	elif message.text == 'Профиль':
		profile(message)
	elif message.text == 'Инфо':
		info(message)
	elif message.text == 'Обратная связь':
		feedback(message)
	else:
		bot.reply_to(message, 'Я вас не понимаю... 😔 \nНапишите /help для просмотра списка команд.')

bot.infinity_polling()  # бот принимает ответы