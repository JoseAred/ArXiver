from django.shortcuts import render
from django.http import HttpResponse
import json
import requests
from bs4 import BeautifulSoup as bs
import json
import urllib
import os
from . import models
import hashlib
from django.forms.models import model_to_dict
import jaro
import ast
from operator import attrgetter

class Paper:
    def __init__(self):
        self.author = []
        self.id = None
        self.updatedTime = None
        self.publishedTime = None
        self.title = None
        self.summary = None
        self.category = []
        self.doiLink = None
        self.paperLink = None
        self.pdfLink = None
        self.score = 0


def index(request):
    return HttpResponse(json.dumps('Hello World'))


def getPaperNum(request):
    method = request.GET.get('method','ti')
    query = request.GET.get('query','electron artificial human dioxide geometry part teacher animal this is only for test')
    sortBy = request.GET.get('sortBy','lastUpdatedDate')
    sortOrder = request.GET.get('sortOrder','ascending')
    maxNum = '1000'
    url = "http://export.arxiv.org/api/query?search_query=" + method + ":" + query + "&sortBy="+sortBy+"&sortOrder="+sortOrder+"&max_results="+maxNum
    try:
        res = requests.get(url)
    except:
        res = dict()
        res['retCode'] = 404
        res = json.dump(res)
        return HttpResponse(json.dumps(res))
    data = res.text
    soup = bs(data,'lxml')
    entries = soup.find_all('entry')
    PaperNum = len(entries)
    return HttpResponse(json.dumps({'retCode':200,'num':PaperNum}))

def searchPaper(request):
    method = request.GET.get('method','ti')
    query = request.GET.get('query','electron')
    sortBy = request.GET.get('sortBy','lastUpdatedDate')
    sortOrder = request.GET.get('sortOrder','ascending')
    maxNum = request.GET.get('maxNum','200')
    start = request.GET.get('start','0')
    url = "http://export.arxiv.org/api/query?search_query=" + method + ":" + query + "&sortBy="+sortBy+"&sortOrder="+sortOrder+"&start="+start+"&max_results="+maxNum
    '''
    url = 'http://export.arxiv.org/api/query?search_query=ti:%22electron%20thermal%20conductivity%22&sortBy=lastUpdatedDate&sortOrder=ascending'
    '''  
    try:
        res = requests.get(url)
    except:
        res = dict()
        res['resCode'] = 404
        res = json.dump(res)
        return HttpResponse(res)
    data = res.text
    soup = bs(data,'lxml')
    entries = soup.find_all('entry')
    papers = []
    for entry in entries:
        newPaper = Paper()
        newPaper.id = entry.id.string
        newPaper.updatedTime = entry.updated.string
        newPaper.publishedTime = entry.published.string
        newPaper.title = entry.title.string
        newPaper.summary = entry.summary.string
        authors = entry.find_all('author')
        for author in authors:
            newPaper.author.append(author.contents[1].string)
        categories = entry.find_all('category')
        for category in categories:
            newPaper.category.append(category.get('term'))
        links = entry.find_all('link')
        for link in links:
            if link.get('title')=='doi':
                newPaper.doiLink = link.get('href')
            elif link.get('title')=='pdf':
                newPaper.pdfLink = link.get('href')
            else:
                newPaper.paperLink = link.get('href')
        papers.append(newPaper)
    res = dict()
    res['resCode'] = 200
    res['len'] = len(papers)
    res['papers'] = []
    for paper in papers:
        p = dict()
        p['author'] = ''
        for author in paper.author:
            p['author']+=(author+'/')
        p['id'] = paper.id
        p['updatedTime'] = paper.publishedTime
        p['title'] = paper.title
        p['summary'] = paper.summary
        p['category'] = ''
        for category in paper.category:
            p['category'] +=(category+'/')
        p['doiLink'] = paper.doiLink
        p['paperLink'] = paper.paperLink
        p['pdfLink'] = paper.pdfLink
        res['papers'].append(p)
    res = json.dumps(res)
    return HttpResponse(res)

