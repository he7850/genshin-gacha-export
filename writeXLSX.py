import json

import xlsxwriter


def getInfoByItemId(item_id, gachaInfo):
    for info in gachaInfo:
        if item_id == info["item_id"]:
            return info["name"], info["item_type"], info["rank_type"]
    return


def convertGachaDataToXLSX(datafile, xlsxName):
    with open(datafile, "r", encoding="utf-8") as f:
        content = f.read()
        dataObj = json.loads(content)

    gachaTypes = dataObj["gachaType"]
    gachaTypeIds = [banner["key"] for banner in gachaTypes]
    gachaTypeNames = [banner["name"] for banner in gachaTypes]

    gachaTypeDict = dict(zip(gachaTypeIds, gachaTypeNames))

    gachaLog = dataObj["gachaLog"]

    print(f"写入文件：{xlsxName}")
    workbook = xlsxwriter.Workbook(xlsxName)
    for gachaTypeId in gachaTypeIds:
        gachaDictList = gachaLog[gachaTypeId]
        gachaTypeName = gachaTypeDict[gachaTypeId]

        # 按时间从前到后排序
        gachaDictList.reverse()

        # 写表头
        header = "时间,名称,类别,星级,总次数,保底内"
        worksheet = workbook.add_worksheet(gachaTypeName)
        content_css = workbook.add_format({"align": "left", "font_name": "微软雅黑", "border_color": "#c4c2bf", "bg_color": "#ebebeb", "border": 1})
        title_css = workbook.add_format(
            {"align": "left", "font_name": "微软雅黑", "color": "#757575", "bg_color": "#dbd7d3", "border_color": "#c4c2bf", "border": 1, "bold": True})
        excel_col = ["A", "B", "C", "D", "E", "F"]
        excel_header = header.split(",")
        worksheet.set_column("A:A", 22)
        worksheet.set_column("B:B", 14)
        for i in range(len(excel_col)):
            worksheet.write(f"{excel_col[i]}1", excel_header[i], title_css)
        worksheet.freeze_panes(1, 0)

        # 写表内容
        total_idx = 0
        pity_idx = 0
        row_num = 2  # 从第2行开始
        for gacha in gachaDictList:
            time = gacha["time"]
            name = gacha["name"]
            item_type = gacha["item_type"]
            rank_type = int(gacha["rank_type"])  # 星级：3,4,5
            total_idx = total_idx + 1
            pity_idx = pity_idx + 1
            excel_data = [time, name, item_type, rank_type, total_idx, pity_idx]
            for i in range(len(excel_col)):
                worksheet.write(f"{excel_col[i]}{row_num}", excel_data[i], content_css)
            if rank_type == 5:
                pity_idx = 0  # 保底重置
            row_num += 1

        # 给5星、4星、3星分别加颜色
        star_5 = workbook.add_format({"color": "#bd6932", "bold": True})
        star_4 = workbook.add_format({"color": "#a256e1", "bold": True})
        star_3 = workbook.add_format({"color": "#8e8e8e"})
        worksheet.conditional_format(f"A2:F{len(gachaDictList) + 1}", {"type": "formula", "criteria": "=$D2=5", "format": star_5})
        worksheet.conditional_format(f"A2:F{len(gachaDictList) + 1}", {"type": "formula", "criteria": "=$D2=4", "format": star_4})
        worksheet.conditional_format(f"A2:F{len(gachaDictList) + 1}", {"type": "formula", "criteria": "=$D2=3", "format": star_3})

    workbook.close()


if __name__ == "__main__":
    # main()
    pass
