from django.http.response import JsonResponse
from django.shortcuts import render
from datetime import datetime
from django.http import JsonResponse
import json
import string, random, smtplib, psycopg2
from email.mime.text import MIMEText
from django.views.decorators.csrf import csrf_exempt


# Odoogiin tsagiig duuddag service
def dt_gettime(request):
    jsons = json.loads(request.body) # request body-g dictionary bolgon avch baina
    action = jsons["action"] #jsons-s action-g salgaj avch baina
    respdata = [{'time':datetime.now().strftime("%Y/%m/%d, %H:%M:%S")}]  # response-n data-g beldej baina. list turultei baih
    resp = sendResponse(request, 200, respdata, action)
    # response beldej baina. 6 keytei.
    return resp
# dt_gettime

#login service
def dt_login(request):
    jsons = json.loads(request.body) # get request body
    action = jsons['action'] # get action key from jsons
    # print(action)
    try:
        uname = jsons['uname'].lower() # get uname key from jsons
        upassword = jsons['upassword'] # get upassword key from jsons
    except: # uname, upassword key ali neg ni baihgui bol aldaanii medeelel butsaana
        action = jsons['action']
        respdata = []
        resp = sendResponse(request, 3006, respdata, action) # response beldej baina. 6 keytei.
        return resp
    
    try: 
        myConn = connectDB() # database holbolt uusgej baina
        cursor = myConn.cursor() # cursor uusgej baina
        
        # Hereglegchiin ner, password-r nevtreh erhtei (isverified=True) hereglegch login hiij baigaag toolj baina.
        query = F"""SELECT COUNT(*) AS usercount, MIN(fname) AS fname, MAX(lname) AS lname FROM t_user 
                WHERE uname = '{uname}' 
                AND isverified = True 
                AND upassword = '{upassword}' 
                AND isbanned = False """ 
        print(query)
        cursor.execute(query) # executing query
        print(query)
        columns = cursor.description #
        respRow = [{columns[index][0]:column for index, 
            column in enumerate(value)} for value in cursor.fetchall()] # respRow is list and elements are dictionary. dictionary structure is columnName : value
        print(respRow)
        cursor.close() # close the cursor. ALWAYS

        if respRow[0]['usercount'] == 1: # verified user oldson uyd login hiine
            cursor1 = myConn.cursor() # creating cursor1
            
            # get logged user information
            query = F"""SELECT uname, fname, lname, lastlogin
                    FROM t_user 
                    WHERE uname = '{uname}' AND isverified = True AND upassword = '{upassword}'"""
            
            cursor1.execute(query) # executing cursor1
            columns = cursor1.description # 
            # print(columns, "tuples")
            respRow = [{columns[index][0]:column for index, 
                column in enumerate(value)} for value in cursor1.fetchall()] # respRow is list. elements are dictionary. dictionary structure is columnName : value
            # print(respRow)
            
            uname = respRow[0]['uname'] # 
            fname = respRow[0]['fname'] #
            lname = respRow[0]['lname'] #
            lastlogin = respRow[0]['lastlogin'] #

            respdata = [{'uname':uname, 'fname':fname, 'lname':lname, 'lastlogin':lastlogin}] # creating response logged user information
            resp = sendResponse(request, 1002, respdata, action) # response beldej baina. 6 keytei.

            query = F"""UPDATE t_user 
                    SET lastlogin = NOW()
                    WHERE uname = '{uname}' AND isverified = True AND upassword = '{upassword}'"""
            
            cursor1.execute(query) # executing query cursor1
            myConn.commit() # save update query database
            cursor1.close() # closing cursor1
            
        else: # if user name or password wrong 
            data = [{'uname':uname}] # he/she wrong username, password. just return username
            resp = sendResponse(request, 1004, data, action) # response beldej baina. 6 keytei.
    except:
        # login service deer aldaa garval ajillana. 
        action = jsons["action"]
        respdata = [] # hooson data bustaana.
        resp = sendResponse(request, 5001, respdata, action) # standartiin daguu 6 key-tei response butsaana
        
    finally:
        disconnectDB(myConn) # yamarch uyd database holbolt uussen bol holboltiig salgana. Uchir ni finally dotor baigaa
        return resp # response bustaaj baina
#dt_login