def showPaper(request):
    url = request.GET.get('url',"http://arxiv.org/pdf/cond-mat/0402245v1")
    
    filename = url[-9:]+'.pdf'
    try:
        res = requests.get(url+'.pdf')
    except:
        res = dict()
        res['retCode'] = 404
        return HttpResponse(res)
    f = open(filename,'wb')
    f.write(res.content)
    f.close()
    with open (filename,'rb') as pdf:
        response = HttpResponse(pdf.read(), content_type='application/pdf')
    os.remove(filename)
    return response
    '''
    fileurl = urllib.request.pathname2url(filename) 
    rp = dict()
    rp['retCode'] = 200
    rp['url'] = fileurl
    return HttpResponse(json.dumps(rp))
    '''


def recommendPaper(request):
    
    user = request.GET.get('user')
    obj = models.UserModel.objects.get(userName=user)
    
    urls = obj.collectList[:10]
    '''
    urls = ["http://arxiv.org/abs/hep-th/9202048v2","http://arxiv.org/abs/cond-mat/9205001v1"]
    '''
    sums = []
    for url in urls:
        res = requests.get(url)
        text = res.text
        soup = bs(text,'lxml')
        s = soup.findAll("blockquote")
        sums.append(s[0].text)
    fields = []
    focusDict = ast.literal_eval(obj.focusDict)
    for (k,v) in focusDict.items:
        fields+=v
    
    papers = []
    for cat in fields:
        url = "http://export.arxiv.org/api/query?search_query=cat:" + cat+ "&sortBy=submittedDate&sortOrder=ascending&max_results=10"
        res = requests.get(url)
        data = res.text
        soup = bs(data,'lxml')
        entries = soup.find_all('entry')
        for entry in entries:
            newPaper = Paper()
            newPaper.id = entry.id.string
            newPaper.updatedTime = entry.updated.string
            newPaper.publishedTime = entry.published.string
            newPaper.title = entry.title.string
            newPaper.summary = entry.summary.string
            authors = entry.find_all('author')
            for author in authors:
                newPaper.author.append(author.contents[1].string)
            categories = entry.find_all('category')
            for category in categories:
                newPaper.category.append(category.get('term'))
            links = entry.find_all('link')
            for link in links:
                if link.get('title')=='doi':
                    newPaper.doiLink = link.get('href')
                elif link.get('title')=='pdf':
                    newPaper.pdfLink = link.get('href')
                else:
                    newPaper.paperLink = link.get('href')
            papers.append(newPaper)
    for paper in papers:
        for summary in sums:
            paper.score+=jaro.jaro_winkler_metric(paper.summary, summary)
    papers = sorted(papers,key=attrgetter('score'))
    if len(papers)>10:
        papers = papers[:10]
    res = dict()
    res['resCode'] = 200
    res['len'] = len(papers)
    res['papers'] = []
    for paper in papers:
        p = dict()
        p['author'] = ''
        for author in paper.author:
            p['author']+=(author+'/')
        p['id'] = paper.id
        p['updatedTime'] = paper.publishedTime
        p['title'] = paper.title
        p['summary'] = paper.summary
        p['category'] = ''
        for category in paper.category:
            p['category'] +=(category+'/')
        p['doiLink'] = paper.doiLink
        p['paperLink'] = paper.paperLink
        p['pdfLink'] = paper.pdfLink
        res['papers'].append(p)
    res = json.dumps(res)
    return HttpResponse(res)
    
    
    

'''
# demo所需函数
def choosePaper(request):
    return render(request, 'choose_paper.html')
def editComment(request):
    return render(request, 'post_comment.html')
def editReply(request):
    return render(request, 'post_reply.html')
'''


