import json
import time
import os

import requests
from urllib import request
import urllib.parse

from config import Config


def parseGachaLogFromUrl(url):
    print("获取抽卡记录...")

    gachaData = dict()

    # store gacha types
    gachaTypes = getGachaTypes(url)
    gachaTypeIds = [banner["key"] for banner in gachaTypes]
    gachaTypeNames = [banner["name"] for banner in gachaTypes]
    gachaTypeDict = dict(zip(gachaTypeIds, gachaTypeNames))
    gachaData["gachaType"] = gachaTypes

    # store gacha log
    gachaData["gachaLog"] = {}
    for gachaTypeId in gachaTypeIds:
        gachaLog = getGachaLogs(url, gachaTypeId, gachaTypeDict)
        gachaData["gachaLog"][gachaTypeId] = gachaLog

    # store uid
    for gachaTypeId in gachaData["gachaLog"]:
        if "uid" in gachaData:
            break
        for gachaEntry in gachaData["gachaLog"][gachaTypeId]:
            if gachaEntry["uid"]:
                gachaData["uid"] = gachaEntry["uid"]
                break

    data_path = os.path.join(os.getcwd(), "data")
    data_file_path = os.path.join(data_path, f"gachaData.json")

    if os.path.isfile(data_file_path):
        with open(data_file_path, "r", encoding="utf-8") as f:
            localData = json.load(f)
        gachaData = mergeData(localData, gachaData)

    t = time.strftime("%Y%m%d", time.localtime())
    datafile_name = f"gachaData-{t}.json"
    print(f"写入文件：{datafile_name}")
    with open(os.path.join(data_path, f"gachaData-{t}.json"), "w", encoding="utf-8") as f:
        json.dump(gachaData, f, ensure_ascii=False, sort_keys=False, indent=4)

    if s.getKey("FLAG_WRITE_XLSX"):
        import writeXLSX
        writeXLSX.convertGachaDataToXLSX(os.path.join(data_path, datafile_name),
                                         os.path.join(data_path, f"gachaExport-{t}.xlsx"))

    if s.getKey("FLAG_SHOW_REPORT"):
        import statisticsDisplay
        statisticsDisplay.showData(os.path.join(data_path, datafile_name))


def mergeData(localData, gachaData):
    gachaTypes = gachaData["gachaType"]
    gachaTypeIds = [banner["key"] for banner in gachaTypes]
    gachaTypeNames = [banner["name"] for banner in gachaTypes]
    gachaTypeDict = dict(zip(gachaTypeIds, gachaTypeNames))

    for gachaTypeId in gachaTypeDict:
        bannerLocal = localData["gachaLog"][gachaTypeId]
        bannerNewGet = gachaData["gachaLog"][gachaTypeId]
        if bannerNewGet == bannerLocal:
            continue
        else:
            print(f"合并{gachaTypeDict[gachaTypeId]}抽卡记录...")
            flag_list = [False] * len(bannerNewGet)
            localEntries = [[gachaEntry["time"], gachaEntry["name"]] for gachaEntry in bannerLocal]
            for i in range(len(bannerNewGet)):
                gachaNewGet = bannerNewGet[i]
                get = [gachaNewGet["time"], gachaNewGet["name"]]
                if get in localEntries:
                    pass
                else:
                    flag_list[i] = True

            print("本地已有", len(localData["gachaLog"][gachaTypeId]), "条记录")
            print("新获取", len(bannerNewGet), "条记录")

            # 合并记录
            tempData = []
            for i in range(len(bannerNewGet)):
                if flag_list[i]:
                    tempData.append(bannerNewGet[i])
            print("共追加", len(tempData), "条有效记录")
            localData["gachaLog"][gachaTypeId] = tempData + localData["gachaLog"][gachaTypeId]

    return localData


def getGachaTypes(url):
    gacha_type_url = url.replace("getGachaLog", "getConfigList")

    parsed_url = urllib.parse.urlparse(gacha_type_url)

    params = urllib.parse.parse_qsl(parsed_url.query)
    param_dict = dict(params)
    param_dict["lang"] = "zh-cn"

    url_body = gacha_type_url.split("?")[0]
    gacha_type_url = url_body + "?" + urllib.parse.urlencode(param_dict)

    res = requests.get(gacha_type_url).content.decode("utf-8")
    dataObj = json.loads(res)
    return dataObj["data"]["gacha_type_list"]


def getGachaLogs(url, gachaTypeId, gachaTypeDict):
    size = "20"  # api限制一页最大20条
    gachaList = []
    end_id = "0"
    for page in range(1, 9999):
        print(f"正在获取 {gachaTypeDict[gachaTypeId]} 第 {page} 页")
        api = getApi(url, gachaTypeId, size, page, end_id)
        res = requests.get(api)
        content = res.content.decode("utf-8")
        dataObj = json.loads(content)
        gachaEntries = dataObj["data"]["list"]
        if not len(gachaEntries):
            print(f"{gachaTypeDict[gachaTypeId]}抽卡记录读取完毕，一共{len(gachaList)}条")
            break
        for gachaEntry in gachaEntries:
            gachaList.append(gachaEntry)
        end_id = gachaEntries[-1]["id"]

    return gachaList