def dt_register(request):
    jsons = json.loads(request.body) # get request body
    action = jsons["action"] # get action key from jsons
    # print(action)
    try :
        uname = jsons["uname"].lower() # get uname key from jsons and lower
        lname = jsons["lname"].capitalize() # get lname key from jsons and capitalize
        fname = jsons["fname"].capitalize() # get fname key from jsons and capitalize
        upassword = jsons["upassword"] # get upassword key from jsons
    except:
        # uname, upassword, fname, lname key ali neg ni baihgui bol aldaanii medeelel butsaana
        action = jsons['action']
        respdata = []
        resp = sendResponse(request, 3007, respdata, action) # response beldej baina. 6 keytei.
        return resp
    
    try:
        conn = connectDB() # database holbolt uusgej baina
        cursor = conn.cursor() # cursor uusgej baina
        # Shineer burtguulj baigaa hereglegch burtguuleh bolomjtoi esehiig shalgaj baina
        print("Helloooooooooooooooooo")
        query = F"""SELECT COUNT(*) AS usercount  
                    FROM t_user  
                    WHERE uname = '{uname}' AND isverified = True"""
        print("Helloooooooooooooooooo2")
        print (query)
        cursor.execute(query) # executing query
        # print(cursor.description)
        columns = cursor.description #
        respRow = [{columns[index][0]:column for index, 
            column in enumerate(value)} for value in cursor.fetchall()] # respRow is list and elements are dictionary. dictionary structure is columnName : value
        print(respRow)
        cursor.close() # close the cursor. ALWAYS

        if respRow[0]["usercount"] == 0: # verified user oldoogui uyd ajillana
            cursor1 = conn.cursor() # creating cursor1
            # Insert user to t_user
            query = F"""INSERT INTO t_user(uname, lname, fname, upassword, isverified, isbanned, regdate, lastlogin) 
                        VALUES('{uname}','{lname}','{fname}', '{upassword}',
                        False, False, NOW(), '1970-01-01') 
                        RETURNING uid"""
            
            cursor1.execute(query) # executing cursor1
            uid = cursor1.fetchone()[0] # Returning newly inserted (uid)
            # print(uid, "uid")
            conn.commit() # updating database

            token = generateStr(20) # generating token 20 urttai
            query = F"""INSERT INTO t_token(uid, token, tokentype, tokenenddate, createddate) 
                        VALUES({uid}, '{token}', 'register', NOW() + interval \'1 day\', NOW() )""" # Inserting t_token
            # print(query)
            cursor1.execute(query) # executing cursor1
            conn.commit() # updating database
            cursor1.close() # closing cursor1
            # sara
            subject = "User burtgel batalgaajuulah mail"
            bodyHTML = F"""http://localhost:8000/users/?token={token}"""
            sendMail(uname, subject, bodyHTML)
            
            action = jsons['action']
            # register service success response with data
            respdata = [{"uname":uname,"lname":lname,"fname":fname}]
            resp = sendResponse(request, 200, respdata, action) # response beldej baina. 6 keytei.

        else:
            action = jsons['action']
            respdata = [{"uname":uname,"fname":fname}]
            resp = sendResponse(request, 3008, respdata, action) # response beldej baina. 6 keytei.
            print(resp, "9876543210")
    except (Exception) as e:
        # register service deer aldaa garval ajillana. 
        action = jsons["action"]
        respdata = [{"aldaa":str(e)}] # hooson data bustaana.
        resp = sendResponse(request, 5002, respdata, action) # standartiin daguu 6 key-tei response butsaana
        
    finally:
        disconnectDB(conn) # yamarch uyd database holbolt uussen bol holboltiig salgana. Uchir ni finally dotor baigaa
        return resp # response bustaaj baina

# dt_register