# 根据评论ID获取回复
# 非通信函数!!!
def getCommentReply(commentID=1, sortedBy='time', userID='1'):
    res = []
    replys = []
    if sortedBy == 'time':
        replys = models.CommentModel.objects.filter(replyCommentID=commentID).order_by('-pubTime', 'hot')
    elif sortedBy == 'hot':
        replys = models.CommentModel.objects.filter(replyCommentID=commentID).order_by('hot', '-pubTime')
    for single_reply in replys:
        reply = model_to_dict(single_reply, fields=['id',
                                                    'userName',
                                                    'userID',
                                                    'paperID',
                                                    'contentView',
                                                    # 'pubTime',
                                                    'likeNum',
                                                    'dislikeNum',
                                                    'hot',
                                                    'replyCommentID',
                                                    'repliedName',
                                                    'replyNum',
                                                    'avatar',
                                                    'replyList'])
        reply['id'] = single_reply.id
        reply['pubTime'] = str(single_reply.pubTime)
        reply['currentUserLike'] = '2'
        if str(userID) in single_reply.likeUserIDList:
            reply['currentUserLike'] = '0'
        elif str(userID) in single_reply.dislikeUserIDList:
            reply['currentUserLike'] = '1'
        res.append(reply)
    return res


# 根据paperID获取评论
# userID用来判断各个评论的点踩情况
def getPaperComment(request):
    # for debug
    # return render(request, 'display_page.html')
    # paperID = 1
    res = []
    paperID = request.GET.get('paperID', 1)
    userID = request.GET.get('userID', 1)
    # sortedBy = 'time'
    sortedBy = request.GET.get('sortedBy', 'time')
    # print(paperID)
    # print(userID)
    # print(sortedBy)
    # sortedBy == 'time':
    # 根据发布时间进行排序
    comments = models.CommentModel.objects.filter(paperID=paperID).order_by('-pubTime')
    # 根据热度进行排序
    if sortedBy == 'hot':
        comments = models.CommentModel.objects.filter(paperID=paperID).order_by('-hot')
    for single_comment in comments:
        comment = model_to_dict(single_comment, fields=['id',
                                                        'userName',
                                                        'userID',
                                                        'paperID',
                                                        'contentView',
                                                        # 'pubTime',
                                                        'likeNum',
                                                        'dislikeNum',
                                                        'hot',
                                                        'replyCommentID',
                                                        'repliedName',
                                                        'replyNum',
                                                        'avatar',
                                                        'replyList'])
        comment['id'] = single_comment.id
        comment['pubTime'] = str(single_comment.pubTime)
        comment['currentUserLike'] = '2'
        if str(userID) in single_comment.likeUserIDList:
            comment['currentUserLike'] = '0'
        elif str(userID) in single_comment.dislikeUserIDList:
            comment['currentUserLike'] = '1'
        comment['replyList'] = getCommentReply(commentID=single_comment.id, sortedBy=sortedBy, userID=userID)
        res.append(comment)
    print('成功获取评论')
    return HttpResponse(json.dumps({'comments': res}))


# 发布评论
def postComment(request):
    # print('开始添加评论')
    res = []
    paperID = request.POST.get('paperID', 'PAPERID')
    userID = request.POST.get('userID', 'USERID')
    userName = request.POST.get('userName', 'USERNAME')
    contentView = request.POST.get('contentView', 'CONTENTVIEW')
    sortedBy = request.POST.get('sortedBy', 'SORTEDBY')
    avatar = request.POST.get('avatar', 'AVATAR')
    new_comment = models.CommentModel.objects.create(paperID=paperID,
                                                     userID=userID,
                                                     userName=userName,
                                                     contentView=contentView,
                                                     likeNum=0,
                                                     dislikeNum=0,
                                                     hot=0,
                                                     replyCommentID=-1,
                                                     replyNum=0,
                                                     avatar=avatar,
                                                     likeUserIDList=['-1'],
                                                     dislikeUserIDList=['-1'],
                                                     )

    # models.HeadPicture.objects.create(commentID=new_comment.id,
    #                                   avatar=avatar)

    # print('成功添加评论')
    comments = models.CommentModel.objects.filter(paperID=paperID)
    for single_comment in comments:
        comment = model_to_dict(single_comment, fields=['id',
                                                        'userName',
                                                        'userID',
                                                        'paperID',
                                                        'contentView',
                                                        # 'pubTime',
                                                        'likeNum',
                                                        'dislikeNum',
                                                        'hot',
                                                        'replyCommentID',
                                                        'repliedName',
                                                        'replyNum',
                                                        'avatar',
                                                        'replyList'])
        comment['id'] = single_comment.id
        comment['pubTime'] = str(single_comment.pubTime)
        comment['currentUserLike'] = '2'
        if str(userID) in single_comment.likeUserIDList:
            comment['currentUserLike'] = '0'
        elif str(userID) in single_comment.dislikeUserIDList:
            comment['currentUserLike'] = '1'
        comment['replyList'] = getCommentReply(commentID=single_comment.id, sortedBy=sortedBy, userID=userID)
        res.append(comment)

    return HttpResponse(json.dumps({'comments': res}))

