# -*- coding: utf-8 -*-

import requests
import time
import json

################### Config #############################

cookie_xsid = '16DD64A835DE8B9D'

########################################################

def getTs():
    return int(time.time() * 1000)

class AutoCompletPapers():
    def __init__(self, session, courseId):

        """
        自动完成小节习题（仅支持已过提交日期的习题）
        :return:
        """
        self.Session = session
        self.courseId = courseId
        self.cookieXsidUser = None

        try:
            self.name = self.get(f'http://www.cqooc.com/account/session/api/profile/get?ts={getTs()}').json().get(
                'name')
        except:
            self.name = input("名字获取失败！请输入你的名字（真实名字）: ")

    def get(self, url, headers=None):
        # 防止请求异常抛出，异常自动重新请�?
        while True:
            try:
                return self.Session.get(url, headers=headers)
            except:
                continue

    def post(self, url, json=None, headers=None, data=None):
        while True:
            try:
                return self.Session.post(url, json=json, headers=headers, data=data)
            except:
                continue

    def getAnswers(self, paperId):
        # 获取答案
        req_url = f'http://www.cqooc.com/test/api/paper/get?id={paperId}&ts={getTs()}'
        # TODO 替换Referer中的id�?
        response = self.get(req_url, headers={
            'Referer': 'http://www.cqooc.com/learn/mooc/testing/do?tid=42663&id=334566831&sid=360456&cid=149658&mid=12158213',
        })
        submitEnd = response.json()['submitEnd']
        if submitEnd > time.time() * 1000:
            return -1
        body = response.json()['body']
        answers = {}
        try:
            for i in body:
                if i['questions'] != []:
                    for question in i['questions']:
                        answer = question['body']['answer']
                        if len(answer) == 1:
                            answer = answer[0]
                        answers["q" + question['id']] = answer
            return answers
        except:
            return None

    def getAnswersFromUser(self, paperId):
        # 获取答案（从另一个用户）
        self.cookieXsidUser = input("请输入已作答用户的cookie(xsid): ") if self.cookieXsidUser == None else self.cookieXsidUser

        session = requests.session()
        session.headers[
            'User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36'
        session.headers['Connection'] = 'close'
        session.headers['cookie'] = 'xsid={}; player=1'.format(self.cookieXsidUser)


        data = session.get('http://www.cqooc.com/json/test/result/search?testID=' + str(paperId), headers={
            'Referer': 'http://www.cqooc.com/learn/mooc/testing/do?tid=42663&id=334566831&sid=360456&cid=149658&mid=12158213',
        })

        time.sleep(0.5)

        req_url = 'http://www.cqooc.com/test/api/paper/get?id=' + str(paperId)
        response = session.get(req_url, headers={
            'Referer': 'http://www.cqooc.com/learn/mooc/testing/do?tid=42663&id=334566831&sid=360456&cid=149658&mid=12158213',
        })

        if response.json().get('code') == 401:
            print("xsid有误，请检查！")
            return -2
        body = response.json()['body']
        answers = {}
        try:
            for i in body:
                if i['questions'] != []:
                    for question in i['questions']:
                        answer = data.json()['data'][0]['body'][0]['q' + question['id']]
                        if len(answer) == 1:
                            answer = answer[0]
                        answers["q" + question['id']] = answer
            return answers
        except:
            return None


    def sendAnswers(self, mode=None):
        """
        :param mode: due 已过期题目获取答案提�? 非due  从另一个用户获取答案提�?
        :return:
        """
        info = self.get('http://www.cqooc.com/user/session?xsid=' + cookie_xsid).json()

        papersList = self.get(
            f'http://www.cqooc.com/json/exam/papers?limit=20&start=1&courseId={self.courseId}&select=id,title&ts={getTs()}')

        papersInfo = {}
        for i in papersList.json()['data']:
            papersInfo[str(i.get('id'))] = i.get('title')

        print("\n[{}] �?{} �?.format('过期题目作答' if mode == 'due' else '拷贝答案作答', len(papersInfo)))
        for index, id in enumerate(papersInfo):

            answers = self.getAnswers(id) if mode == 'due' else self.getAnswersFromUser(id)

            if answers == -1:
                print("{}/{} [{}] 未过提交日期，跳过！".format(len(papersInfo), index + 1, papersInfo[id]))
                time.sleep(1)
                continue
            elif answers == None:
                print(f"{len(papersInfo)}/{index+1} [{papersInfo[id]}] {'无测试题目，跳过�? if mode == 'due' else '未获取到答案，跳过！'}")
                time.sleep(1)
                continue
            elif answers == -2:
                return

            # 检查是否已经作�?
            isAnswer = self.get(f'http://www.cqooc.com/json/test/result/search?testID={id}&ts={getTs()}', headers={
                'Referer': f'http://www.cqooc.com/learn/mooc/testing/do?tid={id}&id={self.courseId}&sid=488839&cid=197038&mid=335078130'
            }).json()

            if isAnswer['data'] != []:
                print("{}/{} [{}] 已作答，跳过�?.format(len(papersInfo), index + 1, papersInfo[id]))
                time.sleep(1)
                continue

            response = self.post('http://www.cqooc.com/test/api/result/add', headers={
                'Referer': f'http://www.cqooc.com/learn/mooc/testing/do?tid={id}&id={self.courseId}&sid=307978&cid=131676&mid=12184817',
            }, data=json.dumps({
                "ownerId": info.get('id'),
                "username": info.get('username'),
                "name": self.name,
                "paperId": str(id),
                "courseId": self.courseId,
                "answers": answers,
                "classId": "11962"
            }))

            if response.json().get('code') == 100:
                print("{}/{} [{}] 已超过提交最大次数！".format(len(papersInfo), index + 1, papersInfo[id]))
            else:
                print("{}/{} [{}] 得分: {}".format(len(papersInfo), index + 1, papersInfo[id], response.json().get('score')))

            time.sleep(1)

class AutoCompleteOnlineCourse:
    def __init__(self) -> None:

        if cookie_xsid == '':
            print("请添加xsid")
            exit(0)
        # headers
        session = requests.Session()
        session.headers['Cookie'] = 'player=1; xsid=' + cookie_xsid
        # session.headers['Connection'] = 'close'
        session.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36'
        session.headers['Host'] = 'www.cqooc.com'
        session.keep_alive = False
        self.Session = session
        self.CompleteCourse = None
        self.courseId = None
        self.courseDes = None


    def get(self, url, headers=None):
        while True:
            try:
                return self.Session.get(url, headers=headers)
            except:
                continue

    def post(self, url, json=None, headers=None):
        while True:
            try:
                return self.Session.post(url, json=json, headers=headers)
            except:
                continue

    def main(self) -> None:
        info = self.getInfomation()
        try:
            print('Login ID:', info['username'])
        except:
            print("xsid有误，请检查！")
            return
        self.ownerId = info['id']
        self.username = info['username']

        courseData = []
        for index, i in enumerate(self.getCourseInfo()['data']):
            print("{}、{}".format(index + 1, i['title']))
            courseData.append({
                "title": i['title'],
                "parentId": i['id'],
                "courseId": i['courseId']
            })
        while True:
            try:
                id = input('请选择课程（序号）:')
                self.title = courseData[int(id) - 1]['title']
                break
            except:
                print("输入有误，请重新输入�?)
                continue
        self.parentId = courseData[int(id) - 1]['parentId']
        self.courseId = courseData[int(id) - 1]['courseId']
        print("\n已选择 {}".format(self.title))

        while True:
            print("\n1、模拟观看网课\n2、题目作答（过期题目作答）\n3、题目作答（拷贝答案作答）\n")
            select = input("请选择模式（序号）: ")
            if select == '1':
                self.CompleteCourse = self.getCompleteCourse()
                self.getCourseDes()
                self.startLearnCourse()
            elif select == '2':
                autoCompletPapers = AutoCompletPapers(self.Session, self.courseId)
                autoCompletPapers.sendAnswers(mode='due')
            elif select == '3':
                autoCompletPapers = AutoCompletPapers(self.Session, self.courseId)
                autoCompletPapers.sendAnswers()
            else:
                print("输入有误，请重新输入�?)

    def getCourseDes(self):
        # 课程章节�?
        self.Session.headers['Referer'] = f'http://www.cqooc.com/my/learn/mooc/structure?id={self.courseId}'
        courseDes = {}
        res = self.get(f'http://www.cqooc.com/json/chapters?limit=200&start=1&sortby=selfId&status=1&courseId={self.courseId}&select=id,title,level,selfId,parentId&ts={getTs()}')
        for i in res.json()['data']:
            courseDes[i['id']] = i['title']
        self.courseDes = courseDes

    def getInfomation(self) -> json:
        """
        获取基本信息
        :return:
        """
        return self.get('http://www.cqooc.com/user/session?xsid=' + cookie_xsid).json()

    def getCourseInfo(self) -> json:
        """
        获取课程信息
        :return:
        """
        self.Session.headers['Referer'] = 'http://www.cqooc.com/my/learn'
        return self.get(
            'http://www.cqooc.com/json/mcs?sortby=id&reverse=true&del=2&courseType=2&ownerId={}&limit=10'.format(
                self.ownerId)).json()

    def getCompleteCourse(self) -> list:
        """
        获取已完成小节列�?
        :return:
        """
        self.Session.headers['Referer'] = 'http://www.cqooc.com/learn/mooc/progress?id=' + self.courseId
        data = self.get(
            f'http://www.cqooc.com/json/learnLogs?limit=100&start=1&courseId={self.courseId}&select=sectionId&username={self.username}&ts={getTs()}')
        CourseIdList = []
        for i in data.json()['data']:
            CourseIdList.append(i['sectionId'])
        return CourseIdList

    def startLearn(self) -> json:
        self.Session.headers['Referer'] = 'http://www.cqooc.com/learn/mooc/structure?id=' + self.courseId
        return self.post(url='http://www.cqooc.com/account/session/api/login/time', json={
            "username": self.username
        }).json()

    def getLog(self, sectionId) -> json:
        self.Session.headers['Referer'] = 'http://www.cqooc.com/learn/mooc/structure?id=' + self.courseId
        return self.get(
            'http://www.cqooc.com/json/learnLogs?sectionId=' + sectionId + '&username=' + self.username).json()

    def checkProgress(self, courseId, sectionId, chapterId) -> None:
        count = 0
        while True:
            self.Session.headers['Referer'] = 'http://www.cqooc.com/learn/mooc/structure?id=' + courseId

            self.startLearn()
            self.getLog(sectionId)
            time.sleep(20)
            self.startLearn()
            time.sleep(1)

            Log = self.post('http://www.cqooc.com/learnLog/api/add', json={
                "action": 0,
                "category": 2,
                "chapterId": str(chapterId),
                "courseId": str(courseId),
                "ownerId": self.ownerId,
                "parentId": str(self.parentId),
                "sectionId": int(sectionId),
                "username": self.username
            })

            if count <= 2:
                date = 40
            else:
                date = 150

            if Log.json()['msg'] == '已经添加记录' or Log.json()['msg'] == 'No error':
                return
            else:
                time.sleep(date)
                count += 1
                continue

    def startLearnCourse(self):

        sectionList = \
            self.get('http://www.cqooc.com/json/chapter/lessons?courseId=' + self.courseId).json()['data'][0]['body']
        index_t = 0
        # CompleteCourse = self.getCompleteCourse()
        print("已完成小节数: {} ".format(len(self.CompleteCourse)))
        for chapterId, sectionIds in sectionList.items():
            print('章节进度: {}/{}({:.2f}%) \t当前: {}'.format(index_t + 1, len(sectionList.items()),
                                                        ((float((index_t + 1) / len(sectionList.items()))) * 100),
                                                        self.courseDes.get(chapterId)))
            index_t += 1
            for index, sectionId in enumerate(sectionIds):
                print('\t小节进度: %d/%d(%.2f%%)' % (
                    index + 1, len(sectionIds), (float((index + 1) / len(sectionIds)) * 100)), end='')
                if sectionId in self.CompleteCourse:
                    print('\t已完成，跳过!')
                    continue
                print('\t成功!')
                self.checkProgress(self.courseId, sectionId, chapterId)


if __name__ == '__main__':
    AutoCompleteOnlineCourse().main()