@csrf_exempt # method POST uyd ajilluulah csrf
def checkService(request): # hamgiin ehend duudagdah request shalgah service
    if request.method == "POST": # Method ni POST esehiig shalgaj baina
        try:
            # request body-g dictionary bolgon avch baina
            jsons = json.loads(request.body)
        except:
            # request body json bish bol aldaanii medeelel butsaana. 
            action = "no action"
            respdata = [] # hooson data bustaana.
            resp = sendResponse(request, 3003, respdata) # standartiin daguu 6 key-tei response butsaana
            return JsonResponse(resp) # response bustaaj baina
            
        try: 
            #jsons-s action-g salgaj avch baina
            action = jsons["action"]
        except:
            # request body-d action key baihgui bol aldaanii medeelel butsaana. 
            action = "no action"
            respdata = [] # hooson data bustaana.
            resp = sendResponse(request, 3005, respdata,action) # standartiin daguu 6 key-tei response butsaana
            return JsonResponse(resp)# response bustaaj baina
        
        # request-n action ni gettime
        if action == "gettime":
            result = dt_gettime(request)
            return JsonResponse(result)
        # request-n action ni login bol ajillana
        elif action == "login":
            result = dt_login(request)
            return JsonResponse(result)
        # request-n action ni register bol ajillana
        elif action == "register":
            result = dt_register(request)
            return JsonResponse(result)
        # request-n action ni burtgegdeegui action bol else ajillana.
        else:
            action = "no action"
            respdata = []
            resp = sendResponse(request, 3001, respdata,action)
            return JsonResponse(resp)
    elif request.method == "GET":
        print("helooo")
        #http://localhost:8000/users/token=erjhfbuegrshjwiefnqier
        token = request.GET.get('token')
        print(token, 'token')
        
        print("helooo")
        conn = connectDB() # database holbolt uusgej baina
        cursor = conn.cursor() # cursor uusgej baina
        # ashere
        query = F"""
                SELECT COUNT(*) AS tokencount
                    , MIN(t_token) AS tokenid
                    , MIN(uid) AS uid
                    , MIN(token) token, MIN(tokentype) tokentype
                FROM t_token 
                WHERE token = '{token}' 
                        AND tokenenddate > NOW()"""
        # print (query)
        cursor.execute(query) # executing query
        # print(cursor.description)
        columns = cursor.description #
        respRow = [{columns[index][0]:column for index, 
            column in enumerate(value)} for value in cursor.fetchall()] # respRow is list and elements are dictionary. dictionary structure is columnName : value
        # print(respRow)
        
        cursor.close() # close the cursor. ALWAYS
        
        if respRow[0]["tokencount"] == 1: # 
            
            uid = respRow[0]["uid"]
            tokentype = respRow[0]["tokentype"]
            tokenid = respRow[0]["tokenid"]
            
            cursor = conn.cursor() # cursor uusgej baina
            if tokentype == "register":
                query = f"""SELECT uname, lname, fname, regdate FROM t_user
                        WHERE uid = {uid}"""
                cursor.execute(query) # executing query
                
                columns = cursor.description #
                respRow = [{columns[index][0]:column for index, 
                    column in enumerate(value)} for value in cursor.fetchall()]
                uname = respRow[0]['uname']
                lname = respRow[0]['lname']
                fname = respRow[0]['fname']
                createddate = respRow[0]['regdate']
                
                query  = f"""SELECT COUNT(*) AS userverified
                            , MIN(uname) AS uname
                            FROM t_user 
                            WHERE uname = '{uname}' AND isverified = True"""
                cursor.execute(query) # executing query
                columns = cursor.description #
                respRow = [{columns[index][0]:column for index, 
                    column in enumerate(value)} for value in cursor.fetchall()]
                if respRow[0]['userverified'] == 0:
                    token = generateStr(30)
                    query = f"UPDATE t_user SET isverified = true WHERE uid = {uid}"
                    cursor.execute(query)
                    conn.commit()
                    
                    query = f"""UPDATE t_token SET token = '{token}', 
                                tokenenddate = '1970-01-01' WHERE t_token = {tokenid}"""
                    cursor.execute(query)
                    conn.commit()
                    
                    action = "verified"
                    respdata = [{"uid":uid,"uname":uname, "lname":lname,
                                "fname":fname,"tokentype":tokentype
                                , "createddate":createddate}]
                    resp = sendResponse(request, 3010, respdata, action) # response beldej baina. 6 keytei.
                else:
                    action = "notverified"
                    respdata = [{"uname":uname,"tokentype":tokentype}]
                    resp = sendResponse(request, 3014, respdata, action) # response beldej baina. 6 keytei.
            elif tokentype == "forgot":
                
                query = f"""SELECT uname, lname, fname, regdate FROM t_user
                        WHERE uid = {uid} AND isverified = True"""
                cursor.execute(query) # executing query
                
                columns = cursor.description #
                respRow = [{columns[index][0]:column for index, 
                    column in enumerate(value)} for value in cursor.fetchall()]
                uname = respRow[0]['uname']
                lname = respRow[0]['lname']
                fname = respRow[0]['fname']
                createddate = respRow[0]['createddate']
                
                action = "forgotverify"
                respdata = [{"uid":uid,"uname":uname,  "tokentype":tokentype
                            , "createddate":createddate}]
                resp = sendResponse(request, 3011, respdata, action) # response beldej baina. 6 keytei.
                
            disconnectDB(conn)
            return JsonResponse(resp)
        else:
            # token buruu esvel hugatsaa duussan 
            action = "token"
            respdata = []
            resp = sendResponse(request, 3009, respdata, action) # response beldej baina. 6 keytei.
            return JsonResponse(resp)
        
        # action = "token"
        # respdata = [{"token":token}]
        # resp = sendResponse(request, 200, respdata, action)
        # return JsonResponse(resp)
    # Method ni POST, GET ali ali ni bish bol ajillana
    else:
        #GET, POST-s busad uyd ajillana
        action = "no action"
        respdata = []
        resp = sendResponse(request, 3002, respdata, action)
        return JsonResponse(resp)
        