'''
# 获取评论的头像
def getCommentAvatar(request):
    commentID = request.POST.get('commentID', )
    headPicture = models.CommentModel.objects.get(commentID=commentID)
    return HttpResponse(headPicture.avatar)
'''


# 进行回复
def postReply(request):
    res = []
    paperID = request.POST.get('paperID', 'PAPERID')
    userID = request.POST.get('userID', 'USERID')
    userName = request.POST.get('userName', 'USERNAME')
    sortedBy = request.POST.get('sortedBy', 'SORTEDBY')
    commentID = request.POST.get('commentID', 1)
    contentView = request.POST.get('contentView', 'CONTENTVIEW')
    repliedName = request.POST.get('repliedName', 'REPLIEDNAME')
    models.CommentModel.objects.create(paperID='reply',
                                       userID=userID,
                                       userName=userName,
                                       contentView=contentView,
                                       likeNum=0,
                                       dislikeNum=0,
                                       hot=0,
                                       replyCommentID=commentID,
                                       replyCommentUserName=repliedName,
                                       likeUserIDList=['-1'],
                                       dislikeUserIDList=['-1'],
                                       )
    tmp_comment = models.CommentModel.objects.get(id=commentID)
    tmp_comment.replyNum += 1
    tmp_comment.save()
    comments = models.CommentModel.objects.filter(paperID=paperID)
    for single_comment in comments:
        comment = model_to_dict(single_comment, fields=['id',
                                                        'userName',
                                                        'userID',
                                                        'paperID',
                                                        'contentView',
                                                        # 'pubTime',
                                                        'likeNum',
                                                        'dislikeNum',
                                                        'hot',
                                                        'replyCommentID',
                                                        'repliedName',
                                                        'replyNum',
                                                        'avatar',
                                                        'replyList'])
        comment['id'] = single_comment.id
        comment['pubTime'] = str(single_comment.pubTime)
        comment['currentUserLike'] = '2'
        if str(userID) in single_comment.likeUserIDList:
            comment['currentUserLike'] = '0'
        elif str(userID) in single_comment.dislikeUserIDList:
            comment['currentUserLike'] = '1'
        comment['replyList'] = getCommentReply(commentID=single_comment.id, sortedBy=sortedBy, userID=userID)
        res.append(comment)
    return HttpResponse(json.dumps({'comments': res}))


# 点踩功能
def postLike(request):
    res = []
    paperID = request.POST.get('paperID', 'PAPERID')
    userID = request.POST.get('userID', '1')
    commentID = request.POST.get('commentID', 'COMMENTID')
    isLike = request.POST.get('isLike', '1')
    sortedBy = request.POST.get('sortedBy', 'time')
    comment = models.CommentModel.objects.get(id=commentID)
    # print(paperID)
    # print(userID)
    # print(commentID)
    if isLike == '1':
        comment.likeNum += 1
        comment.hot += 1
        if str(userID) not in comment.likeUserIDList:
            comment.likeUserIDList.append(str(userID))
    else:
        comment.dislikeNum += 1
        comment.hot -= 1
        if str(userID) not in comment.dislikeUserIDList:
            comment.dislikeUserIDList.append(str(userID))
    comment.save()
    comments = models.CommentModel.objects.filter(paperID=paperID)
    for single_comment in comments:
        comment_ = model_to_dict(single_comment, fields=['id',
                                                         'userName',
                                                         'userID',
                                                         'paperID',
                                                         'contentView',
                                                         # 'pubTime',
                                                         'likeNum',
                                                         'dislikeNum',
                                                         'hot',
                                                         'replyCommentID',
                                                         'repliedName',
                                                         'replyNum',
                                                         'avatar',
                                                         'replyList'])
        comment_['id'] = single_comment.id
        comment_['pubTime'] = str(single_comment.pubTime)
        comment_['currentUserLike'] = '2'
        if str(userID) in single_comment.likeUserIDList:
            comment_['currentUserLike'] = '0'
        elif str(userID) in single_comment.dislikeUserIDList:
            comment_['currentUserLike'] = '1'
        comment_['replyList'] = getCommentReply(commentID=single_comment.id, sortedBy=sortedBy, userID=userID)
        res.append(comment_)
    return HttpResponse(json.dumps({'comments': res}))


