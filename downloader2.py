import requests
from bs4 import BeautifulSoup
import csv
import os, shutil, time, json, datetime
from tqdm import tqdm

prefectures = {
    '東京都':44,
    '沖縄県':91,
    '茨城県':40,
    '千葉県':45,
    '埼玉県':43,
    '栃木県':41,
    '福島県':36,
}

from_year = 2018
to_year = 2020
save_root_dir = "./data"
base_url = "http://www.data.jma.go.jp/obd/stats/etrn/view/hourly_%s1.php?prec_no=%s&block_no=%s&year=%s&month=%s&day=%s&view=p1"

abnormity_wind = set()
place_dic = {}



def str2float(str):
  try:
    return float(str)
  except:
    return None



# 風向を漢字表記から変更
def get_wind_direction(str):
  if str == "静穏":
    return "calm"
  change = {"東":"E", "西":"W", "南":"S", "北":"N"}
  try:
    res = [change[s] for s in str]
    res = "".join(res)
  except:
    #TODO 東西南北以外の処理(x,///)
    abnormity_wind.add(str)
    res = None
  return res



# 各県の都市を取得
def get_place_list(pre_no):
  url = "http://www.data.jma.go.jp/obd/stats/etrn/select/prefecture.php?prec_no=%s&block_no=&year=&month=&day=&view="%(pre_no)
  r = requests.get(url)
  r.encoding = r.apparent_encoding
  soup = BeautifulSoup(r.text,"html.parser")
  areas = soup.findAll('area')
  already = set()
  places = []
  for area in areas:
    name = area.get("alt")
    #TODO 都道府県全地点選択も防ぐ
    if len(name) >= 3 and name[-3:] == "全地点":
      continue
    if name[-1] in "都道府県":
      continue
    if name in already:
      continue
    already.add(name)
    city_no = area.get("href").split("block_no=")[1].split("&year")[0]
    places.append([name, pre_no, city_no])

  return places



# データページをスクレイピング
def get_rows(url):
  # 表をスクレイピング
  r = requests.get(url)
  r.encoding = r.apparent_encoding
  soup = BeautifulSoup(r.text,"html.parser")
  rows = soup.findAll('tr',class_='mtx')
  # 表の最初の1~4行目はカラム情報なのでスライス
  rows = rows[4:]
  if not (len(rows[0]) == 8 or len(rows[0]) == 17):
    print(len(rows[0]))
  return rows



# 取得した表から必要な情報を取り出す
def get_rowData(row, year, month, day):
  data = row.findAll('td')
  rowData = [] #初期化
  rowData.append(str(year) + "/" + str(month) + "/" + str(day) + "/" + str(data[0].string))

  #官署かどうかで処理するカラムが変わる
  if len(row)==8:
    #官署以外の処理
    data_idx = [idx for idx in range(1,len(row))]
    dir_idx = 4
  elif len(row)==17:
    #官署での処理
    #TODO 官署で取得する項目の選定
    data_idx = [3, 4, 8, 9, 10, 12, 13]
    dir_idx = 9
  else:
    print(len(row))
    return
  
  #各要素を処理
  for idx in data_idx:
    d = data[idx].string
    if idx == dir_idx:
      #風向は別で処理
      d = get_wind_direction(d)
    else:
      d = str2float(d)
    rowData.append(d)

  return rowData



def main():
  #data directoryの初期化
  if os.path.exists(save_root_dir):
    shutil.rmtree(save_root_dir)
  os.mkdir(save_root_dir)

  #県名から都市リストをスクレイピング
  places = []
  for pre_name, pre_no in prefectures.items():
    place_dic[pre_no] = pre_name
    save_dir = os.path.join(save_root_dir,str(pre_no))
    os.mkdir(save_dir)
    places = places + get_place_list(pre_no)
  
  #都市を網羅
  for idx in range(len(places)):
    place_name, pre_no, city_no = places[idx]
    place_dic[city_no] = place_name
    save_dir = os.path.join(save_root_dir,str(pre_no))
    print("{}/{}\t{}".format(idx+1, len(places), place_name))

    #カラムで初期化
    #TODO 官署の場合のカラム
    #TODO 英語名への変更
    All_list = [['年月日', '降水量(mm)', '気温(℃)', '風速(m/s)', '風向', '日照時間(h)', '降雪(cm)','積雪(cm)']]

    #日付のリストを作成
    days = [(year,month,day) for year in range(from_year,to_year+1) for month in range(1,13) for day in range(1,32)]

    #一日ずつデータを取得
    for year, month, day in tqdm(days):
      #不正な日付をとばす
      try:
        if datetime.date(year,month,day) >= datetime.date.today():
          continue
      except:
        continue

      #官署かどうかでurlが変わる
      try:
        url = base_url%("a", pre_no, city_no, year, month,day)
        rows = get_rows(url)
      except:
        #官署のときurlが変わる
        try:
          url = base_url%("s", pre_no, city_no, year, month,day)
          rows = get_rows(url)
        except:
          continue
      # 1行ずつデータを処理
      for row in rows:
        #次の行にデータを追加
        All_list.append(get_rowData(row, year, month, day))

    #保存時の名前はidで管理
    with open(os.path.join(save_dir,str(city_no) + '.csv'), 'w') as file:
      writer = csv.writer(file, lineterminator='\n')
      writer.writerows(All_list)

  #設定をjsonで保存
  json_str = json.dumps(place_dic)
  json_str = json_str.encode("utf-8")
  with open(os.path.join(save_root_dir,"place_dic.txt"), "wb") as f:
    f.write(json_str)
  print(abnormity_wind)



if __name__ == "__main__":
  main()