#Standartiin daguu response json-g 6 key-tei bolgoj beldej baina.
def sendResponse(request, resultCode, data, action="no action"):
    response = {} # response dictionary zarlaj baina
    response["resultCode"] = resultCode # 
    response["resultMessage"] = resultMessages[resultCode] #resultCode-d hargalzah message-g avch baina
    response["data"] = data
    response["size"] = len(data) # data-n urtiig avch baina
    response["action"] = action
    response["curdate"] = datetime.now().strftime('%Y/%m/%d %H:%M:%S') # odoogiin tsagiig response-d oruulj baina

    return response 
#   sendResponse

# result Messages. nemj hugjuuleerei
resultMessages = {
    200 : "Амжилттай",
    201 : "Амжилттай бүртгэлээ",
    400 : "Буруу хүсэлт",
    404 : "Олдсонгүй.",
    505 : "Алдаа",
    1000 : "Бүртгэхгүй боломжгүй. Цахим шуудан өмнө нь бүртгэлтэй байна.",
    1001 : "Хэрэглэгч амжилттай бүртгэгдлээ. Баталгаажуулах мэйл илгээлээ. 24 цагийн дотор баталгаажуулна уу.",
    1002 : "Амжилттай нэвтэрлээ.",
    1003 : "Амжилттай баталгаажлаа.",
    1004 : "Хэрэглэгчийн нэр, нууц үг буруу байна.",
    3001 : "ACTION буруу",
    3002 : "METHOD буруу",
    3003 : "JSON буруу",
    3004 : "Токений хугацаа дууссан. Идэвхгүй токен байна.",
    3005 : "NO ACTION",
    3006 : "Нэвтрэх сервис key дутуу",
    3007 : "Бүртгүүлэх сервисийн key дутуу",
    3008 : "Баталгаажсан хэрэглэгч байна",
    3009 : "Идэвхгүй токен байна",
    3010 : "Бүртгэл баталгаажлаа",
    3011 : "Мартсан нууц үг баталгаажлаа",
    3012 : "Мартсан нууц үг хүсэлт илгээлээ",
    3013 : "Нууц үг мартсан хэрэглэгч олдсонгүй",
    3014 : "Баталгаажсан хэрэглэгч байна",
    5001 : "Нэвтрэх сервис дотоод алдаа",
    5002 : "Бүртгүүлэх сервис дотоод сервис"
}


# db connection
def connectDB():
    conn = psycopg2.connect (
        host = 'localhost', #server host
        # host = '59.153.86.251',
        dbname = 'projectzero', # database name
        user = 'postgres', # databse user 
        password = '1234', 
        port = '5432', # postgre port
    )
    return conn
# connectDB


# DB disconnect hiij baina
def disconnectDB(conn):
    conn.close()
# disconnectDB

#random string generating
def generateStr(length):
    characters = string.ascii_lowercase + string.digits # jijig useg, toonuud
    password = ''.join(random.choice(characters) for i in range(length)) # jijig useg toonuudiig token-g ugugdsun urtiin daguu (parameter length) uusgej baina
    return password # uusgesen token-g butsaalaa
# generateStr