# 取消点踩
def cancelLike(request):
    res = []
    paperID = request.POST.get('paperID', 'PAPERID')
    userID = request.POST.get('userID', '1')
    commentID = request.POST.get('commentID', 'COMMENTID')
    isLike = request.POST.get('isLike', '1')
    sortedBy = request.POST.get('sortedBy', 'time')
    comment = models.CommentModel.objects.get(id=commentID)
    if isLike == '1':
        comment.likeNum -= 1
        comment.hot -= 1
        if str(userID) in comment.likeUserIDList:
            comment.likeUserIDList.remove(str(userID))
    else:
        comment.dislikeNum -= 1
        comment.hot += 1
        if str(userID) in comment.dislikeUserIDList:
            comment.dislikeUserIDList.remove(str(userID))
    comment.save()
    comments = models.CommentModel.objects.filter(paperID=paperID)
    for single_comment in comments:
        comment_ = model_to_dict(single_comment, fields=['id',
                                                         'userName',
                                                         'userID',
                                                         'paperID',
                                                         'contentView',
                                                         # 'pubTime',
                                                         'likeNum',
                                                         'dislikeNum',
                                                         'hot',
                                                         'replyCommentID',
                                                         'repliedName',
                                                         'replyNum',
                                                         'avatar',
                                                         'replyList'])
        comment_['id'] = single_comment.id
        comment_['pubTime'] = str(single_comment.pubTime)
        comment_['currentUserLike'] = '2'
        if str(userID) in single_comment.likeUserIDList:
            comment_['currentUserLike'] = '0'
        elif str(userID) in single_comment.dislikeUserIDList:
            comment_['currentUserLike'] = '1'
        comment_['replyList'] = getCommentReply(commentID=single_comment.id, sortedBy=sortedBy, userID=userID)
        res.append(comment_)
    return HttpResponse(json.dumps({'comments': res}))

'''
def register(request): # 等同于if request.method == 'POST':
    ret = {'code': 1000, 'msg': None} 
    try:
        user = request._request.POST.get('username') 
        pwd = request._request.POST.get('password')
        obj = models.UserInfo.objects.filter(username=user).first()
        if not obj:
            models.UserInfo.objects.create(username=user, password=pwd)
            ret['code'] = 100
            ret['msg'] = u'创建成功'
        else:
            ret['code'] = 101
            ret['msg'] = u'用户名存在'
    except Exception as e:
        ret['code'] = 102
        ret['msg'] = 'getting username or password error or database error'
                
    return HttpResponse(json.dumps(ret))

def login(request):
    ret = {'code': 1000, 'msg': None}
    try:
        user = request._request.POST.get('username')
        pwd = request._request.POST.get('password')
        obj = models.UserInfo.objects.filter(username=user, password=pwd).first()
        if not obj:
            ret['code']=1001
            ret['msg']='username or password is wrong'
            # 为登录用户创建token
        token = hashlib.md5(user)
            # 存在则更新，反之创建
        models.UserToken.objects.update_or_create(user=obj, defaults={'token': token})
        ret['token'] = token
    except Exception as e:
        ret['code'] = 1002
        ret['msg'] = 'getting username or password error or database error'
    return HttpResponse(json.dumps(ret))
'''