def getApi(url, gachaType, size, page, end_id=""):
    parsed = urllib.parse.urlparse(url)
    queries = urllib.parse.parse_qsl(parsed.query)
    param_dict = dict(queries)
    param_dict["size"] = size
    param_dict["gacha_type"] = gachaType
    param_dict["page"] = page
    param_dict["lang"] = "zh-cn"
    param_dict["end_id"] = end_id
    param = urllib.parse.urlencode(param_dict)
    path = url.split("?")[0]
    api = path + "?" + param
    return api


def checkApi(url):
    if not url:
        print("url为空")
        return False
    if "getGachaLog" not in url:
        print("错误的url，检查是否包含getGachaLog")
        return False
    try:
        req = requests.get(url)
        res = req.content.decode("utf-8")
        jsonObj = json.loads(res)
    except Exception as e:
        print("API请求解析出错：" + str(e))
        return False

    if not jsonObj["data"]:
        if jsonObj["message"] == "authkey valid error":
            print("authkey错误")
        else:
            print("数据为空，错误代码：" + jsonObj["message"])
        return False
    return True


def getQueryVariable(variable):
    query = url.split("?")[1]
    vars = query.split("&")
    for v in vars:
        if v.split("=")[0] == variable:
            return v.split("=")[1]
    return ""


def getGachaInfo():
    region = getQueryVariable("region")
    lang = getQueryVariable("lang")
    gachaInfoUrl = "https://webstatic.mihoyo.com/hk4e/gacha_info/{}/items/{}.json".format(region, lang)
    r = requests.get(gachaInfoUrl)
    s = r.content.decode("utf-8")
    gachaInfo = json.loads(s)
    return gachaInfo


if __name__ == "__main__":
    url = ""

    curr_path = os.getcwd()
    s = Config(os.path.join(curr_path, "config.json"))
    version = s.getKey("version")
    print(f"当前版本：{version}")

    latest = "https://cdn.jsdelivr.net/gh/he7850/genshin-gacha-export@latest/version.txt"
    print("从 github 获取最新版本号：", end='')
    latestVersion = requests.get(latest, proxies=request.getproxies()).text
    print(latestVersion)

    if version != latestVersion:
        print(f"当前版本不是最新，请到 https://github.com/he7850/genshin-gacha-export/releases 下载最新版本{latestVersion}")

    FLAG_USE_CONFIG_URL = s.getKey("FLAG_USE_CONFIG_URL")
    FLAG_USE_LOG_URL = s.getKey("FLAG_USE_LOG_URL")
    FLAG_SAVE_URL_TO_CONFIG = s.getKey("FLAG_SAVE_URL_TO_CONFIG")

    if FLAG_USE_CONFIG_URL:
        print("读取配置文件中已保存的链接...")
        url = s.getKey("url")

    elif FLAG_USE_LOG_URL:
        USERPROFILE = os.environ["USERPROFILE"]
        output_log_path = None
        output_log_path_cn = os.path.join(USERPROFILE, "AppData", "LocalLow", "miHoYo", "原神", "output_log.txt")
        output_log_path_global = os.path.join(USERPROFILE, "AppData", "LocalLow", "miHoYo", "Genshin Impact", "output_log.txt")

        if os.path.isfile(output_log_path_cn):
            print("检测到国服日志文件")
            output_log_path = output_log_path_cn

        if os.path.isfile(output_log_path_global):
            print("检测到海外服日志文件")
            output_log_path = output_log_path_global

        if os.path.isfile(output_log_path_cn) and os.path.isfile(output_log_path_global):
            flag = True
            while flag:
                c = input("检测到两个日志文件，输入1选择国服，输入2选择海外服：")
                if c == "1":
                    output_log_path = output_log_path_cn
                    flag = False
                elif c == "2":
                    output_log_path = output_log_path_global
                    flag = False

        if not os.path.isfile(output_log_path):
            print("错误：日志文件已被清除")
        else:
            print("提取日志文件中的链接...")
            # with open(output_log_path, "r", encoding="utf-8") as f:
            with open(output_log_path, "r", encoding="mbcs", errors="ignore") as f:
                log = f.readlines()

            for line in log:
                if line.startswith("OnGetWebViewPageFinish") and line.endswith("#/log\n"):
                    url = line.replace("OnGetWebViewPageFinish:", "").replace("#/log\n", "")

            if url == "":
                print("错误：日志文件中没有链接，请打开原神抽卡历史记录，浏览翻页后再使用本程序")
            else:
                splitUrl = url.split("?")
                splitUrl[0] = "https://hk4e-api.mihoyo.com/event/gacha_info/api/getGachaLog"
                url = "?".join(splitUrl)
    else:
        print(f"配置文件出错，请重新下载程序")
        exit()

    if checkApi(url):
        print("链接合法")
        if FLAG_SAVE_URL_TO_CONFIG:
            s.setKey("url", url)
    else:
        print("错误：链接不合法，请打开原神抽卡历史记录，浏览翻页后再使用本程序")
        exit()

    try:
        parseGachaLogFromUrl(url)
    except Exception as e:
        print("日志读取出错:", e)