def sendMail(recipient, subj, bodyHtml):
    sender_email = "testmail@mandakh.edu.mn"
    sender_password = "Mandakh2"
    # sender_email = "star.odic@gmail.com"
    # sender_password = "Odic!3005"
    recipient_email = recipient
    subject = subj
    body = bodyHtml
    html_message = MIMEText(body, 'html')
    html_message['Subject'] = subject
    html_message['From'] = sender_email
    html_message['To'] = recipient_email
    with smtplib.SMTP('smtp-mail.outlook.com',587) as server:
        server.ehlo()
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, html_message.as_string())
        server.quit()

#sendMail

# def dt_register(request):
#     jsons = json.loads(request.body)
#     action = jsons['action']
#     firstname = jsons['firstname']
#     lastname = jsons['lastname']
#     email = jsons['email']
#     passw = jsons['passw']

#     myCon = connectDB()
#     cursor = myCon.cursor()
    
#     query = F"""SELECT COUNT(*) AS usercount FROM t_user 
#             WHERE email = '{email}' AND enabled = 1"""
    
#     cursor.execute(query)
#     columns = cursor.description
#     respRow = [{columns[index][0]:column for index, 
#         column in enumerate(value)} for value in cursor.fetchall()]
#     cursor.close()

#     if respRow[0]['usercount'] == 1:
#         data = [{'email':email}]
#         resp = sendResponse(request, 1000, data, action)
#     else:
#         token = generateStr(12)
#         query = F"""INSERT INTO public.t_user(
#   email, lastname, firstname, passw, regdate, enabled, token, tokendate)
#   VALUES ('{email}', '{lastname}', '{firstname}', '{passw}'
#     , NOW(), 0, '{token}', NOW() + interval \'1 day\');"""
#         cursor1 = myCon.cursor()
#         cursor1.execute(query)
#         myCon.commit()
#         cursor1.close()
#         data = [{'email':email, 'firstname':firstname, 'lastname': lastname}]
#         resp = sendResponse(request, 1001, data, action)
        

#         sendMail(email, "Verify your email", F"""
#                 <html>
#                 <body>
#                     <p>Ta amjilttai burtguulle. Doorh link deer darj burtgelee batalgaajuulna uu. Hervee ta manai sited burtguuleegui bol ene mailiig ustgana uu.</p>
#                     <p> <a href="http://localhost:8001/check/?token={token}">Batalgaajuulalt</a> </p>
#                 </body>
#                 </html>
#                 """)

#     return resp
# # dt_register




# @csrf_exempt
# def checkToken(request):
#     token = request.GET.get('token')
#     myCon = connectDB()
#     cursor = myCon.cursor()
    
#     query = F"""SELECT COUNT(*) AS usertokencount, MIN(email) as email, MAX(firstname) as firstname, 
#                     MIN(lastname) AS lastname 
#             FROM t_user 
#             WHERE token = '{token}' AND enabled = 0 AND NOW() <= tokendate """
    
#     cursor.execute(query)
#     columns = cursor.description
#     respRow = [{columns[index][0]:column for index, 
#         column in enumerate(value)} for value in cursor.fetchall()]
#     cursor.close()

#     if respRow[0]['usertokencount'] == 1:
#         query = F"""UPDATE t_user SET enabled = 1 WHERE token = '{token}'"""
#         cursor1 = myCon.cursor()
#         cursor1.execute(query)
#         myCon.commit()
#         cursor1.close()

#         tokenExpired = generateStr(30)
#         email = respRow[0]['email']
#         firstname = respRow[0]['firstname']
#         lastname = respRow[0]['lastname']
#         query = F"""UPDATE t_user SET token = '{tokenExpired}', tokendate = NOW() WHERE email = '{email}'"""
#         cursor1 = myCon.cursor()
#         cursor1.execute(query)
#         myCon.commit()
#         cursor1.close()
        
#         data = [{'email':email, 'firstname':firstname, 'lastname':lastname}]
#         resp = sendResponse(request, 1003, data, "verified")
#         sendMail(email, "Tanii mail batalgaajlaa",  F"""
#                 <html>
#                 <body>
#                     <p>Tanii mail batalgaajlaa. </p>
#                 </body>
#                 </html>
#                 """)
#     else:
        
#         data = []
#         resp = sendResponse(request, 3004, data, "not verified")
#     return JsonResponse(json.loads(resp))
# #checkToken