# 注册
def register(request):
    userName = request.POST.get('userName', 'username')
    password = request.POST.get('password', 'xxx')
    # email = request.POST.get('email', 'undefined')

    res = {'retCode': 0, 'message': ''}

    obj = models.UserModel.objects.filter(userName=userName)
    if obj.count() == 0:
        models.UserModel.objects.create(userName=userName, password=password,
                                        collectList=['-1'], focusDict=str({}))
        obj = models.UserModel.objects.get(userName=userName)
        #obj.collectList.remove('-1')
        obj.save()
        res['retCode'] = 1
        res['message'] = '注册成功'
    else:
        res['retCode'] = 0
        res['message'] = '用户名已注册'
    return HttpResponse(json.dumps({'register': res}))


# 登录
def login(request):
    userName = request.POST.get('userName', 'username')
    password = request.POST.get('password', 'xxx')

    res = {'retCode': 0, 'message': ''}
    obj = models.UserModel.objects.filter(userName=userName)

    if obj.count() == 0:
        res['retCode'] = 0
        res['message'] = '用户不存在'
    else:
        obj = models.UserModel.objects.get(userName=userName)
        if obj.password == password:
            res['retCode'] = 1
            res['message'] = '成功登录'
        else:
            res['retCode'] = 2
            res['message'] = '密码错误'
    return HttpResponse(json.dumps({'login': res}))


# 获取个人信息
def getUserInformation(request):
    userName = request.POST.get('userName', 'username')

    obj = models.UserModel.objects.get(userName=userName)

    res = model_to_dict(obj, fields=['userName', 'profession', 'email', 'phoneNumber',
                                     'area', 'personHomepage', 'note', 'isOnline'])
    res['collectList'] = []
    for url in obj.collectList:
        res['collectList'].append(url)
    res['focusDict'] = ast.literal_eval(obj.focusDict)

    return HttpResponse(json.dumps({'userInfo': res}))


# 修改个人信息
def modifyUserInformation(request):
    userName = request.POST.get('userName', '')
    password = request.POST.get('password', '')
    profession = request.POST.get('profession', '')
    email = request.POST.get('email', '')
    phoneNumber = request.POST.get('phoneNumber', '')
    area = request.POST.get('area', '')
    personHomepage = request.POST.get('personHomepage', '')
    note = request.POST.get('note', '')

    obj = models.UserModel.objects.get(userName=userName)
    if password != '':
        obj.password = password
        obj.save()
    if profession != '':
        obj.profession = profession
        obj.save()
    if email != '':
        obj.email = email
        obj.save()
    if phoneNumber != '':
        obj.phoneNumber = phoneNumber
        obj.save()
    if area != '':
        obj.area = area
        obj.save()
    if personHomepage != '':
        obj.personHomepage = personHomepage
        obj.save()
    if note != '':
        obj.note = note
        obj.save()

    obj = models.UserModel.objects.get(userName=userName)
    res = model_to_dict(obj, fields=['userName', 'profession', 'email', 'phoneNumber',
                                     'area', 'personHomepage', 'note', 'isOnline'])
    res['collectList'] = []
    for url in obj.collectList:
        res['collectList'].append(url)
    res['focusDict'] = ast.literal_eval(obj.focusDict)
    return HttpResponse(json.dumps({'userInfo': res}))


# 点关注
def addFocus(request):
    userName = request.POST.get('userName', '')
    field_1 = request.POST.get('field_1', '')
    field_2 = request.POST.get('field_2', '')
    level = request.POST.get('level', '')
    obj = models.UserModel.objects.get(userName=userName)

    # 关注一级学科
    if str(level) == '1':
        tmpFocus = ast.literal_eval(obj.focusDict)  # str2dict
        if field_1 not in tmpFocus:
            tmpFocus[field_1] = []
            obj.focusDict = str(tmpFocus)
            obj.save()
    # 关注二级学科
    else:
        tmpFocus = ast.literal_eval(obj.focusDict)
        if field_1 not in tmpFocus:
            tmpFocus[field_1] = [field_2]
        else:
            if field_2 not in tmpFocus[field_1]:
                tmpFocus[field_1].append(field_2)
        obj.focusDict = str(tmpFocus)
        obj.save()

    obj = models.UserModel.objects.get(userName=userName)
    res = model_to_dict(obj, fields=['userName', 'profession', 'email', 'phoneNumber',
                                     'area', 'personHomepage', 'note', 'isOnline'])
    res['collectList'] = []
    for url in obj.collectList:
        res['collectList'].append(url)
    res['focusDict'] = ast.literal_eval(obj.focusDict)
    return HttpResponse(json.dumps({'userInfo': res}))


