import os

import numpy as np
from nakuru.entities.components import *
from nakuru import (
    GroupMessage,
    FriendMessage
)
from botpy.message import Message, DirectMessage
from model.platform.qq import QQ

from cores.qqbot.global_object import AstrMessageEvent

import time
import requests
import json
import threading
from apscheduler.schedulers.asyncio import AsyncIOScheduler

LEETCODE_URL = "https://leetcode-cn.com/problemset/all/"
base_url = 'https://leetcode-cn.com'


class LeetCodePlugin:
    """
    初始化函数, 可以选择直接pass
    """

    def __init__(self) -> None:
        self.myThread = None
        if os.path.exists("leetCode.npy"):  # 如果有保存的数据
            self.subs = np.load("leetCode.npy")
            print("读取到订阅数据：")
            for channel_id in self.subs:  # 遍历所有订阅的up主
                print(f"订阅每日一题的频道：{channel_id}")  # 打印订阅信息
        else:  # 如果没有保存的数据
            self.subs = np.array([])  # 创建订阅字典

    """
    入口函数，机器人会调用此函数。
    返回规范: bool: 插件是否响应该消息 (所有的消息均会调用每一个载入的插件, 如果不响应, 则应返回 False)
             Tuple: None或者长度为3的元组。如果不响应, 返回None； 如果响应, 第1个参数为指令是否调用成功, 第2个参数为返回的消息文本或者gocq的消息链列表, 第3个参数为指令名称
    例子：一个名为"yuanshen"的插件；当接收到消息为“原神 可莉”, 如果不想要处理此消息，则返回False, None；如果想要处理，但是执行失败了，返回True, tuple([False, "请求失败。", "yuanshen"]) ；执行成功了，返回True, tuple([True, "结果文本", "yuanshen"])
    """

    def run(self, ame: AstrMessageEvent):

        if ame.platform == "gocq":
            """
            QQ平台指令处理逻辑
            """
            return False, None
        elif ame.platform == "qqchan":
            """
            频道处理逻辑(频道暂时只支持回复字符串类型的信息，返回的信息都会被转成字符串，如果不想处理某一个平台的信息，直接返回False, None就行)
            """
            if self.myThread is None:  # 如果没有启动线程
                self.myThread = threading.Thread(target=self.send_leetcode_everyday,
                                                 args=(ame,))  # 创建线程对象并传入qq平台对象
                self.myThread.start()  # 启动线程
            if ame.message_str == "每日一题":
                return True, tuple([True, self.get_leetcode_question_everyday(), "LeetCode"])
            elif ame.message_str == '开启每日一题':
                channel_id = ame.message_obj.channel_id
                if channel_id not in self.subs:
                    self.subs = np.concatenate([self.subs, [channel_id]])
                    np.save('leetCode.npy', self.subs)
                    return True, tuple([True, f"每日一题订阅成功！", "LeetCode"])  # 返回失败信息
                else:
                    return True, tuple([False, f"该频道已订阅每日一题！", "LeetCode"])  # 返回失败信息

            else:
                return False, None

    """
    帮助函数，当用户输入 plugin v 插件名称 时，会调用此函数，返回帮助信息
    返回参数要求(必填)：dict{
        "name": str, # 插件名称
        "desc": str, # 插件简短描述
        "help": str, # 插件帮助信息
        "version": str, # 插件版本
        "author": str, # 插件作者
    }
    """

    def info(self):
        return {
            "name": "LeetCode",
            "desc": "LeetCode每日一题插件",
            "help": "LeetCode每日一题插件, 回复『每日一题』即可触发",
            "version": "v1.0.0 beta",
            "author": "Eve"
        }

    def get_leetcode_question_everyday(self) -> str:
        try:
            resp = requests.get(url=LEETCODE_URL)
            response = requests.post(base_url + "/graphql", json={
                "operationName": "questionOfToday",
                "variables": {},
                "query": "query questionOfToday { todayRecord {   question {     questionFrontendId     questionTitleSlug     __typename   }   lastSubmission {     id     __typename   }   date   userStatus   __typename }}"
            })

            leetcodeTitle = json.loads(response.text).get('data').get('todayRecord')[0].get("question").get(
                'questionTitleSlug')

            # 获取今日每日一题的所有信息
            url = base_url + "/problems/" + leetcodeTitle
            response = requests.post(base_url + "/graphql",
                                     json={"operationName": "questionData", "variables": {"titleSlug": leetcodeTitle},
                                           "query": "query questionData($titleSlug: String!) {  question(titleSlug: $titleSlug) {    questionId    questionFrontendId    boundTopicId    title    titleSlug    content    translatedTitle    translatedContent    isPaidOnly    difficulty    likes    dislikes    isLiked    similarQuestions    contributors {      username      profileUrl      avatarUrl      __typename    }    langToValidPlayground    topicTags {      name      slug      translatedName      __typename    }    companyTagStats    codeSnippets {      lang      langSlug      code      __typename    }    stats    hints    solution {      id      canSeeDetail      __typename    }    status    sampleTestCase    metaData    judgerAvailable    judgeType    mysqlSchemas    enableRunCode    envInfo    book {      id      bookName      pressName      source      shortDescription      fullDescription      bookImgUrl      pressImgUrl      productUrl      __typename    }    isSubscribed    isDailyQuestion    dailyRecordStatus    editorType    ugcQuestionId    style    __typename  }}"})
            # 转化成json格式
            jsonText = json.loads(response.text).get('data').get("question")
            # 题名（English）
            titleSlug = jsonText.get('titleSlug')
            # 题名（中文）
            leetcodeTitle = jsonText.get('translatedTitle')
            # 题目难度级别
            level = jsonText.get('difficulty')
            # 题目内容
            context = jsonText.get('translatedContent')
            import re

            context = re.sub('<[^<]+?>', '', context).replace('\n', '').strip()
            context = context.replace('。&nbsp;', '。\n')
            context = context.replace('&nbsp;', ' ')
            context = context.replace('。', '。\n')
            context = context.replace('&lt;', '<')
            context = context.replace('&gt;', '>')
            link = 'https://leetcode.cn/problems/{}/'.format(titleSlug)
            return '『LeetCode 每日一题』 {}, 难度: {}\n题目：{}\n'.format(leetcodeTitle, level, context)
        except Exception as ex:
            raise ex

    def send_leetcode_everyday(self, ame: AstrMessageEvent):
        while True:
            msg = self.get_leetcode_question_everyday()
            for channel in self.subs:
                ame.global_obj.qq_sdk_platform.client.api.post_message(channel_id=str(channel), content=msg)
            time.sleep(60*60*24)


