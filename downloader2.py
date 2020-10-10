import requests
from bs4 import BeautifulSoup
import csv
import os, shutil, time
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

init_year = 2017
save_root_dir = "./data"
base_url = "http://www.data.jma.go.jp/obd/stats/etrn/view/hourly_%s1.php?prec_no=%s&block_no=%s&year=%s&month=%s&day=%s&view=p1"

abnormity_wind = set()



def str2float(str):
  try:
    return float(str)
  except:
    return None



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
    if name[-1] in "都道府県":
      continue
    if name in already:
      continue
    already.add(name)
    city_no = area.get("href").split("block_no=")[1].split("&year")[0]
    places.append([name, pre_no, city_no])

  return places



def get_rows(pre_no, city_no, year, month, day):
  #官署かどうかでurlが変わる
  try:
    #2つの都市コードと年と月を当てはめる
    url = base_url%("a", pre_no, city_no, year, month,day)
    r = requests.get(url)
    r.encoding = r.apparent_encoding

    # 対象である表をスクレイピング
    soup = BeautifulSoup(r.text,"html.parser")
    #表示されている日付を取り出す
    day_pre = int(soup.findAll('h3')[0].text.split("月")[1].split("日")[0])
  except:
    #官署のときurlが変わる
    #2つの都市コードと年と月を当てはめる
    url = base_url%("s", pre_no, city_no, year, month,day)
    r = requests.get(url)
    r.encoding = r.apparent_encoding

    # 対象である表をスクレイピング
    soup = BeautifulSoup(r.text,"html.parser")
    #表示されている日付を取り出す
    day_pre = int(soup.findAll('h3')[0].text.split("月")[1].split("日")[0])

  
  #意図した日付にアクセスできていなければ飛ばす
  if day_pre != day:
    rows = []
  else:
    rows = soup.findAll('tr',class_='mtx') #タグ指定してclass名を指定
    # 表の最初の1~4行目はカラム情報なのでスライス
    rows = rows[4:]
    if not (len(rows[0]) == 8 or len(rows[0]) == 17):
      print(len(rows[0]))
  return rows



def get_rowData(row, year, month, day):
  data = row.findAll('td')
  rowData = [] #初期化
  rowData.append(str(year) + "/" + str(month) + "/" + str(day) + "/" + str(data[0].string))

  #官署かどうかで処理を変える
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
  for pre_no in prefectures.values():
    places = places + get_place_list(pre_no)
  #都市を網羅
  for idx in range(len(places)):
    #TODO 都道府県の扱い
    place_name = places[idx][0]
    print("{}/{}\t{}".format(idx+1, len(places), place_name))
    #カラムで初期化
    #TODO 官署の場合のカラム
    #TODO 英語名への変更
    All_list = [['年月日', '降水量(mm)', '気温(℃)', '風速(m/s)', '風向', '日照時間(h)', '降雪(cm)','積雪(cm)']]
    #日付のリストを作成
    #TODO 最新の日付までの対応
    days = [(year,month,day) for year in range(init_year,2020) for month in range(1,13) for day in range(1,32)]
    for year, month, day in tqdm(days):
      #存在しない日付にアクセスした場合は空のリストを返す
      rows = get_rows(places[idx][1], places[idx][2], year, month, day)
      # 1行ずつデータを処理
      for row in rows:
        #次の行にデータを追加
        All_list.append(get_rowData(row, year, month, day))

    #TODO 保存時の名前をアルファベットに
    #都市ごとにデータをファイルを新しく生成して書き出す。(csvファイル形式。名前は都市名)
    with open(os.path.join(save_root_dir,place_name + '.csv'), 'w') as file:
      writer = csv.writer(file, lineterminator='\n')
      writer.writerows(All_list)
  print(abnormity_wind)



if __name__ == "__main__":
  main()