# 取消关注
def cancelFocus(request):
    userName = request.POST.get('userName', '')
    field_1 = request.POST.get('field_1', '')
    field_2 = request.POST.get('field_2', '')
    level = request.POST.get('level', '')
    obj = models.UserModel.objects.get(userName=userName)

    # 取消关注一级学科
    if str(level) == '1':
        tmpFocus = ast.literal_eval(obj.focusDict)
        if field_1 in tmpFocus:
            tmpFocus.pop(field_1)
            obj.focusDict = str(tmpFocus)
            obj.save()
    # 取消关注二级学科
    else:
        tmpFocus = ast.literal_eval(obj.focusDict)
        if field_1 in tmpFocus:
            if field_2 in tmpFocus[field_1]:
                tmpFocus[field_1].remove(field_2)
        obj.focusDict = str(tmpFocus)
        obj.save()

    obj = models.UserModel.objects.get(userName=userName)
    res = model_to_dict(obj, fields=['userName', 'profession', 'email', 'phoneNumber',
                                     'area', 'personHomepage', 'note', 'isOnline'])
    res['collectList'] = []
    for url in obj.collectList:
        res['collectList'].append(url)
    res['focusDict'] = ast.literal_eval(obj.focusDict)
    return HttpResponse(json.dumps({'userInfo': res}))


# 点收藏
def addCollect(request):
    userName = request.POST.get('userName', '')
    paperID = request.POST.get('paperID', 'PAPERID')

    obj = models.UserModel.objects.get(userName=userName)
    if paperID not in obj.collectList:
        obj.collectList.append(paperID)
        obj.save()

    obj = models.UserModel.objects.get(userName=userName)
    res = model_to_dict(obj, fields=['userName', 'profession', 'email', 'phoneNumber',
                                     'area', 'personHomepage', 'note', 'isOnline'])
    res['collectList'] = []
    for url in obj.collectList:
        res['collectList'].append(url)
    res['focusDict'] = ast.literal_eval(obj.focusDict)
    return HttpResponse(json.dumps({'userInfo': res}))


# 取消收藏
def cancelCollect(request):
    userName = request.POST.get('userName', '')
    paperID = request.POST.get('paperID', 'PAPERID')

    obj = models.UserModel.objects.get(userName=userName)
    if paperID in obj.collectList:
        obj.collectList.remove(paperID)
        obj.save()

    obj = models.UserModel.objects.get(userName=userName)
    res = model_to_dict(obj, fields=['userName', 'profession', 'email', 'phoneNumber',
                                     'area', 'personHomepage', 'note', 'isOnline'])
    res['collectList'] = []
    for url in obj.collectList:
        res['collectList'].append(url)
    res['focusDict'] = ast.literal_eval(obj.focusDict)
    return HttpResponse(json.dumps({'userInfo': res}))


# 上传头像
def uploadHeadImg(request):
    # noinspection PyBroadException
    try:
        userName = request.POST.get('userName', '')
        headImg = request.FILES.get('headImg')
        print(headImg)

        obj = models.UserModel.objects.get(userName=userName)
        obj.headImg = headImg
        obj.save()
        return HttpResponse(json.dumps({'retCode': 1, 'message': '成功上传'}))
    except Exception as e:
        return HttpResponse(json.dumps({'retCode': 0, 'message':'上传失败'}))


# 获取头像
def getHeadImg(request):
    userName = request.POST.get('userName', '')
    obj = models.UserModel.objects.get(userName=userName)
    return HttpResponse(obj.headImg, content_type='image/jpg')